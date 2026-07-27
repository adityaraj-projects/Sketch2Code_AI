from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.bugdetector.detector import detect_bugs
from app.bugdetector.schemas import BugDetectRequest, BugDetectResponse, FindingOut
from app.codegen.graph_structurer import GraphEdge, GraphNode
from app.models.user import User

router = APIRouter(prefix="/bugdetector", tags=["bugdetector"])


@router.post("/scan", response_model=BugDetectResponse)
def scan(payload: BugDetectRequest, _: User = Depends(get_current_user)):
    nodes = [GraphNode(id=n.id, type=n.type, text=n.text) for n in payload.nodes]
    edges = [GraphEdge(id=e.id, from_id=e.fromNodeId, to_id=e.toNodeId, label=e.label) for e in payload.edges]

    findings = detect_bugs(nodes, edges)

    return BugDetectResponse(
        findings=[
            FindingOut(severity=f.severity, category=f.category, message=f.message, node_ids=f.node_ids)
            for f in findings
        ],
        error_count=sum(1 for f in findings if f.severity == "error"),
        warning_count=sum(1 for f in findings if f.severity == "warning"),
    )
