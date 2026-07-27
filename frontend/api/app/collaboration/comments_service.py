from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.collaboration import Comment


class CommentError(Exception):
    pass


def add_comment(
    db: Session,
    project_id: uuid.UUID,
    author_id: uuid.UUID,
    author_name: str,
    text: str,
    node_id: str | None = None,
    x: float | None = None,
    y: float | None = None,
) -> Comment:
    if not text.strip():
        raise CommentError("Comment text can't be empty.")
    if node_id is None and (x is None or y is None):
        raise CommentError("A comment needs either a node to attach to, or an (x, y) position.")

    comment = Comment(
        project_id=project_id,
        author_id=author_id,
        author_name=author_name,
        node_id=node_id,
        x=x,
        y=y,
        text=text.strip(),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def list_comments(db: Session, project_id: uuid.UUID) -> list[Comment]:
    return (
        db.query(Comment)
        .filter(Comment.project_id == project_id)
        .order_by(Comment.created_at.asc())
        .all()
    )


def delete_comment(db: Session, project_id: uuid.UUID, comment_id: uuid.UUID, requester_id: uuid.UUID) -> None:
    comment = db.get(Comment, comment_id)
    if comment is None or comment.project_id != project_id:
        raise CommentError("Comment not found.")
    if comment.author_id != requester_id:
        raise CommentError("Only the comment's author can delete it.")
    db.delete(comment)
    db.commit()
