"""
"Beautify" doesn't nudge existing pixel positions around — it rebuilds
the diagram from its actual logical structure, the same way Feature 3
(Code -> Flowchart) lays out a fresh diagram from parsed code. The
insight: a flowchart's node/edge graph already *is* structured logic
(GraphStructurer, from Feature 2, understands it), so regenerating clean
positions is just running that same structure through the same
FlowchartLayout engine from Feature 3 — no new layout code needed, only
composition of two already-tested pieces.

This does mean text gets re-normalized through the parser/formatter
round-trip (e.g. "n>0" becomes "n > 0") and connector/free-text shapes
get folded into ordinary process boxes, since the layout engine optimizes
positions for the standard control-flow symbols. Both are documented,
not hidden.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.codegen.graph_structurer import GraphEdge, GraphNode, GraphStructurer
from app.codetoflow.flowchart_layout import FlowchartLayout


@dataclass
class BeautifyResult:
    nodes: list
    edges: list
    warnings: list[str]


def beautify_flowchart(nodes_data: list[dict], edges_data: list[dict]) -> BeautifyResult:
    nodes = [GraphNode(id=n["id"], type=n["type"], text=n.get("text", "")) for n in nodes_data]
    edges = [
        GraphEdge(id=e["id"], from_id=e["fromNodeId"], to_id=e["toNodeId"], label=e.get("label"))
        for e in edges_data
    ]

    structurer = GraphStructurer(nodes, edges)
    program = structurer.structure()

    layout = FlowchartLayout()
    laid_out_nodes, laid_out_edges, layout_warnings = layout.build(program)

    return BeautifyResult(
        nodes=laid_out_nodes,
        edges=laid_out_edges,
        warnings=structurer.warnings + layout_warnings,
    )
