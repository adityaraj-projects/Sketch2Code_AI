from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class CommentCreate(BaseModel):
    text: str
    node_id: str | None = None
    x: float | None = None
    y: float | None = None


class CommentOut(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID
    author_name: str
    node_id: str | None
    x: float | None
    y: float | None
    text: str
    created_at: datetime

    class Config:
        from_attributes = True


class VersionCreate(BaseModel):
    label: str | None = None


class VersionSummary(BaseModel):
    id: uuid.UUID
    label: str
    created_by_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class VersionOut(VersionSummary):
    canvas_data: dict
