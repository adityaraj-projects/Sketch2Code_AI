from __future__ import annotations

from pydantic import BaseModel


class RawStrokeIn(BaseModel):
    id: str
    tool: str
    points: list[float]
    pressures: list[float] = []
    color: str = "#EDEBE6"
    width: float = 3


class SnapshotIn(BaseModel):
    image_base64: str
    viewport_x: float
    viewport_y: float
    viewport_zoom: float
    pixel_ratio: float = 1.0


class RecognizeRequest(BaseModel):
    strokes: list[RawStrokeIn]
    snapshot: SnapshotIn | None = None


class RecognizedNodeOut(BaseModel):
    id: str
    type: str
    x: float
    y: float
    width: float
    height: float
    text: str
    fill: str
    stroke: str


class RecognizedEdgeOut(BaseModel):
    id: str
    fromNodeId: str
    toNodeId: str
    points: list[float]
    stroke: str


class RecognizeResponse(BaseModel):
    nodes: list[RecognizedNodeOut]
    edges: list[RecognizedEdgeOut]
    consumed_stroke_ids: list[str]
    unrecognized_stroke_ids: list[str]
    ocr_warning: str | None = None
