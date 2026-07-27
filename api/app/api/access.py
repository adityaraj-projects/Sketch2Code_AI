import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User


def get_owned_project(project_id: uuid.UUID, db: Session, user: User) -> Project:
    """Strict ownership check, for destructive/structural operations
    (rename, duplicate, delete, toggling sharing) that should stay with
    the project's owner regardless of collaboration."""
    project = db.get(Project, project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return project


def get_accessible_project(project_id: uuid.UUID, db: Session, user: User) -> Project:
    """Owner OR any authenticated user, if the project has sharing turned
    on — this is what collaborative editing, comments, versions, and the
    live WebSocket session all check instead of strict ownership."""
    project = db.get(Project, project_id)
    if not project or (project.owner_id != user.id and not project.is_shared):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return project
