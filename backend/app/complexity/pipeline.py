from __future__ import annotations

from dataclasses import dataclass

from app.codegen.graph_structurer import GraphEdge, GraphNode, GraphStructurer
from app.complexity.analyzer import ComplexityResult, analyze_complexity
from app.explainer.providers import TextProvider

_NARRATIVE_SYSTEM_PROMPT = (
    "You are a computer science tutor. You will be given an already-computed time "
    "complexity, space complexity, and the reasoning behind them for a specific "
    "algorithm, plus a list of optimization ideas. Write a short, clear explanation "
    "(3-5 sentences) summarizing why the complexity is what it is, in your own words, "
    "for a student. Then if there are optimization ideas, briefly mention them. "
    "Do not change or second-guess the stated complexity — treat it as fact and "
    "explain it, the way a tutor would explain a result their student already computed."
)


@dataclass
class ComplexityAnalysisOutput:
    result: ComplexityResult
    narrative: str | None
    structuring_warnings: list[str]


def analyze_flowchart_complexity(
    nodes_data: list[dict], edges_data: list[dict], narrative_provider: TextProvider | None = None
) -> ComplexityAnalysisOutput:
    nodes = [GraphNode(id=n["id"], type=n["type"], text=n.get("text", "")) for n in nodes_data]
    edges = [
        GraphEdge(id=e["id"], from_id=e["fromNodeId"], to_id=e["toNodeId"], label=e.get("label"))
        for e in edges_data
    ]

    structurer = GraphStructurer(nodes, edges)
    program = structurer.structure()
    result = analyze_complexity(program)

    narrative = None
    if narrative_provider is not None:
        user_prompt = (
            f"Time complexity: {result.time_complexity}\n"
            f"Space complexity: {result.space_complexity}\n"
            f"Confidence: {result.confidence}\n"
            "Reasoning:\n" + "\n".join(f"- {r}" for r in result.reasoning) + "\n\n"
            "Optimization ideas:\n"
            + ("\n".join(f"- {s}" for s in result.suggestions) if result.suggestions else "(none)")
        )
        narrative = narrative_provider.generate(_NARRATIVE_SYSTEM_PROMPT, user_prompt)

    return ComplexityAnalysisOutput(result=result, narrative=narrative, structuring_warnings=structurer.warnings)
