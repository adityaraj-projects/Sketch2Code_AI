from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.complexity.pipeline import analyze_flowchart_complexity
from app.complexity.schemas import ComplexityRequest, ComplexityResponse
from app.explainer.providers import TextProviderError, get_configured_text_provider
from app.models.user import User

router = APIRouter(prefix="/complexity", tags=["complexity"])


@router.post("/analyze", response_model=ComplexityResponse)
def analyze(payload: ComplexityRequest, _: User = Depends(get_current_user)):
    narrative_provider = None
    narrative_unavailable_reason = None

    if payload.include_ai_narrative:
        try:
            narrative_provider = get_configured_text_provider()
        except TextProviderError as e:
            narrative_unavailable_reason = str(e)

    output = analyze_flowchart_complexity(
        [n.model_dump() for n in payload.nodes],
        [e.model_dump() for e in payload.edges],
        narrative_provider=narrative_provider,
    )

    return ComplexityResponse(
        time_complexity=output.result.time_complexity,
        space_complexity=output.result.space_complexity,
        reasoning=output.result.reasoning,
        suggestions=output.result.suggestions,
        confidence=output.result.confidence,
        narrative=output.narrative,
        narrative_unavailable_reason=narrative_unavailable_reason,
        warnings=output.structuring_warnings,
    )
