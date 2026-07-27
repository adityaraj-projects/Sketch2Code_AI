from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from jose import JWTError
from sqlalchemy.orm import Session

from app.api.access import get_accessible_project
from app.collaboration.connection_manager import collaboration_manager
from app.core.security import decode_token
from app.db.database import get_db
from app.models.user import User

router = APIRouter(tags=["collaboration-ws"])

_PALETTE = ["#7C5CFF", "#2EE6A6", "#FF9F43", "#FF6B9D", "#4FD1FF", "#FFD93D"]


def _color_for(user_id: str) -> str:
    return _PALETTE[hash(user_id) % len(_PALETTE)]


@router.websocket("/ws/projects/{project_id}")
async def project_collaboration_socket(
    websocket: WebSocket, project_id: str, db: Session = Depends(get_db)
) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return

    try:
        user_id = decode_token(token, expected_type="access")
    except JWTError:
        await websocket.close(code=4401)
        return

    user = db.get(User, uuid.UUID(user_id))
    if user is None:
        await websocket.close(code=4401)
        return

    try:
        get_accessible_project(uuid.UUID(project_id), db, user)
    except Exception:
        await websocket.close(code=4403)
        return

    await websocket.accept()
    color = _color_for(str(user.id))
    await collaboration_manager.join(project_id, websocket, str(user.id), user.full_name, color)

    try:
        while True:
            message = await websocket.receive_json()
            msg_type = message.get("type")

            if msg_type == "cursor":
                await collaboration_manager.broadcast_from(
                    project_id, websocket,
                    {
                        "type": "cursor",
                        "user_id": str(user.id),
                        "user_name": user.full_name,
                        "color": color,
                        "x": message.get("x"),
                        "y": message.get("y"),
                    },
                )
            elif msg_type == "canvas_op":
                await collaboration_manager.broadcast_from(
                    project_id, websocket,
                    {
                        "type": "canvas_op",
                        "user_id": str(user.id),
                        "op": message.get("op"),
                    },
                )
    except WebSocketDisconnect:
        pass
    finally:
        await collaboration_manager.leave(project_id, websocket)
