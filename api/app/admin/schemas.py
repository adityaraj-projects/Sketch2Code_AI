from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class AdminUserOut(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    is_active: bool
    is_admin: bool
    is_email_verified: bool
    auth_provider: str
    project_count: int
    created_at: datetime


class AdminProjectOut(BaseModel):
    id: uuid.UUID
    name: str
    owner_name: str
    owner_email: str
    is_shared: bool
    updated_at: datetime
    created_at: datetime


class SetUserActiveRequest(BaseModel):
    is_active: bool


class AnalyticsOut(BaseModel):
    total_users: int
    total_projects: int
    shared_projects: int
    total_comments: int
    total_versions: int
    signups_by_day: list[tuple[str, int]]
    projects_by_day: list[tuple[str, int]]
    avg_projects_per_user: float
