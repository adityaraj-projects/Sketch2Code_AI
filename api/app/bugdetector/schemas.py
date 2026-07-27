from __future__ import annotations

from pydantic import BaseModel


class BugDetectNodeIn(BaseModel):
    id: str
    type: str
    text: str = ""


class BugDetectEdgeIn(BaseModel):
    id: str
    fromNodeId: str
    toNodeId: str
    label: str | None = None


class BugDetectRequest(BaseModel):
    nodes: list[BugDetectNodeIn]
    edges: list[BugDetectEdgeIn]


class FindingOut(BaseModel):
    severity: str
    category: str
    message: str
    node_ids: list[str]


class BugDetectResponse(BaseModel):
    findings: list[FindingOut]
    error_count: int
    warning_count: int
