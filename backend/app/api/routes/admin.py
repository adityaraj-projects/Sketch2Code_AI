import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.admin.deps import get_current_admin_user
from app.admin.schemas import AdminProjectOut, AdminUserOut, AnalyticsOut, SetUserActiveRequest
from app.admin.service import (
    AdminError,
    admin_delete_project,
    get_analytics_summary,
    list_all_projects,
    list_users_with_stats,
    set_user_active,
)
from app.db.database import get_db
from app.models.project import Project
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[AdminUserOut])
def get_users(db: Session = Depends(get_db), _: User = Depends(get_current_admin_user)):
    rows = list_users_with_stats(db)
    return [
        AdminUserOut(
            id=r.user.id, full_name=r.user.full_name, email=r.user.email,
            is_active=r.user.is_active, is_admin=r.user.is_admin,
            is_email_verified=r.user.is_email_verified, auth_provider=r.user.auth_provider,
            project_count=r.project_count, created_at=r.user.created_at,
        )
        for r in rows
    ]


@router.patch("/users/{user_id}/active", response_model=AdminUserOut)
def patch_user_active(
    user_id: uuid.UUID,
    payload: SetUserActiveRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    try:
        user = set_user_active(db, user_id, payload.is_active, admin.id)
    except AdminError as e:
        raise HTTPException(status_code=400, detail=str(e))

    project_count = db.query(func.count(Project.id)).filter(Project.owner_id == user.id).scalar() or 0
    return AdminUserOut(
        id=user.id, full_name=user.full_name, email=user.email,
        is_active=user.is_active, is_admin=user.is_admin,
        is_email_verified=user.is_email_verified, auth_provider=user.auth_provider,
        project_count=project_count, created_at=user.created_at,
    )


@router.get("/projects", response_model=list[AdminProjectOut])
def get_projects(db: Session = Depends(get_db), _: User = Depends(get_current_admin_user)):
    rows = list_all_projects(db)
    return [
        AdminProjectOut(
            id=r.project.id, name=r.project.name, owner_name=r.owner_name, owner_email=r.owner_email,
            is_shared=r.project.is_shared, updated_at=r.project.updated_at, created_at=r.project.created_at,
        )
        for r in rows
    ]


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_admin_user)):
    try:
        admin_delete_project(db, project_id)
    except AdminError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/analytics", response_model=AnalyticsOut)
def get_analytics(db: Session = Depends(get_db), _: User = Depends(get_current_admin_user)):
    summary = get_analytics_summary(db)
    return AnalyticsOut(
        total_users=summary.total_users,
        total_projects=summary.total_projects,
        shared_projects=summary.shared_projects,
        total_comments=summary.total_comments,
        total_versions=summary.total_versions,
        signups_by_day=summary.signups_by_day,
        projects_by_day=summary.projects_by_day,
        avg_projects_per_user=summary.avg_projects_per_user,
    )
