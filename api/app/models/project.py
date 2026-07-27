import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    name: Mapped[str] = mapped_column(String(150), default="Untitled Flowchart")

    # Canvas graph = list of nodes + edges + freehand strokes, serialized as JSON.
    # Kept generic on purpose: Phase 2's AI recognizer, code generator, and
    # execution simulator will all read/write this same shape without any
    # schema migration.
    canvas_data: Mapped[dict] = mapped_column(JSON, default=dict)

    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # When true, any authenticated user who has this project's id (e.g. via
    # a shared link) can view/edit it collaboratively and add comments —
    # a deliberately simple "anyone with the link" model rather than a
    # full per-user role/permission system. Destructive project
    # management (rename, duplicate, delete) stays owner-only regardless.
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
