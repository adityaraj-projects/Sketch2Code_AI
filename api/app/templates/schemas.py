from __future__ import annotations

from pydantic import BaseModel


class TemplateSummary(BaseModel):
    id: str
    name: str
    category: str
    description: str
    executable: bool


class TemplateListResponse(BaseModel):
    templates: list[TemplateSummary]


class TemplateNodeOut(BaseModel):
    id: str
    type: str
    x: float
    y: float
    width: float
    height: float
    text: str
    fill: str
    stroke: str


class TemplateEdgeOut(BaseModel):
    id: str
    fromNodeId: str
    toNodeId: str
    points: list[float]
    stroke: str
    label: str | None = None


class TemplateLoadResponse(BaseModel):
    template: TemplateSummary
    nodes: list[TemplateNodeOut]
    edges: list[TemplateEdgeOut]
    warnings: list[str]
