from fastapi import Depends, HTTPException, status

from app.api.deps import get_current_user
from app.models.user import User


def get_current_admin_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
    return user
