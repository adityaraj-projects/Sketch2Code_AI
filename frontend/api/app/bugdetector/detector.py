"""
Detects structural problems in a flowchart by actually analyzing its
graph — not a list of canned warnings.

The key technique is a two-directional reachability check: compute every
node reachable *forward* from Start, and every node that can reach *any*
End *backward*. A node that's reachable from Start but can never reach an
End represents a guaranteed non-terminating path — whether that's a
literal infinite loop (a cycle with no exit) or a structural dead end
(a branch that trails off with no way back to the main flow), the
symptom is the same: execution can enter that region and never leave it.
That single check, run once, catches both "infinite loops" and a good
chunk of "invalid structure" without needing separate cycle-detection
code.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from app.codegen.branch_resolution import resolve_branch
from app.codegen.graph_structurer import GraphEdge, GraphNode


@dataclass
class Finding:
    severity: str
    category: str
    message: str
    node_ids: list[str] = field(default_factory=list)


def _bfs_forward(start_id: str, out_edges: dict[str, list[GraphEdge]]) -> set[str]:
    visited = {start_id}
    queue = deque([start_id])
    while queue:
        current = queue.popleft()
        for e in out_edges.get(current, []):
            if e.to_id not in visited:
                visited.add(e.to_id)
                queue.append(e.to_id)
    return visited


def _bfs_backward(end_ids: set[str], in_edges: dict[str, list[GraphEdge]]) -> set[str]:
    visited = set(end_ids)
    queue = deque(end_ids)
    while queue:
        current = queue.popleft()
        for e in in_edges.get(current, []):
            if e.from_id not in visited:
                visited.add(e.from_id)
                queue.append(e.from_id)
    return visited


def detect_bugs(nodes: list[GraphNode], edges: list[GraphEdge]) -> list[Finding]:
    findings: list[Finding] = []

    out_edges: dict[str, list[GraphEdge]] = {}
    in_edges: dict[str, list[GraphEdge]] = {}
    for e in edges:
        out_edges.setdefault(e.from_id, []).append(e)
        in_edges.setdefault(e.to_id, []).append(e)

    start_nodes = [n for n in nodes if n.type == "start"]
    end_nodes = [n for n in nodes if n.type == "end"]

    if not start_nodes:
        findings.append(Finding("error", "structure", "This flowchart has no Start shape."))
    elif len(start_nodes) > 1:
        findings.append(
            Finding(
                "warning", "structure",
                f"Found {len(start_nodes)} Start shapes — a flowchart should have exactly one.",
                [n.id for n in start_nodes],
            )
        )
    if not end_nodes:
        findings.append(
            Finding("warning", "structure", "This flowchart has no End shape — it's not clear where it should stop.")
        )

    for s in start_nodes:
        outs = out_edges.get(s.id, [])
        if len(outs) == 0:
            findings.append(Finding("error", "missing_arrow", "The Start shape isn't connected to anything.", [s.id]))
        elif len(outs) > 1:
            findings.append(
                Finding(
                    "warning", "structure",
                    "The Start shape has more than one outgoing connector — flow should begin with exactly one path.",
                    [s.id],
                )
            )

    for e_node in end_nodes:
        if out_edges.get(e_node.id):
            findings.append(
                Finding("warning", "structure", "An End shape has an outgoing connector — End should be a final step.", [e_node.id])
            )

    for n in nodes:
        if n.type != "end" and not out_edges.get(n.id):
            label = n.text.strip() or n.type
            findings.append(
                Finding("error", "missing_arrow", f"The shape \"{label}\" has no outgoing connector — the flow just stops there.", [n.id])
            )
        if n.type != "start" and not in_edges.get(n.id):
            label = n.text.strip() or n.type
            findings.append(
                Finding("warning", "disconnected_node", f"The shape \"{label}\" has nothing connecting into it.", [n.id])
            )

    for n in nodes:
        if n.type != "decision":
            continue
        outs = out_edges.get(n.id, [])
        label = n.text.strip() or "this decision"

        if len(outs) == 1:
            findings.append(
                Finding("error", "invalid_decision", f'The decision "{label}" only has one outgoing connector — it needs both a Yes and a No path.', [n.id])
            )
        elif len(outs) > 2:
            findings.append(
                Finding(
                    "warning", "invalid_decision",
                    f'The decision "{label}" has {len(outs)} outgoing connectors — a decision should have exactly two (Yes/No).',
                    [n.id],
                )
            )

        if len(outs) == 2 and outs[0].to_id == outs[1].to_id:
            findings.append(
                Finding("warning", "invalid_decision", f'Both branches of "{label}" lead to the same shape, so the decision has no effect.', [n.id])
            )

        if len(outs) >= 2:
            _, _, branch_warnings = resolve_branch(n.id, outs)
            for w in branch_warnings:
                findings.append(Finding("warning", "invalid_decision", w, [n.id]))

    if start_nodes and end_nodes:
        reachable_from_start = _bfs_forward(start_nodes[0].id, out_edges)
        can_reach_end = _bfs_backward({n.id for n in end_nodes}, in_edges)
        stuck = sorted(reachable_from_start - can_reach_end)
        if stuck:
            findings.append(
                Finding(
                    "error", "infinite_loop",
                    f"{len(stuck)} shape(s) are reachable from Start but can never reach an End — "
                    "this looks like an infinite loop or a dead end with no way back to the main flow.",
                    stuck,
                )
            )

    return findings
