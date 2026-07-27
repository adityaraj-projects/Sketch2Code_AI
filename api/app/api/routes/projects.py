import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.access import get_accessible_project, get_owned_project
from app.db.database import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.project import (
    ProjectAutosave,
    ProjectCreate,
    ProjectOut,
    ProjectRename,
    ProjectShareToggle,
    ProjectSummary,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectSummary])
def list_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Project)
        .filter(Project.owner_id == user.id)
        .order_by(desc(Project.updated_at))
        .all()
    )


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = Project(owner_id=user.id, name=payload.name, canvas_data={
        "nodes": [], "edges": [], "strokes": [], "viewport": {"x": 0, "y": 0, "zoom": 1}
    })
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Owner or an invited collaborator on a shared project can view it —
    # this is what makes opening someone else's shared project possible.
    return get_accessible_project(project_id, db, user)


@router.patch("/{project_id}/rename", response_model=ProjectOut)
def rename_project(
    project_id: uuid.UUID,
    payload: ProjectRename,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = get_owned_project(project_id, db, user)
    project.name = payload.name
    db.commit()
    db.refresh(project)
    return project


@router.patch("/{project_id}/share", response_model=ProjectOut)
def set_sharing(
    project_id: uuid.UUID,
    payload: ProjectShareToggle,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Owner-only: turn collaborative access on/off. While shared, any
    authenticated user who has this project's id can view/edit it and
    join its live session — deliberately simple "anyone with the link"
    sharing rather than a full per-user role system."""
    project = get_owned_project(project_id, db, user)
    project.is_shared = payload.is_shared
    db.commit()
    db.refresh(project)
    return project


@router.put("/{project_id}/autosave", response_model=ProjectOut)
def autosave_project(
    project_id: uuid.UUID,
    payload: ProjectAutosave,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Called by the frontend's debounced autosave hook. Idempotent full
    replace of canvas_data. Any collaborator on a shared project can
    autosave, not just the owner — that's the whole point of realtime
    collaboration; last-write-wins is the concurrency model here, same
    as the rest of this canvas's autosave design.
    """
    project = get_accessible_project(project_id, db, user)
    project.canvas_data = payload.canvas_data
    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/duplicate", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def duplicate_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    source = get_owned_project(project_id, db, user)
    copy = Project(
        owner_id=user.id,
        name=f"{source.name} (copy)",
        canvas_data=source.canvas_data,
        thumbnail_url=source.thumbnail_url,
    )
    db.add(copy)
    db.commit()
    db.refresh(copy)
    return copy


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = get_owned_project(project_id, db, user)
    db.delete(project)
    db.commit()
