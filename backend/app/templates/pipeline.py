from __future__ import annotations

from app.codetoflow.flowchart_layout import FlowchartLayout
from app.templates.definitions import TEMPLATE_REGISTRY, TemplateMeta, get_template


def list_templates() -> list[TemplateMeta]:
    return TEMPLATE_REGISTRY


def load_template_flowchart(template_id: str):
    template = get_template(template_id)
    if template is None:
        raise ValueError(f"Unknown template '{template_id}'")

    program = template.builder()
    layout = FlowchartLayout()
    nodes, edges, warnings = layout.build(program)
    return template, nodes, edges, warnings
