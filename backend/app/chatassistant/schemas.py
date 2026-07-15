from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ChatNodeIn(BaseModel):
    id: str
    type: str
    text: str = ""
    imageUrl: str | None = None


class ChatEdgeIn(BaseModel):
    id: str
    fromNodeId: str
    toNodeId: str
    label: str | None = None


class ChatRequest(BaseModel):
    message: str
    nodes: list[ChatNodeIn]
    edges: list[ChatEdgeIn]


class ChatResponse(BaseModel):
    reply: str
    intent: str
    data: dict[str, Any] | None = None
