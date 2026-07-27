from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.explainer.pipeline import explain_flowchart
from app.explainer.providers import TextProviderError, get_configured_text_provider
from app.explainer.schemas import ExplainRequest, ExplainResponse
from app.models.user import User

router = APIRouter(prefix="/explainer", tags=["explainer"])


@router.post("/explain", response_model=ExplainResponse)
def explain(payload: ExplainRequest, _: User = Depends(get_current_user)):
    try:
        provider = get_configured_text_provider()
    except TextProviderError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        result = explain_flowchart(
            [n.model_dump() for n in payload.nodes],
            [e.model_dump() for e in payload.edges],
            payload.mode,
            provider,
            payload.custom_prompt,
        )
    except Exception as e:
        err_str = str(e)
        if "quota" in err_str.lower() or "429" in err_str:
            raise HTTPException(status_code=429, detail="Gemini AI API rate limit reached (Quota Exceeded). Please wait a minute and try again!")
        raise HTTPException(status_code=502, detail=f"The AI explainer failed: {e}")

    return ExplainResponse(explanation=result.explanation, pseudocode=result.pseudocode, warnings=result.warnings)
