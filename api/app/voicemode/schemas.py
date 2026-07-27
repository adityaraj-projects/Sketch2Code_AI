from __future__ import annotations

from pydantic import BaseModel


class VoiceModeRequest(BaseModel):
    description: str


class VoiceModeNodeOut(BaseModel):
    id: str
    type: str
    x: float
    y: float
    width: float
    height: float
    text: str
    fill: str
    stroke: str


class VoiceModeEdgeOut(BaseModel):
    id: str
    fromNodeId: str
    toNodeId: str
    points: list[float]
    stroke: str
    label: str | None = None


class VoiceModeResponse(BaseModel):
    success: bool
    nodes: list[VoiceModeNodeOut]
    edges: list[VoiceModeEdgeOut]
    warnings: list[str]
    generated_code: str
    error_message: str | None = None
