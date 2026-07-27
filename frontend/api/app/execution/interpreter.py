"""
Runs a flowchart for real: walks the node/edge graph starting at Start,
parses each node's text the same way Feature 2 does (reusing
pseudocode_parser so simulation and code generation never disagree on
what a shape means), evaluates expressions against a real variable
environment, and follows whichever branch the *actual runtime value* of
the condition selects — so loops genuinely repeat based on live state
rather than being statically unrolled.

This is deliberately simpler than graph_structurer.py: an interpreter
doesn't need to detect loops or find merge points the way code generation
does, because it isn't trying to produce nested if/while source text —
it just keeps following edges. That's what makes it a natural fit for
literally any graph the person drew, structured or not.

Scope: this executes the symbols this flowchart tool actually has —
sequences, decisions, loops via decision back-edges, input/output. There
is no subroutine/function-call shape in this app's symbol set, so
functions and recursion aren't part of what gets simulated; adding that
would mean adding a new node type first, not this module pretending to
support something that isn't drawable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.codegen.branch_resolution import resolve_branch
from app.codegen.graph_structurer import GraphEdge, GraphNode
from app.codegen.ir import Assignment, Comment, Input, Output
from app.codegen.pseudocode_parser import parse_condition, parse_statement
from app.execution.evaluator import EvalError, evaluate_expr

MAX_STEPS = 2000


@dataclass
class TraceStep:
    step_index: int
    node_id: str
    node_type: str
    label: str
    variables: dict[str, Any]
    output: str | None = None
    branch_taken: str | None = None


@dataclass
class ExecutionResult:
    steps: list[TraceStep] = field(default_factory=list)
    final_variables: dict[str, Any] = field(default_factory=dict)
    console_output: list[str] = field(default_factory=list)
    status: str = "completed"
    error_message: str | None = None
    error_node_id: str | None = None
    warnings: list[str] = field(default_factory=list)


class FlowchartInterpreter:
    def __init__(self, nodes: list[GraphNode], edges: list[GraphEdge], input_values: list[str] | None = None):
        self.node_by_id = {n.id: n for n in nodes}
        self._out_edges: dict[str, list[GraphEdge]] = {}
        for e in edges:
            self._out_edges.setdefault(e.from_id, []).append(e)
        self._input_queue = list(input_values or [])
        self._input_cursor = 0
        self.warnings: list[str] = []

    def _successors(self, node_id: str) -> list[GraphEdge]:
        return self._out_edges.get(node_id, [])

    def _next_input_value(self, target: str) -> Any:
        if self._input_cursor < len(self._input_queue):
            raw = self._input_queue[self._input_cursor]
            self._input_cursor += 1
            try:
                if "." in raw:
                    return float(raw)
                return int(raw)
            except ValueError:
                return raw
        self.warnings.append(
            f"No input value supplied for '{target}' — defaulted to 0. "
            "Provide values for every Input shape to simulate accurately."
        )
        return 0

    def run(self) -> ExecutionResult:
        env: dict[str, Any] = {}
        steps: list[TraceStep] = []
        console: list[str] = []

        start_nodes = [n for n in self.node_by_id.values() if n.type == "start"]
        if not start_nodes:
            return ExecutionResult(status="error", error_message="No Start shape found in this flowchart.")

        current: str | None = start_nodes[0].id
        step_index = 0

        while current is not None:
            step_index += 1
            if step_index > MAX_STEPS:
                return ExecutionResult(
                    steps=steps, final_variables=dict(env), console_output=console,
                    status="step_limit",
                    error_message=f"Stopped after {MAX_STEPS} steps — this looks like an infinite loop.",
                    warnings=self.warnings,
                )

            node = self.node_by_id.get(current)
            if node is None:
                break

            if node.type == "start":
                succs = self._successors(current)
                current = succs[0].to_id if succs else None
                continue

            if node.type == "end":
                steps.append(TraceStep(step_index, node.id, "end", "End", dict(env)))
                current = None
                break

            if node.type == "decision":
                condition = parse_condition(node.text)
                try:
                    result = evaluate_expr(condition, env)
                except EvalError as e:
                    return ExecutionResult(
                        steps=steps, final_variables=dict(env), console_output=console,
                        status="error", error_message=str(e), error_node_id=node.id,
                        warnings=self.warnings,
                    )

                true_edge, false_edge, branch_warnings = resolve_branch(node.id, self._successors(current))
                self.warnings.extend(w for w in branch_warnings if w not in self.warnings)

                truthy = bool(result)
                label = "Yes" if truthy else "No"
                steps.append(
                    TraceStep(
                        step_index, node.id, "decision",
                        f"{node.text.strip().rstrip('?')} → {truthy}",
                        dict(env), branch_taken=label,
                    )
                )
                chosen = true_edge if truthy else false_edge
                current = chosen.to_id if chosen else None
                continue

            stmt = parse_statement(node.text) if node.type != "connector" else Comment(text=node.text)

            if isinstance(stmt, Assignment):
                try:
                    value = evaluate_expr(stmt.value, env)
                except EvalError as e:
                    return ExecutionResult(
                        steps=steps, final_variables=dict(env), console_output=console,
                        status="error", error_message=str(e), error_node_id=node.id,
                        warnings=self.warnings,
                    )
                env[stmt.target] = value
                steps.append(TraceStep(step_index, node.id, node.type, f"{stmt.target} = {value!r}", dict(env)))

            elif isinstance(stmt, Input):
                value = self._next_input_value(stmt.target)
                env[stmt.target] = value
                steps.append(TraceStep(step_index, node.id, node.type, f"{stmt.target} = {value!r} (input)", dict(env)))

            elif isinstance(stmt, Output):
                try:
                    value = evaluate_expr(stmt.value, env)
                except EvalError as e:
                    return ExecutionResult(
                        steps=steps, final_variables=dict(env), console_output=console,
                        status="error", error_message=str(e), error_node_id=node.id,
                        warnings=self.warnings,
                    )
                text = str(value)
                console.append(text)
                steps.append(TraceStep(step_index, node.id, node.type, f"Print {text}", dict(env), output=text))

            else:
                steps.append(TraceStep(step_index, node.id, node.type, "(skipped — not executable)", dict(env)))

            succs = self._successors(current)
            current = succs[0].to_id if succs else None

        return ExecutionResult(
            steps=steps, final_variables=dict(env), console_output=console,
            status="completed", warnings=self.warnings,
        )
