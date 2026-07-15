from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ExecNodeIn(BaseModel):
    id: str
    type: str
    text: str = ""


class ExecEdgeIn(BaseModel):
    id: str
    fromNodeId: str
    toNodeId: str
    label: str | None = None


class ExecuteRequest(BaseModel):
    nodes: list[ExecNodeIn]
    edges: list[ExecEdgeIn]
    input_values: list[str] = []


class TraceStepOut(BaseModel):
    step_index: int
    node_id: str
    node_type: str
    label: str
    variables: dict[str, Any]
    output: str | None = None
    branch_taken: str | None = None


class ExecuteResponse(BaseModel):
    steps: list[TraceStepOut]
    final_variables: dict[str, Any]
    console_output: list[str]
    status: str
    error_message: str | None = None
    error_node_id: str | None = None
    warnings: list[str]
