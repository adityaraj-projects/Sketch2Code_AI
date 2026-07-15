"""
Manages who's connected to which project's live collaboration session and
broadcasts messages between them — cursor positions, canvas operations,
presence join/leave. This is a plain, dependency-free class (it only
needs an object with an async `send_json`, which both Starlette's real
WebSocket and a lightweight fake in tests satisfy) so the actual
room/broadcast/disconnect logic is fully unit-testable without spinning
up a real ASGI server or websocket client.

Scope, stated honestly: this is a single in-memory manager, appropriate
for one server instance. Scaling collaboration across multiple backend
instances/processes would need a shared pub/sub layer (e.g. Redis) so
instances can broadcast to clients connected to a different instance —
that's a real infrastructure component this project doesn't have, and
isn't needed to run this as built.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class SendsJson(Protocol):
    async def send_json(self, data: dict[str, Any]) -> None: ...


@dataclass
class Participant:
    connection: SendsJson
    user_id: str
    user_name: str
    color: str


class CollaborationManager:
    def __init__(self) -> None:
        self._rooms: dict[str, list[Participant]] = {}

    def _room(self, project_id: str) -> list[Participant]:
        return self._rooms.setdefault(project_id, [])

    def participants(self, project_id: str) -> list[Participant]:
        return list(self._rooms.get(project_id, []))

    async def join(self, project_id: str, connection: SendsJson, user_id: str, user_name: str, color: str) -> None:
        room = self._room(project_id)
        participant = Participant(connection=connection, user_id=user_id, user_name=user_name, color=color)
        room.append(participant)

        await self._broadcast(
            project_id,
            {
                "type": "presence",
                "participants": [
                    {"user_id": p.user_id, "user_name": p.user_name, "color": p.color} for p in room
                ],
            },
            exclude=None,
        )

    async def leave(self, project_id: str, connection: SendsJson) -> None:
        room = self._room(project_id)
        self._rooms[project_id] = [p for p in room if p.connection is not connection]
        remaining = self._rooms[project_id]

        if remaining:
            await self._broadcast(
                project_id,
                {
                    "type": "presence",
                    "participants": [
                        {"user_id": p.user_id, "user_name": p.user_name, "color": p.color} for p in remaining
                    ],
                },
                exclude=None,
            )
        else:
            del self._rooms[project_id]

    async def broadcast_from(self, project_id: str, sender: SendsJson, message: dict[str, Any]) -> None:
        await self._broadcast(project_id, message, exclude=sender)

    async def _broadcast(self, project_id: str, message: dict[str, Any], exclude: SendsJson | None) -> None:
        for participant in self._rooms.get(project_id, []):
            if participant.connection is exclude:
                continue
            await participant.connection.send_json(message)

    def room_size(self, project_id: str) -> int:
        return len(self._rooms.get(project_id, []))


# One shared manager for the whole process — rooms are keyed by project
# id, so this safely serves every project's collaboration session.
collaboration_manager = CollaborationManager()
