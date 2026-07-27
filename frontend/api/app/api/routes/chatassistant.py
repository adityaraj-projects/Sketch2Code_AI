from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.chatassistant.pipeline import handle_chat_message
from app.chatassistant.schemas import ChatRequest, ChatResponse
from app.explainer.providers import TextProviderError, get_configured_text_provider
from app.models.user import User

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, _: User = Depends(get_current_user)):
    try:
        provider = get_configured_text_provider()
    except TextProviderError:
        provider = None

    try:
        result = handle_chat_message(
            payload.message,
            [n.model_dump() for n in payload.nodes],
            [e.model_dump() for e in payload.edges],
            provider,
        )
    except Exception as e:
        from fastapi import HTTPException
        err_str = str(e)
        if "quota" in err_str.lower() or "429" in err_str:
            raise HTTPException(status_code=429, detail="Gemini AI API rate limit reached (Quota Exceeded). Please wait a minute and try again!")
        raise HTTPException(status_code=502, detail=f"AI Chat Assistant failed: {e}")

    return ChatResponse(reply=result.reply, intent=result.intent, data=result.data)
