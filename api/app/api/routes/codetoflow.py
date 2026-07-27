from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.codetoflow.pipeline import generate_flowchart_from_code
from app.codetoflow.python_ast_adapter import UnsupportedSourceError
from app.codetoflow.schemas import CodeToFlowchartRequest, CodeToFlowchartResponse, FlowEdgeOut, FlowNodeOut
from app.models.user import User

router = APIRouter(prefix="/codetoflow", tags=["codetoflow"])

NODE_FILL = "#1B1E29"
NODE_STROKE = "#7C5CFF"
EDGE_STROKE = "#7C5CFF"


@router.post("/generate", response_model=CodeToFlowchartResponse)
def generate(payload: CodeToFlowchartRequest, _: User = Depends(get_current_user)):
    try:
        result = generate_flowchart_from_code(payload.code, payload.language)
    except UnsupportedSourceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SyntaxError as e:
        raise HTTPException(status_code=400, detail=f"Python syntax error: {e}")

    return CodeToFlowchartResponse(
        nodes=[
            FlowNodeOut(
                id=n.id, type=n.type, x=n.x, y=n.y, width=n.width, height=n.height,
                text=n.text, fill=NODE_FILL, stroke=NODE_STROKE,
            )
            for n in result.nodes
        ],
        edges=[
            FlowEdgeOut(
                id=e.id, fromNodeId=e.from_id, toNodeId=e.to_id,
                points=[e.from_point[0], e.from_point[1], e.to_point[0], e.to_point[1]],
                stroke=EDGE_STROKE, label=e.label,
            )
            for e in result.edges
        ],
        warnings=result.warnings,
    )
