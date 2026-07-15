"""
Actually evaluates an IR expression against a variable environment, with
real runtime semantics: division by zero raises, using a variable before
it's ever been assigned raises (the simulator is supposed to catch these
bugs for the student, not paper over them with a silent default), and
`and`/`or` short-circuit like a real language instead of eagerly
evaluating both sides.
"""
from __future__ import annotations

from typing import Any

from app.codegen.ir import BinOp, BoolLiteral, Expr, Identifier, NumberLiteral, RawExpr, StringLiteral, UnaryOp

Env = dict[str, Any]


class EvalError(Exception):
    pass


def evaluate_expr(expr: Expr, env: Env) -> Any:
    if isinstance(expr, NumberLiteral):
        return float(expr.value) if expr.is_float else int(expr.value)

    if isinstance(expr, StringLiteral):
        return expr.value

    if isinstance(expr, BoolLiteral):
        return expr.value

    if isinstance(expr, Identifier):
        if expr.name not in env:
            raise EvalError(f"'{expr.name}' is used here before it has a value")
        return env[expr.name]

    if isinstance(expr, UnaryOp):
        value = evaluate_expr(expr.operand, env)
        if expr.op == "-":
            _require_numeric(value, "-")
            return -value
        if expr.op == "not":
            return not _truthy(value)
        raise EvalError(f"Unknown unary operator '{expr.op}'")

    if isinstance(expr, BinOp):
        if expr.op == "and":
            left = evaluate_expr(expr.left, env)
            if not _truthy(left):
                return False
            return _truthy(evaluate_expr(expr.right, env))
        if expr.op == "or":
            left = evaluate_expr(expr.left, env)
            if _truthy(left):
                return True
            return _truthy(evaluate_expr(expr.right, env))

        left = evaluate_expr(expr.left, env)
        right = evaluate_expr(expr.right, env)
        return _apply_binary(expr.op, left, right)

    if isinstance(expr, RawExpr):
        raise EvalError(f"Couldn't evaluate the expression '{expr.text}' — try rewriting it more simply")

    raise EvalError("Unknown expression type")


def _truthy(value: Any) -> bool:
    return bool(value)


def _require_numeric(value: Any, op: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise EvalError(f"Can't apply '{op}' to {value!r} — expected a number")


def _apply_binary(op: str, left: Any, right: Any) -> Any:
    if op == "+":
        if isinstance(left, str) or isinstance(right, str):
            return f"{_display(left)}{_display(right)}"
        _require_numeric(left, "+")
        _require_numeric(right, "+")
        return left + right

    if op in ("-", "*", "/", "%", "//"):
        _require_numeric(left, op)
        _require_numeric(right, op)
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            if right == 0:
                raise EvalError("Division by zero")
            return left / right
        if op == "%":
            if right == 0:
                raise EvalError("Division by zero (modulo)")
            return left % right
        if op == "//":
            if right == 0:
                raise EvalError("Division by zero")
            return left // right

    if op in ("<", ">", "<=", ">=", "==", "!="):
        try:
            if op == "<":
                return left < right
            if op == ">":
                return left > right
            if op == "<=":
                return left <= right
            if op == ">=":
                return left >= right
            if op == "==":
                return left == right
            if op == "!=":
                return left != right
        except TypeError as e:
            raise EvalError(f"Can't compare {left!r} and {right!r}") from e

    raise EvalError(f"Unknown operator '{op}'")


def _display(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)
