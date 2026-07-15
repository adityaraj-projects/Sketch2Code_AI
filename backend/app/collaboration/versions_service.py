from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.collaboration import ProjectVersion
from app.models.project import Project

MAX_VERSIONS_PER_PROJECT = 50


class VersionError(Exception):
    pass


def save_version(
    db: Session,
    project: Project,
    created_by_id: uuid.UUID,
    created_by_name: str,
    label: str | None = None,
    created_at: datetime | None = None,
) -> ProjectVersion:
    now = created_at or datetime.utcnow()
    version = ProjectVersion(
        project_id=project.id,
        created_by_id=created_by_id,
        created_by_name=created_by_name,
        label=label or f"Version at {now.strftime('%b %d, %H:%M')}",
        canvas_data=project.canvas_data,
        created_at=now,
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    _prune_old_versions(db, project.id)
    return version


def _prune_old_versions(db: Session, project_id: uuid.UUID) -> None:
    versions = (
        db.query(ProjectVersion)
        .filter(ProjectVersion.project_id == project_id)
        .order_by(ProjectVersion.created_at.desc())
        .all()
    )
    for stale in versions[MAX_VERSIONS_PER_PROJECT:]:
        db.delete(stale)
    if len(versions) > MAX_VERSIONS_PER_PROJECT:
        db.commit()


def list_versions(db: Session, project_id: uuid.UUID) -> list[ProjectVersion]:
    return (
        db.query(ProjectVersion)
        .filter(ProjectVersion.project_id == project_id)
        .order_by(ProjectVersion.created_at.desc())
        .all()
    )


def restore_version(db: Session, project: Project, version_id: uuid.UUID) -> Project:
    version = db.get(ProjectVersion, version_id)
    if version is None or version.project_id != project.id:
        raise VersionError("Version not found.")

    project.canvas_data = version.canvas_data
    db.commit()
    db.refresh(project)
    return project
