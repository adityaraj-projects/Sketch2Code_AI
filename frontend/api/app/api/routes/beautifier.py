from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.beautifier.pipeline import beautify_flowchart
from app.beautifier.schemas import BeautifiedEdgeOut, BeautifiedNodeOut, BeautifyRequest, BeautifyResponse
from app.models.user import User

router = APIRouter(prefix="/beautifier", tags=["beautifier"])

NODE_FILL = "#1B1E29"
NODE_STROKE = "#7C5CFF"
EDGE_STROKE = "#7C5CFF"


@router.post("/beautify", response_model=BeautifyResponse)
def beautify(payload: BeautifyRequest, _: User = Depends(get_current_user)):
    result = beautify_flowchart(
        [n.model_dump() for n in payload.nodes],
        [e.model_dump() for e in payload.edges],
    )

    return BeautifyResponse(
        nodes=[
            BeautifiedNodeOut(
                id=n.id, type=n.type, x=n.x, y=n.y, width=n.width, height=n.height,
                text=n.text, fill=NODE_FILL, stroke=NODE_STROKE,
            )
            for n in result.nodes
        ],
        edges=[
            BeautifiedEdgeOut(
                id=e.id, fromNodeId=e.from_id, toNodeId=e.to_id,
                points=[e.from_point[0], e.from_point[1], e.to_point[0], e.to_point[1]],
                stroke=EDGE_STROKE, label=e.label,
            )
            for e in result.edges
        ],
        warnings=result.warnings,
    )
