from __future__ import annotations

from pydantic import BaseModel


class ComplexityNodeIn(BaseModel):
    id: str
    type: str
    text: str = ""


class ComplexityEdgeIn(BaseModel):
    id: str
    fromNodeId: str
    toNodeId: str
    label: str | None = None


class ComplexityRequest(BaseModel):
    nodes: list[ComplexityNodeIn]
    edges: list[ComplexityEdgeIn]
    include_ai_narrative: bool = True


class ComplexityResponse(BaseModel):
    time_complexity: str
    space_complexity: str
    reasoning: list[str]
    suggestions: list[str]
    confidence: str
    narrative: str | None = None
    narrative_unavailable_reason: str | None = None
    warnings: list[str]
