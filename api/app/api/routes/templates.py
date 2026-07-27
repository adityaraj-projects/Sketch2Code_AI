from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.models.user import User
from app.templates.pipeline import list_templates, load_template_flowchart
from app.templates.schemas import (
    TemplateEdgeOut,
    TemplateListResponse,
    TemplateLoadResponse,
    TemplateNodeOut,
    TemplateSummary,
)

router = APIRouter(prefix="/templates", tags=["templates"])

NODE_FILL = "#1B1E29"
NODE_STROKE = "#7C5CFF"
EDGE_STROKE = "#7C5CFF"


@router.get("", response_model=TemplateListResponse)
def list_all(_: User = Depends(get_current_user)):
    templates = list_templates()
    return TemplateListResponse(
        templates=[
            TemplateSummary(id=t.id, name=t.name, category=t.category, description=t.description, executable=t.executable)
            for t in templates
        ]
    )


@router.get("/{template_id}/load", response_model=TemplateLoadResponse)
def load(template_id: str, _: User = Depends(get_current_user)):
    try:
        template, nodes, edges, warnings = load_template_flowchart(template_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return TemplateLoadResponse(
        template=TemplateSummary(
            id=template.id, name=template.name, category=template.category,
            description=template.description, executable=template.executable,
        ),
        nodes=[
            TemplateNodeOut(
                id=n.id, type=n.type, x=n.x, y=n.y, width=n.width, height=n.height,
                text=n.text, fill=NODE_FILL, stroke=NODE_STROKE,
            )
            for n in nodes
        ],
        edges=[
            TemplateEdgeOut(
                id=e.id, fromNodeId=e.from_id, toNodeId=e.to_id,
                points=[e.from_point[0], e.from_point[1], e.to_point[0], e.to_point[1]],
                stroke=EDGE_STROKE, label=e.label,
            )
            for e in edges
        ],
        warnings=warnings,
    )
