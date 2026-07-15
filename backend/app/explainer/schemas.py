from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ExplainNodeIn(BaseModel):
    id: str
    type: str
    text: str = ""


class ExplainEdgeIn(BaseModel):
    id: str
    fromNodeId: str
    toNodeId: str
    label: str | None = None


class ExplainRequest(BaseModel):
    nodes: list[ExplainNodeIn]
    edges: list[ExplainEdgeIn]
    mode: Literal["simple", "line_by_line", "interview", "study_notes", "generate_quiz", "dry_run", "custom"] = "simple"
    custom_prompt: str | None = None


class ExplainResponse(BaseModel):
    explanation: str
    pseudocode: str
    warnings: list[str]
