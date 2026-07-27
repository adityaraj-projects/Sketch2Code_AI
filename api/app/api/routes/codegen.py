from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.codegen.emitters.registry import EMITTER_REGISTRY
from app.codegen.pipeline import generate_code
from app.codegen.schemas import CodegenRequest, CodegenResponse, SupportedLanguagesResponse
from app.models.user import User

router = APIRouter(prefix="/codegen", tags=["codegen"])


@router.get("/languages", response_model=SupportedLanguagesResponse)
def list_languages():
    return SupportedLanguagesResponse(languages=sorted(EMITTER_REGISTRY.keys()))


@router.post("/generate", response_model=CodegenResponse)
def generate(payload: CodegenRequest, _: User = Depends(get_current_user)):
    try:
        result = generate_code(
            [n.model_dump() for n in payload.nodes],
            [e.model_dump() for e in payload.edges],
            payload.language,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return CodegenResponse(
        code=result.code,
        language=result.language,
        file_extension=result.file_extension,
        warnings=result.warnings,
    )
