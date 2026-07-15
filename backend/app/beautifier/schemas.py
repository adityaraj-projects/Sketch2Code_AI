from __future__ import annotations

from pydantic import BaseModel


class BeautifyNodeIn(BaseModel):
    id: str
    type: str
    text: str = ""


class BeautifyEdgeIn(BaseModel):
    id: str
    fromNodeId: str
    toNodeId: str
    label: str | None = None


class BeautifyRequest(BaseModel):
    nodes: list[BeautifyNodeIn]
    edges: list[BeautifyEdgeIn]


class BeautifiedNodeOut(BaseModel):
    id: str
    type: str
    x: float
    y: float
    width: float
    height: float
    text: str
    fill: str
    stroke: str


class BeautifiedEdgeOut(BaseModel):
    id: str
    fromNodeId: str
    toNodeId: str
    points: list[float]
    stroke: str
    label: str | None = None


class BeautifyResponse(BaseModel):
    nodes: list[BeautifiedNodeOut]
    edges: list[BeautifiedEdgeOut]
    warnings: list[str]
