from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.collaboration import Comment, ProjectVersion
from app.models.project import Project
from app.models.user import User

ANALYTICS_WINDOW_DAYS = 30


class AdminError(Exception):
    pass


@dataclass
class UserWithStats:
    user: User
    project_count: int


@dataclass
class ProjectWithOwner:
    project: Project
    owner_name: str
    owner_email: str


@dataclass
class AnalyticsSummary:
    total_users: int
    total_projects: int
    shared_projects: int
    total_comments: int
    total_versions: int
    signups_by_day: list[tuple[str, int]]
    projects_by_day: list[tuple[str, int]]
    avg_projects_per_user: float


def list_users_with_stats(db: Session) -> list[UserWithStats]:
    rows = (
        db.query(User, func.count(Project.id))
        .outerjoin(Project, Project.owner_id == User.id)
        .group_by(User.id)
        .order_by(User.created_at.desc())
        .all()
    )
    return [UserWithStats(user=u, project_count=count) for u, count in rows]


def list_all_projects(db: Session) -> list[ProjectWithOwner]:
    rows = (
        db.query(Project, User.full_name, User.email)
        .join(User, Project.owner_id == User.id)
        .order_by(Project.updated_at.desc())
        .all()
    )
    return [ProjectWithOwner(project=p, owner_name=name, owner_email=email) for p, name, email in rows]


def set_user_active(db: Session, user_id: uuid.UUID, is_active: bool, requesting_admin_id: uuid.UUID) -> User:
    if user_id == requesting_admin_id and not is_active:
        raise AdminError("You can't deactivate your own account.")
    user = db.get(User, user_id)
    if user is None:
        raise AdminError("User not found.")
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def admin_delete_project(db: Session, project_id: uuid.UUID) -> None:
    project = db.get(Project, project_id)
    if project is None:
        raise AdminError("Project not found.")
    db.delete(project)
    db.commit()


def _counts_by_day(db: Session, model, date_column, since: datetime) -> list[tuple[str, int]]:
    rows = (
        db.query(func.date(date_column), func.count(model.id))
        .filter(date_column >= since)
        .group_by(func.date(date_column))
        .order_by(func.date(date_column))
        .all()
    )
    return [(str(day), count) for day, count in rows]


def get_analytics_summary(db: Session) -> AnalyticsSummary:
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_projects = db.query(func.count(Project.id)).scalar() or 0
    shared_projects = db.query(func.count(Project.id)).filter(Project.is_shared.is_(True)).scalar() or 0
    total_comments = db.query(func.count(Comment.id)).scalar() or 0
    total_versions = db.query(func.count(ProjectVersion.id)).scalar() or 0

    since = datetime.utcnow() - timedelta(days=ANALYTICS_WINDOW_DAYS)
    signups_by_day = _counts_by_day(db, User, User.created_at, since)
    projects_by_day = _counts_by_day(db, Project, Project.created_at, since)

    avg_projects_per_user = (total_projects / total_users) if total_users > 0 else 0.0

    return AnalyticsSummary(
        total_users=total_users,
        total_projects=total_projects,
        shared_projects=shared_projects,
        total_comments=total_comments,
        total_versions=total_versions,
        signups_by_day=signups_by_day,
        projects_by_day=projects_by_day,
        avg_projects_per_user=round(avg_projects_per_user, 2),
    )
