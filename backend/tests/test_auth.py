import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db
from app.models.user import User
from app.core.security import verify_password, create_password_reset_token

# Setup test DB
import os
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        if os.path.exists("./test_auth.db"):
            try:
                os.remove("./test_auth.db")
            except OSError:
                pass

@pytest.fixture()
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_signup_and_login(client, db):
    # Test Signup
    signup_payload = {
        "full_name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    }
    response = client.post("/api/auth/signup", json=signup_payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["full_name"] == "Test User"
    assert data["user"]["is_email_verified"] is False

    # Test Login
    login_payload = {
        "email": "test@example.com",
        "password": "password123"
    }
    response = client.post("/api/auth/login", json=login_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "user" in data

def test_login_invalid_credentials(client, db):
    signup_payload = {
        "full_name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    }
    client.post("/api/auth/signup", json=signup_payload)

    # Wrong password
    response = client.post("/api/auth/login", json={"email": "test@example.com", "password": "wrongpassword"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Non-existent user
    response = client.post("/api/auth/login", json={"email": "nonexistent@example.com", "password": "password123"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_forgot_password_and_reset_flow(client, db):
    # Setup user
    signup_payload = {
        "full_name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    }
    client.post("/api/auth/signup", json=signup_payload)

    # Forgot password
    response = client.post("/api/auth/forgot-password", json={"email": "test@example.com"})
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json()["message"] == "If an account exists for this email, a reset link has been sent."

    # Get the user to create a reset token manually (or we could mock it)
    user = db.query(User).filter(User.email == "test@example.com").first()
    reset_token = create_password_reset_token(str(user.id))

    # Reset password with invalid token
    response = client.post("/api/auth/reset-password", json={"token": "invalidtoken", "new_password": "newpassword123"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Reset password with valid token
    response = client.post("/api/auth/reset-password", json={"token": reset_token, "new_password": "newpassword123"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Password updated successfully"

    # Try login with old password - should fail
    response = client.post("/api/auth/login", json={"email": "test@example.com", "password": "password123"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Try login with new password - should succeed
    response = client.post("/api/auth/login", json={"email": "test@example.com", "password": "newpassword123"})
    assert response.status_code == status.HTTP_200_OK
