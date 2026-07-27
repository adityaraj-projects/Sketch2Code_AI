"""
The chat assistant doesn't have its own understanding of flowcharts —
it's a router in front of the pipelines that already do. Bug Detector,
Complexity Analysis, Code Generation, and the Beautifier are fully
deterministic and work here with zero AI dependency; only "explain this"
and genuinely open-ended questions need an LLM, and those degrade to a
clear, honest fallback message (not silence, not a fake answer) when no
provider is configured.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.beautifier.pipeline import beautify_flowchart
from app.bugdetector.detector import detect_bugs
from app.chatassistant.intent_router import Intent, classify_intent
from app.chatassistant.language_detector import detect_language
from app.codegen.graph_structurer import GraphEdge, GraphNode, GraphStructurer
from app.codegen.pipeline import generate_code
from app.complexity.pipeline import analyze_flowchart_complexity
from app.explainer.providers import TextProvider
from app.explainer.pseudocode_renderer import program_to_pseudocode

NODE_FILL = "#1B1E29"
NODE_STROKE = "#7C5CFF"
EDGE_STROKE = "#7C5CFF"

_NO_AI_FALLBACK = (
    "I can check for bugs, analyze time/space complexity, generate code, or beautify "
    "the layout without needing anything extra — just ask. Free-form explanations and "
    "open-ended questions need an AI provider configured in the backend's .env (see the "
    "README's AI Explainer section) — that part isn't available right now."
)


@dataclass
class ChatResult:
    reply: str
    intent: str
    data: dict[str, Any] | None = None


def _serialize_laid_out(nodes, edges) -> tuple[list[dict], list[dict]]:
    node_dicts = [
        {
            "id": n.id, "type": n.type, "x": n.x, "y": n.y, "width": n.width, "height": n.height,
            "text": n.text, "fill": NODE_FILL, "stroke": NODE_STROKE,
        }
        for n in nodes
    ]
    edge_dicts = [
        {
            "id": e.id, "fromNodeId": e.from_id, "toNodeId": e.to_id,
            "points": [e.from_point[0], e.from_point[1], e.to_point[0], e.to_point[1]],
            "stroke": EDGE_STROKE, "label": e.label,
        }
        for e in edges
    ]
    return node_dicts, edge_dicts


def _handle_bug_check(nodes: list[GraphNode], edges: list[GraphEdge]) -> ChatResult:
    findings = detect_bugs(nodes, edges)
    if not findings:
        return ChatResult(reply="I didn't find any structural issues — Start/End are present, every shape connects, and decisions look properly formed.", intent=Intent.BUG_CHECK.value)

    lines = [f"I found {len(findings)} issue(s):", ""]
    for f in findings:
        icon = "\u274c" if f.severity == "error" else "\u26a0\ufe0f"
        lines.append(f"{icon} {f.message}")
    return ChatResult(
        reply="\n".join(lines),
        intent=Intent.BUG_CHECK.value,
        data={"findings": [{"severity": f.severity, "category": f.category, "message": f.message, "node_ids": f.node_ids} for f in findings]},
    )


def _handle_complexity(nodes_data, edges_data, provider: TextProvider | None) -> ChatResult:
    output = analyze_flowchart_complexity(nodes_data, edges_data, narrative_provider=provider)
    r = output.result
    lines = [f"Time complexity: {r.time_complexity}", f"Space complexity: {r.space_complexity}", ""]
    lines.extend(r.reasoning)
    if r.suggestions:
        lines.append("")
        lines.append("Optimization ideas:")
        lines.extend(f"- {s}" for s in r.suggestions)
    if output.narrative:
        lines.append("")
        lines.append(output.narrative)
    return ChatResult(
        reply="\n".join(lines),
        intent=Intent.COMPLEXITY.value,
        data={"time_complexity": r.time_complexity, "space_complexity": r.space_complexity},
    )


def _handle_generate_code(nodes_data, edges_data, message: str) -> ChatResult:
    language = detect_language(message)
    result = generate_code(nodes_data, edges_data, language)
    reply = f"Here's the {language} code:\n\n```{language}\n{result.code}```"
    if result.warnings:
        reply += "\n\nNotes:\n" + "\n".join(f"- {w}" for w in result.warnings)
    return ChatResult(reply=reply, intent=Intent.GENERATE_CODE.value, data={"code": result.code, "language": language})


def _handle_beautify(nodes_data, edges_data) -> ChatResult:
    result = beautify_flowchart(nodes_data, edges_data)
    node_dicts, edge_dicts = _serialize_laid_out(result.nodes, result.edges)
    reply = f"Done — rearranged into a clean layout ({len(node_dicts)} shapes, {len(edge_dicts)} connectors)."
    if result.warnings:
        reply += "\n\nNotes:\n" + "\n".join(f"- {w}" for w in result.warnings)
    return ChatResult(reply=reply, intent=Intent.BEAUTIFY.value, data={"nodes": node_dicts, "edges": edge_dicts})


def _handle_explain(nodes: list[GraphNode], edges: list[GraphEdge], provider: TextProvider | None) -> ChatResult:
    program = GraphStructurer(nodes, edges).structure()
    if not program.body:
        return ChatResult(reply="This flowchart doesn't have a Start shape connected to anything yet — draw the logic first.", intent=Intent.EXPLAIN.value)

    pseudocode = program_to_pseudocode(program)
    if provider is None:
        return ChatResult(
            reply="I can't write a prose explanation without an AI provider configured, but here's the logic as pseudocode:\n\n" + pseudocode,
            intent=Intent.EXPLAIN.value,
        )

    system_prompt = (
        "You are a patient computer science tutor. Explain the given flowchart's pseudocode "
        "in plain, beginner-friendly English, in a few short sentences."
    )
    user_prompt = f"```\n{pseudocode}\n```\n\nExplain this."
    reply = provider.generate(system_prompt, user_prompt)
    return ChatResult(reply=reply, intent=Intent.EXPLAIN.value)


def _handle_general(nodes: list[GraphNode], edges: list[GraphEdge], message: str, provider: TextProvider | None, images: list[str] | None = None) -> ChatResult:
    if provider is None:
        return ChatResult(reply=_NO_AI_FALLBACK, intent=Intent.GENERAL.value)

    program = GraphStructurer(nodes, edges).structure()
    pseudocode = program_to_pseudocode(program) if program.body else "(empty flowchart)"
    system_prompt = (
        "You are a helpful assistant embedded in a flowchart-to-code tool called Sketch2Code AI. "
        "The person is looking at a specific flowchart or solving a coding problem on a whiteboard. Answer their "
        "question conversationally and concisely, grounded in the flowchart or any attached images when relevant."
    )
    user_prompt = f"Whiteboard pseudocode:\n```\n{pseudocode}\n```\n\nQuestion: {message}"
    if images:
        user_prompt += "\n\nNote: The user has attached/pasted one or more screenshot images from their canvas (e.g. LeetCode questions or descriptions). Please read the text inside these images carefully to answer their question."

    reply = provider.generate(system_prompt, user_prompt, images)
    return ChatResult(reply=reply, intent=Intent.GENERAL.value)


def handle_chat_message(
    message: str, nodes_data: list[dict[str, Any]], edges_data: list[dict[str, Any]], provider: TextProvider | None
) -> ChatResult:
    nodes = [GraphNode(id=n["id"], type=n["type"], text=n.get("text", "")) for n in nodes_data if n.get("type") != "image"]
    edges = [
        GraphEdge(id=e["id"], from_id=e["fromNodeId"], to_id=e["toNodeId"], label=e.get("label"))
        for e in edges_data
    ]

    images = [n["imageUrl"] for n in nodes_data if n.get("type") == "image" and n.get("imageUrl")]

    intent = classify_intent(message)

    if intent == Intent.BUG_CHECK:
        return _handle_bug_check(nodes, edges)
    if intent == Intent.COMPLEXITY:
        return _handle_complexity(nodes_data, edges_data, provider)
    if intent == Intent.GENERATE_CODE:
        return _handle_generate_code(nodes_data, edges_data, message)
    if intent == Intent.BEAUTIFY:
        return _handle_beautify(nodes_data, edges_data)
    if intent == Intent.EXPLAIN:
        return _handle_explain(nodes, edges, provider)
    return _handle_general(nodes, edges, message, provider, images)
