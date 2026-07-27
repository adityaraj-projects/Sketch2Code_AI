from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.explainer.providers import TextProviderError, get_configured_text_provider
from app.models.user import User
from app.voicemode.pipeline import generate_flowchart_from_speech
from app.voicemode.schemas import VoiceModeEdgeOut, VoiceModeNodeOut, VoiceModeRequest, VoiceModeResponse

router = APIRouter(prefix="/voicemode", tags=["voicemode"])

NODE_FILL = "#1B1E29"
NODE_STROKE = "#7C5CFF"
EDGE_STROKE = "#7C5CFF"


@router.post("/generate", response_model=VoiceModeResponse)
def generate(payload: VoiceModeRequest, _: User = Depends(get_current_user)):
    if not payload.description.strip():
        raise HTTPException(status_code=400, detail="No speech was captured — try again.")

    try:
        provider = get_configured_text_provider()
    except TextProviderError as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = generate_flowchart_from_speech(payload.description, provider)

    return VoiceModeResponse(
        success=result.success,
        nodes=[
            VoiceModeNodeOut(
                id=n.id, type=n.type, x=n.x, y=n.y, width=n.width, height=n.height,
                text=n.text, fill=NODE_FILL, stroke=NODE_STROKE,
            )
            for n in result.nodes
        ],
        edges=[
            VoiceModeEdgeOut(
                id=e.id, fromNodeId=e.from_id, toNodeId=e.to_id,
                points=[e.from_point[0], e.from_point[1], e.to_point[0], e.to_point[1]],
                stroke=EDGE_STROKE, label=e.label,
            )
            for e in result.edges
        ],
        warnings=result.warnings,
        generated_code=result.generated_code,
        error_message=result.error_message,
    )
