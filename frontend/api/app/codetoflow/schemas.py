from __future__ import annotations

from pydantic import BaseModel


class CodeToFlowchartRequest(BaseModel):
    code: str
    language: str = "python"


class FlowNodeOut(BaseModel):
    id: str
    type: str
    x: float
    y: float
    width: float
    height: float
    text: str
    fill: str
    stroke: str


class FlowEdgeOut(BaseModel):
    id: str
    fromNodeId: str
    toNodeId: str
    points: list[float]
    stroke: str
    label: str | None = None


class CodeToFlowchartResponse(BaseModel):
    nodes: list[FlowNodeOut]
    edges: list[FlowEdgeOut]
    warnings: list[str]
