import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(default="Untitled Flowchart", max_length=150)


class ProjectRename(BaseModel):
    name: str = Field(min_length=1, max_length=150)


class ProjectAutosave(BaseModel):
    """
    canvas_data shape (kept generic so Phase 2 AI features slot in without
    a migration):
    {
      "nodes": [{ id, type, x, y, width, height, text, style }],
      "edges": [{ id, fromNodeId, toNodeId, points, style }],
      "strokes": [{ id, tool, points, pressure, color, width }],
      "viewport": { x, y, zoom }
    }
    """
    canvas_data: dict[str, Any]


class ProjectShareToggle(BaseModel):
    is_shared: bool


class ProjectOut(BaseModel):
    id: uuid.UUID
    name: str
    canvas_data: dict[str, Any]
    thumbnail_url: str | None
    is_shared: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectSummary(BaseModel):
    """Lightweight shape for project list views (dashboard, recent projects)."""
    id: uuid.UUID
    name: str
    thumbnail_url: str | None
    updated_at: datetime

    class Config:
        from_attributes = True
