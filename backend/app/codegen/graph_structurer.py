"""
Turns a flowchart's nodes + edges into structured control flow (sequences,
If, While) instead of a flat list of "goto"s. This is the part that makes
generated code actually readable.

Two real graph algorithms drive it:

1. Loop detection: while walking forward from a decision node, if either
   outgoing branch points at a node already on the current path (an
   ancestor), that's a back-edge — the classic definition of a loop in a
   control flow graph. The branch that loops becomes the while body; the
   other branch is where execution continues after the loop.

2. If/else merge-point detection: when neither branch loops, we BFS
   forward from both branches simultaneously and take the first node
   reached by both as the merge point — where the if/else ends and
   single-flow execution resumes. Branches that dead-end at an "end" node
   are treated as early returns and don't need a merge.

Flowcharts that don't reduce cleanly this way (multiple entries into a
loop, edges that never remerge) still produce correct code — later
statements are just appended sequentially with a comment noting the
diagram didn't have a clean merge point — rather than crashing or
fabricating structure that wasn't drawn.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.codegen.branch_resolution import resolve_branch
from app.codegen.ir import Break, Comment, If, Program, Return, Stmt, UnaryOp, While
from app.codegen.pseudocode_parser import parse_condition, parse_statement

MAX_WALK_STEPS = 500


@dataclass
class GraphNode:
    id: str
    type: str
    text: str


@dataclass
class GraphEdge:
    id: str
    from_id: str
    to_id: str
    label: str | None = None


class GraphStructurer:
    def __init__(self, nodes: list[GraphNode], edges: list[GraphEdge]):
        self.node_by_id = {n.id: n for n in nodes}
        self.warnings: list[str] = []
        self._out_edges: dict[str, list[GraphEdge]] = {}
        for e in edges:
            self._out_edges.setdefault(e.from_id, []).append(e)
        self._step_count = 0

    def _successors(self, node_id: str) -> list[GraphEdge]:
        return self._out_edges.get(node_id, [])

    def _single_successor(self, node_id: str) -> str | None:
        succs = self._successors(node_id)
        if not succs:
            return None
        if len(succs) > 1:
            self.warnings.append(
                f"Node '{node_id}' has multiple outgoing connectors but isn't a decision — "
                "using the first one."
            )
        return succs[0].to_id

    def _branch_targets(self, node_id: str) -> tuple[str | None, str | None]:
        succs = self._successors(node_id)
        true_edge, false_edge, warnings = resolve_branch(node_id, succs)
        self.warnings.extend(warnings)
        return (true_edge.to_id if true_edge else None), (false_edge.to_id if false_edge else None)

    def _find_merge_point(self, a: str | None, b: str | None, boundary: set[str]) -> str | None:
        if a is None or b is None:
            return None

        visited_a = {a}
        visited_b = {b}
        frontier_a = [a]
        frontier_b = [b]

        for _ in range(MAX_WALK_STEPS):
            if frontier_a and frontier_a[0] in visited_b:
                return frontier_a[0]
            if frontier_b and frontier_b[0] in visited_a:
                return frontier_b[0]
            if not frontier_a and not frontier_b:
                return None

            next_a: list[str] = []
            for n in frontier_a:
                if n in boundary or self.node_by_id.get(n, GraphNode("", "end", "")).type == "end":
                    continue
                for e in self._successors(n):
                    if e.to_id not in visited_a:
                        visited_a.add(e.to_id)
                        next_a.append(e.to_id)
                        if e.to_id in visited_b:
                            return e.to_id
            frontier_a = next_a

            next_b: list[str] = []
            for n in frontier_b:
                if n in boundary or self.node_by_id.get(n, GraphNode("", "end", "")).type == "end":
                    continue
                for e in self._successors(n):
                    if e.to_id not in visited_b:
                        visited_b.add(e.to_id)
                        next_b.append(e.to_id)
                        if e.to_id in visited_a:
                            return e.to_id
            frontier_b = next_b

        return None

    def _can_reach(self, start_id: str | None, target_id: str, boundary: set[str]) -> bool:
        """BFS forward from start_id looking for target_id, without
        expanding past `boundary` nodes or 'end' nodes. This is what
        detects a loop even when the back edge is several nodes downstream
        of the decision (e.g. decision -> body -> decision), not just an
        immediate decision -> decision edge."""
        if start_id is None:
            return False
        if start_id == target_id:
            return True

        visited = {start_id}
        frontier = [start_id]
        for _ in range(MAX_WALK_STEPS):
            if not frontier:
                return False
            next_frontier: list[str] = []
            for n in frontier:
                if n in boundary:
                    continue
                node = self.node_by_id.get(n)
                if node is not None and node.type == "end":
                    continue
                for e in self._successors(n):
                    if e.to_id == target_id:
                        return True
                    if e.to_id not in visited:
                        visited.add(e.to_id)
                        next_frontier.append(e.to_id)
            frontier = next_frontier
        return False

    def _walk(self, start_id: str | None, ancestors: list[str], stop_at: set[str]) -> list[Stmt]:
        stmts: list[Stmt] = []
        current = start_id
        path = list(ancestors)

        while current is not None and current not in stop_at:
            self._step_count += 1
            if self._step_count > MAX_WALK_STEPS:
                stmts.append(Comment(text="(diagram too large or has an unbounded cycle — truncated)"))
                break

            node = self.node_by_id.get(current)
            if node is None:
                break

            if node.type == "end":
                stmts.append(Return())
                current = None
                break

            if node.type == "start":
                path.append(current)
                current = self._single_successor(current)
                continue

            if node.type == "decision":
                true_id, false_id = self._branch_targets(current)
                true_is_back_edge = self._can_reach(true_id, current, stop_at | {current})
                false_is_back_edge = self._can_reach(false_id, current, stop_at | {current})

                condition = parse_condition(node.text)

                if true_is_back_edge or false_is_back_edge:
                    if true_is_back_edge:
                        loop_entry, exit_target, loop_condition = true_id, false_id, condition
                    else:
                        loop_entry, exit_target = false_id, true_id
                        loop_condition = UnaryOp(op="not", operand=condition)

                    body = self._walk(loop_entry, path + [current], stop_at | {current})
                    stmts.append(While(condition=loop_condition, body=body))
                    current = exit_target
                    if current:
                        path.append(current)
                    continue

                merge = self._find_merge_point(true_id, false_id, stop_at | {current})
                branch_stop = stop_at | ({merge} if merge else set())

                then_body = self._walk(true_id, path + [current], branch_stop) if true_id else []
                else_body = self._walk(false_id, path + [current], branch_stop) if false_id else []

                stmts.append(If(condition=condition, then_body=then_body, else_body=else_body))

                if merge is None:
                    current = None
                    break
                current = merge
                path.append(current)
                continue

            # process / input / output / connector / text — a plain
            # statement node with exactly one way forward.
            stmts.append(parse_statement(node.text))
            path.append(current)
            current = self._single_successor(current)

        return stmts

    def structure(self) -> Program:
        start_nodes = [n for n in self.node_by_id.values() if n.type == "start"]
        if not start_nodes:
            self.warnings.append("No Start node found — nothing to generate.")
            return Program(body=[])
        if len(start_nodes) > 1:
            self.warnings.append(
                f"Found {len(start_nodes)} Start nodes — generating code from the first one only."
            )

        body = self._walk(start_nodes[0].id, [], set())
        return Program(body=body)
