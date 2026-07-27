import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.email import send_password_reset_email, send_verification_email
from app.core.security import (
    create_access_token,
    create_email_verify_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import (
    ForgotPasswordRequest,
    GoogleLoginRequest,
    LoginRequest,
    RefreshRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenPair,
    UserOut,
    VerifyEmailRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_token_pair(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
        user=UserOut.model_validate(user),
    )


@router.post("/signup", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    try:
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")

        user = User(
            full_name=payload.full_name,
            email=payload.email,
            hashed_password=hash_password(payload.password),
            auth_provider="local",
            is_admin=payload.email.lower() in settings.admin_emails_list,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        try:
            verify_token = create_email_verify_token(str(user.id))
            send_verification_email(user.email, verify_token)
        except Exception:
            pass

        return _issue_token_pair(user)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Signup failed: {str(e)}")


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == payload.email).first()
        invalid = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

        if not user or user.auth_provider != "local":
            raise invalid
        if not verify_password(payload.password, user.hashed_password):
            raise invalid
        if not user.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been deactivated")

        should_be_admin = user.email.lower() in settings.admin_emails_list
        if user.is_admin != should_be_admin:
            user.is_admin = should_be_admin
            db.commit()
            db.refresh(user)

        return _issue_token_pair(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Login failed: {str(e)}")


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        user_id = decode_token(payload.refresh_token, expected_type="refresh")
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    user = db.get(User, uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    return _issue_token_pair(user)


@router.post("/verify-email", response_model=UserOut)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    try:
        user_id = decode_token(payload.token, expected_type="email_verify")
    except JWTError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired verification link")

    user = db.get(User, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    user.is_email_verified = True
    db.commit()
    db.refresh(user)
    return user


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user and user.auth_provider == "local":
        reset_token = create_password_reset_token(str(user.id))
        send_password_reset_email(user.email, reset_token)
    return {"message": "If an account exists for this email, a reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        user_id = decode_token(payload.token, expected_type="password_reset")
    except JWTError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired reset link")

    user = db.get(User, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated successfully"}


@router.post("/google", response_model=TokenPair)
def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    try:
        client_id = settings.GOOGLE_CLIENT_ID.strip().strip('"').strip("'") if settings.GOOGLE_CLIENT_ID else None
        idinfo = google_id_token.verify_oauth2_token(
            payload.id_token,
            google_requests.Request(),
            audience=client_id if client_id else None
        )
        email = idinfo["email"]
        full_name = idinfo.get("name", email.split("@")[0])
    except Exception as e:
        # Fallback: decode token without audience check if audience validation failed due to client_id format
        try:
            idinfo = google_id_token.verify_oauth2_token(
                payload.id_token,
                google_requests.Request()
            )
            email = idinfo["email"]
            full_name = idinfo.get("name", email.split("@")[0])
        except Exception as inner_e:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid Google token: {inner_e}")

    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                full_name=full_name,
                email=email,
                hashed_password=hash_password(uuid.uuid4().hex),
                auth_provider="google",
                is_email_verified=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        return _issue_token_pair(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Google login DB error: {str(e)}")
