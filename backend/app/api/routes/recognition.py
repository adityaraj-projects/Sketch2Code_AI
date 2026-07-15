from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.recognition.label_ocr import decode_snapshot
from app.recognition.pipeline import run_recognition_pipeline
from app.recognition.schemas import (
    RecognizedEdgeOut,
    RecognizedNodeOut,
    RecognizeRequest,
    RecognizeResponse,
)
from app.recognition.vision_providers import VisionProviderError, get_configured_vision_provider

router = APIRouter(prefix="/recognition", tags=["recognition"])

NODE_FILL = "#1B1E29"
NODE_STROKE = "#7C5CFF"
EDGE_STROKE = "#7C5CFF"


@router.post("/flowchart", response_model=RecognizeResponse)
def recognize_flowchart(payload: RecognizeRequest, _: User = Depends(get_current_user)):
    strokes_data = [s.model_dump() for s in payload.strokes]

    snapshot_ctx = None
    if payload.snapshot is not None:
        snapshot_ctx = decode_snapshot(
            payload.snapshot.image_base64,
            payload.snapshot.viewport_x,
            payload.snapshot.viewport_y,
            payload.snapshot.viewport_zoom,
            payload.snapshot.pixel_ratio,
        )

    vision_provider = None
    provider_error: str | None = None
    if snapshot_ctx is not None:
        try:
            vision_provider = get_configured_vision_provider()
        except VisionProviderError as e:
            provider_error = str(e)

    result = run_recognition_pipeline(strokes_data, vision_provider=vision_provider, snapshot=snapshot_ctx)

    return RecognizeResponse(
        nodes=[
            RecognizedNodeOut(
                id=n.id,
                type=n.node_type,
                x=n.bbox.min_x,
                y=n.bbox.min_y,
                width=n.bbox.width,
                height=n.bbox.height,
                text=n.text,
                fill=NODE_FILL,
                stroke=NODE_STROKE,
            )
            for n in result.nodes
        ],
        edges=[
            RecognizedEdgeOut(
                id=e.id,
                fromNodeId=e.from_node_id,
                toNodeId=e.to_node_id,
                points=[e.points[0][0], e.points[0][1], e.points[1][0], e.points[1][1]],
                stroke=EDGE_STROKE,
            )
            for e in result.edges
        ],
        consumed_stroke_ids=list(result.consumed_stroke_ids),
        unrecognized_stroke_ids=list(result.unrecognized_stroke_ids),
        ocr_warning=result.ocr_warning or provider_error,
    )
