import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.access import get_accessible_project
from app.api.deps import get_current_user
from app.collaboration.comments_service import CommentError, add_comment, delete_comment, list_comments
from app.collaboration.schemas import CommentCreate, CommentOut, VersionCreate, VersionOut, VersionSummary
from app.collaboration.versions_service import VersionError, list_versions, restore_version, save_version
from app.db.database import get_db
from app.models.user import User

router = APIRouter(prefix="/projects", tags=["collaboration"])


@router.get("/{project_id}/comments", response_model=list[CommentOut])
def get_comments(project_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_accessible_project(project_id, db, user)
    return list_comments(db, project_id)


@router.post("/{project_id}/comments", response_model=CommentOut, status_code=201)
def create_comment(
    project_id: uuid.UUID,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    get_accessible_project(project_id, db, user)
    try:
        return add_comment(
            db, project_id, user.id, user.full_name, payload.text,
            node_id=payload.node_id, x=payload.x, y=payload.y,
        )
    except CommentError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{project_id}/comments/{comment_id}", status_code=204)
def remove_comment(
    project_id: uuid.UUID,
    comment_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    get_accessible_project(project_id, db, user)
    try:
        delete_comment(db, project_id, comment_id, user.id)
    except CommentError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{project_id}/versions", response_model=list[VersionSummary])
def get_versions(project_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_accessible_project(project_id, db, user)
    return list_versions(db, project_id)


@router.post("/{project_id}/versions", response_model=VersionSummary, status_code=201)
def create_version(
    project_id: uuid.UUID,
    payload: VersionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = get_accessible_project(project_id, db, user)
    return save_version(db, project, user.id, user.full_name, label=payload.label)


@router.get("/{project_id}/versions/{version_id}", response_model=VersionOut)
def get_version_detail(
    project_id: uuid.UUID,
    version_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    get_accessible_project(project_id, db, user)
    versions = {v.id: v for v in list_versions(db, project_id)}
    version = versions.get(version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Version not found.")
    return version


@router.post("/{project_id}/versions/{version_id}/restore", response_model=VersionSummary)
def restore(
    project_id: uuid.UUID,
    version_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = get_accessible_project(project_id, db, user)
    try:
        restored = restore_version(db, project, version_id)
    except VersionError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Save the restore itself as a new checkpoint too, so restoring never
    # loses the version history that was already there.
    return save_version(db, restored, user.id, user.full_name, label=f"Restored from an earlier version")
