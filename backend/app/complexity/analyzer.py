"""
Estimates time and space complexity from the same structured IR that
Feature 2's code generator and Feature 5's explainer use. This is genuine
static analysis, not an AI guess: nested-loop depth becomes polynomial
degree, a loop whose control variable changes multiplicatively each
iteration (i = i * 2, i = i / 2) becomes a logarithmic factor, and
sequential blocks combine by taking the dominant (max) term, the same way
a person would reason about Big-O by eye.

This is deliberately honest about its limits: determining exact runtime
behavior of arbitrary code is undecidable in general, so when a loop's
growth pattern doesn't match a recognizable shape, it's reported as an
estimate rather than asserted with false confidence.

Space complexity: this flowchart tool has no array/list/recursion
support in its symbol set (Feature 1's shapes are Start/End/Process/
Decision/Input/Output/Connector), so any diagram it can represent only
ever uses a fixed number of scalar variables — auxiliary space is
always O(1). That's stated as a fact about this tool's scope, not
computed per-diagram.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.codegen.ir import Assignment, BinOp, Identifier, If, NumberLiteral, Program, Stmt, While
from app.codetoflow.ir_to_text import condition_to_text
from app.complexity.ir_queries import collect_assignment_targets, expr_identifiers, find_variable_update

Degree = tuple[int, int]  # (polynomial degree of n, count of log-n factors)


@dataclass
class ComplexityResult:
    time_complexity: str
    space_complexity: str
    reasoning: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    confidence: str = "high"


def _format_degree(degree: Degree) -> str:
    poly, log = degree
    parts: list[str] = []
    if poly == 1:
        parts.append("n")
    elif poly > 1:
        parts.append(f"n^{poly}")
    if log == 1:
        parts.append("log n")
    elif log > 1:
        parts.append(f"(log n)^{log}")
    if not parts:
        return "O(1)"
    return "O(" + " · ".join(parts) + ")"


def _detect_loop_growth(stmt: While) -> tuple[str | None, str]:
    """Returns (control_variable, growth) where growth is
    'linear' | 'logarithmic' | 'unknown'."""
    candidates = expr_identifiers(stmt.condition)
    for var in candidates:
        update = find_variable_update(stmt.body, var)
        if update is None:
            continue
        value = update.value
        if isinstance(value, BinOp):
            operands = [value.left, value.right]
            is_self_and_const = any(
                isinstance(o, Identifier) and o.name == var for o in operands
            ) and any(isinstance(o, NumberLiteral) for o in operands)
            if is_self_and_const:
                if value.op in ("+", "-"):
                    return var, "linear"
                if value.op in ("*", "/", "//"):
                    const = next((o for o in operands if isinstance(o, NumberLiteral)), None)
                    if const is not None and const.value not in (0, 1):
                        return var, "logarithmic"
    return None, "unknown"


class ComplexityAnalyzer:
    def __init__(self):
        self.suggestions: list[str] = []
        self.low_confidence = False

    def _analyze_block(self, stmts: list[Stmt]) -> tuple[Degree, list[str]]:
        best: Degree = (0, 0)
        reasoning: list[str] = []

        for stmt in stmts:
            if isinstance(stmt, While):
                degree, stmt_reasoning = self._analyze_while(stmt)
                reasoning.extend(stmt_reasoning)
                best = max(best, degree)

            elif isinstance(stmt, If):
                then_degree, then_reasoning = self._analyze_block(stmt.then_body)
                else_degree, else_reasoning = self._analyze_block(stmt.else_body)
                reasoning.extend(then_reasoning)
                reasoning.extend(else_reasoning)
                best = max(best, then_degree, else_degree)

        return best, reasoning

    def _analyze_while(self, stmt: While) -> tuple[Degree, list[str]]:
        var, growth = _detect_loop_growth(stmt)
        body_degree, body_reasoning = self._analyze_block(stmt.body)
        cond_text = condition_to_text(stmt.condition)

        if growth == "linear":
            this_degree: Degree = (body_degree[0] + 1, body_degree[1])
            reasoning = [f"Loop '{cond_text}' — '{var}' moves toward the limit by a fixed amount each time, so it runs proportional to n."]
        elif growth == "logarithmic":
            this_degree = (body_degree[0], body_degree[1] + 1)
            reasoning = [f"Loop '{cond_text}' — '{var}' changes multiplicatively each iteration, so it runs about log n times."]
        else:
            this_degree = (body_degree[0] + 1, body_degree[1])
            reasoning = [f"Loop '{cond_text}' — couldn't tell exactly how the loop variable changes, assuming a normal linear scan (O(n))."]
            self.low_confidence = True

        reasoning.extend(body_reasoning)

        changed_in_loop = collect_assignment_targets(stmt.body)
        for inner in stmt.body:
            if isinstance(inner, Assignment) and inner.target != var:
                deps = expr_identifiers(inner.value)
                if deps and not (deps & changed_in_loop):
                    self.suggestions.append(
                        f"'{inner.target} = {condition_to_text(inner.value)}' inside the loop '{cond_text}' "
                        "doesn't depend on anything the loop changes — computing it once before the loop "
                        "would avoid redoing it every iteration."
                    )

        return max(this_degree, body_degree), reasoning

    def analyze(self, program: Program) -> ComplexityResult:
        degree, reasoning = self._analyze_block(program.body)

        if degree[0] >= 2:
            self.suggestions.append(
                f"This has nested loops totaling {_format_degree(degree)}. If they're scanning for pairs, "
                "duplicates, or matches, a hash set/map often reduces this to a single O(n) pass."
            )

        if not reasoning:
            reasoning = ["No loops were found, so this runs in constant time relative to its inputs."]

        return ComplexityResult(
            time_complexity=_format_degree(degree),
            space_complexity="O(1)",
            reasoning=reasoning,
            suggestions=self.suggestions,
            confidence="estimated" if self.low_confidence else "high",
        )


def analyze_complexity(program: Program) -> ComplexityResult:
    return ComplexityAnalyzer().analyze(program)
