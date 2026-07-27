"""
The inverse of graph_structurer.py: takes structured IR (If/While/
Assignment/...) and lays it out as an actual flowchart — computing x/y
positions for each shape and the edges between them, including loop
back-edges and if/else branches that diverge and remerge. This is a real,
if intentionally simple, automatic graph-layout algorithm (a single-pass
layered layout specialized for flowcharts), not a static template.

Layout conventions, matching how people draw these by hand:
- The main sequence runs straight down a center line.
- An if/else's "then" branch is offset to the right, "else" to the left;
  both branches' dangling ends reconverge into whatever node comes next.
- A while loop's body is offset to the right below the decision; each
  path through the body that doesn't dead-end loops back up to the
  decision node itself.
- `break` and early `return` are honest dead ends in the diagram (no
  attempt to route a break forward to "wherever the enclosing loop
  exits" — that requires two-pass layout and isn't worth the complexity
  it would add for what's usually a rare case in flowchart-style code).

Every statement sequence is laid out with a real list of "incoming" exit
points from its actual predecessor (the Start node, a decision's branch
side, a loop's body entry) — there is no placeholder/dummy entry point;
an earlier version of this file had one, which silently dropped the edge
into the first node of every branch.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.codegen.ir import Assignment, Break, Comment, If, Input, Output, Program, Return, Stmt, While
from app.codetoflow.ir_to_text import condition_to_text, statement_to_label

NODE_SIZES = {
    "start": (140, 64),
    "end": (140, 64),
    "process": (160, 72),
    "decision": (170, 100),
    "input": (170, 72),
}
V_GAP = 50
BRANCH_DX = 230
CENTER_X = 500


@dataclass
class ExitPoint:
    node_id: str
    x: float
    y: float
    label: str | None = None


@dataclass
class LayoutResult:
    exits: list[ExitPoint]
    bottom_y: float


@dataclass
class LaidOutNode:
    id: str
    type: str
    x: float
    y: float
    width: float
    height: float
    text: str


@dataclass
class LaidOutEdge:
    id: str
    from_id: str
    to_id: str
    from_point: tuple[float, float]
    to_point: tuple[float, float]
    label: str | None = None


class FlowchartLayout:
    def __init__(self):
        self.nodes: list[LaidOutNode] = []
        self.edges: list[LaidOutEdge] = []
        self.warnings: list[str] = []

    def _new_id(self) -> str:
        return uuid.uuid4().hex[:12]

    def _add_node(self, node_type: str, cx: float, top_y: float, text: str) -> LaidOutNode:
        w, h = NODE_SIZES[node_type]
        node = LaidOutNode(id=self._new_id(), type=node_type, x=cx - w / 2, y=top_y, width=w, height=h, text=text)
        self.nodes.append(node)
        return node

    def _exit_bottom(self, node: LaidOutNode, label: str | None = None) -> ExitPoint:
        return ExitPoint(node_id=node.id, x=node.x + node.width / 2, y=node.y + node.height, label=label)

    def _land(self, incoming: list[ExitPoint], node: LaidOutNode) -> None:
        to_top_center = (node.x + node.width / 2, node.y)
        for e in incoming:
            self.edges.append(
                LaidOutEdge(
                    id=self._new_id(),
                    from_id=e.node_id,
                    to_id=node.id,
                    from_point=(e.x, e.y),
                    to_point=to_top_center,
                    label=e.label,
                )
            )

    def layout_block(self, stmts: list[Stmt], cx: float, top_y: float, incoming: list[ExitPoint]) -> LayoutResult:
        exits = incoming
        current_y = top_y

        for i, stmt in enumerate(stmts):
            if isinstance(stmt, (Assignment, Comment)):
                node = self._add_node("process", cx, current_y, statement_to_label(stmt))
                self._land(exits, node)
                exits = [self._exit_bottom(node)]
                current_y = node.y + node.height + V_GAP

            elif isinstance(stmt, (Input, Output)):
                node = self._add_node("input", cx, current_y, statement_to_label(stmt))
                self._land(exits, node)
                exits = [self._exit_bottom(node)]
                current_y = node.y + node.height + V_GAP

            elif isinstance(stmt, If):
                result = self._layout_if(stmt, cx, current_y, exits)
                exits = result.exits
                current_y = result.bottom_y

            elif isinstance(stmt, While):
                result = self._layout_while(stmt, cx, current_y, exits)
                exits = result.exits
                current_y = result.bottom_y

            elif isinstance(stmt, Return):
                node = self._add_node("end", cx, current_y, "End")
                self._land(exits, node)
                exits = []
                current_y = node.y + node.height + V_GAP

            elif isinstance(stmt, Break):
                node = self._add_node("process", cx, current_y, "break")
                self._land(exits, node)
                exits = []
                current_y = node.y + node.height + V_GAP
                self.warnings.append(
                    "A 'break' was drawn as a dead-end box rather than routed to after its loop."
                )

            if not exits and i != len(stmts) - 1:
                self.warnings.append("Unreachable code after a return/break was skipped in the diagram.")
                break

        return LayoutResult(exits=exits, bottom_y=current_y)

    def _layout_if(self, stmt: If, cx: float, top_y: float, incoming: list[ExitPoint]) -> LayoutResult:
        decision = self._add_node("decision", cx, top_y, condition_to_text(stmt.condition))
        self._land(incoming, decision)

        branch_top = decision.y + decision.height + V_GAP
        then_cx = cx + BRANCH_DX if stmt.else_body else cx
        then_entry = ExitPoint(
            node_id=decision.id,
            x=decision.x + decision.width if stmt.else_body else decision.x + decision.width / 2,
            y=decision.y + decision.height / 2 if stmt.else_body else decision.y + decision.height,
            label="Yes",
        )
        then_result = self.layout_block(stmt.then_body, then_cx, branch_top, [then_entry])

        if stmt.else_body:
            else_entry = ExitPoint(
                node_id=decision.id, x=decision.x, y=decision.y + decision.height / 2, label="No"
            )
            else_result = self.layout_block(stmt.else_body, cx - BRANCH_DX, branch_top, [else_entry])
            combined_exits = then_result.exits + else_result.exits
            bottom_y = max(then_result.bottom_y, else_result.bottom_y)
        else:
            direct_exit = ExitPoint(
                node_id=decision.id,
                x=decision.x + decision.width / 2,
                y=decision.y + decision.height,
                label="No",
            )
            combined_exits = then_result.exits + [direct_exit]
            bottom_y = max(then_result.bottom_y, branch_top)

        return LayoutResult(exits=combined_exits, bottom_y=bottom_y)

    def _layout_while(self, stmt: While, cx: float, top_y: float, incoming: list[ExitPoint]) -> LayoutResult:
        decision = self._add_node("decision", cx, top_y, condition_to_text(stmt.condition))
        self._land(incoming, decision)

        body_top = decision.y + decision.height + V_GAP
        body_cx = cx + BRANCH_DX
        body_entry = ExitPoint(
            node_id=decision.id, x=decision.x + decision.width, y=decision.y + decision.height / 2, label="Yes"
        )
        body_result = self.layout_block(stmt.body, body_cx, body_top, [body_entry])

        for exit_point in body_result.exits:
            self.edges.append(
                LaidOutEdge(
                    id=self._new_id(),
                    from_id=exit_point.node_id,
                    to_id=decision.id,
                    from_point=(exit_point.x, exit_point.y),
                    to_point=(decision.x + decision.width, decision.y + decision.height / 2),
                    label=None,
                )
            )

        exit_below = ExitPoint(
            node_id=decision.id,
            x=decision.x + decision.width / 2,
            y=decision.y + decision.height,
            label="No",
        )
        bottom_y = max(body_result.bottom_y, body_top)
        return LayoutResult(exits=[exit_below], bottom_y=bottom_y)

    def build(self, program: Program) -> tuple[list[LaidOutNode], list[LaidOutEdge], list[str]]:
        start = self._add_node("start", CENTER_X, 40, "Start")
        result = self.layout_block(
            program.body, CENTER_X, start.y + start.height + V_GAP, [self._exit_bottom(start)]
        )

        if result.exits:
            end = self._add_node("end", CENTER_X, result.bottom_y, "End")
            self._land(result.exits, end)

        return self.nodes, self.edges, self.warnings
