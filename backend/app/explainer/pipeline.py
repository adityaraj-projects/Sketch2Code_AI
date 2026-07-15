from __future__ import annotations

from dataclasses import dataclass

from typing import Any

from app.codegen.graph_structurer import GraphEdge, GraphNode, GraphStructurer
from app.explainer.prompts import ExplainMode, build_prompt
from app.explainer.providers import TextProvider
from app.explainer.pseudocode_renderer import program_to_pseudocode


@dataclass
class ExplainResult:
    explanation: str
    pseudocode: str
    warnings: list[str]


def explain_flowchart(
    nodes_data: list[dict[str, Any]], edges_data: list[dict[str, Any]], mode: ExplainMode, provider: TextProvider, custom_prompt: str | None = None
) -> ExplainResult:
    nodes = [GraphNode(id=n["id"], type=n["type"], text=n.get("text", "")) for n in nodes_data]
    edges = [
        GraphEdge(id=e["id"], from_id=e["fromNodeId"], to_id=e["toNodeId"], label=e.get("label"))
        for e in edges_data
    ]

    structurer = GraphStructurer(nodes, edges)
    program = structurer.structure()

    pseudocode = ""
    if program.body:
        pseudocode = program_to_pseudocode(program)

    if not pseudocode and mode not in ("custom", "dry_run"):
        return ExplainResult(
            explanation="This flowchart doesn't have a Start shape connected to anything yet — "
            "draw the logic first, then ask for an explanation.",
            pseudocode="",
            warnings=structurer.warnings,
        )

    system_prompt, user_prompt = build_prompt(pseudocode, mode, custom_prompt)

    if mode == "custom" and not pseudocode and nodes_data:
        raw_nodes_desc = "\n".join([f"- Shape ({n['type']}): {n.get('text', '')}" for n in nodes_data])
        user_prompt += f"\n\nHere are some individual shapes placed on the whiteboard canvas:\n{raw_nodes_desc}"

    explanation = provider.generate(system_prompt, user_prompt)

    return ExplainResult(explanation=explanation, pseudocode=pseudocode, warnings=structurer.warnings)
