from __future__ import annotations

from app.codegen.ir import (
    Assignment,
    BinOp,
    BoolLiteral,
    Comment,
    Expr,
    Identifier,
    Input,
    NumberLiteral,
    Output,
    RawExpr,
    Stmt,
    StringLiteral,
    UnaryOp,
)


def expr_to_text(expr: Expr) -> str:
    if isinstance(expr, NumberLiteral):
        return str(int(expr.value)) if not expr.is_float else str(expr.value)
    if isinstance(expr, StringLiteral):
        return f'"{expr.value}"'
    if isinstance(expr, BoolLiteral):
        return "true" if expr.value else "false"
    if isinstance(expr, Identifier):
        return expr.name
    if isinstance(expr, UnaryOp):
        inner = expr_to_text(expr.operand)
        return f"not {inner}" if expr.op == "not" else f"-{inner}"
    if isinstance(expr, BinOp):
        return f"{expr_to_text(expr.left)} {expr.op} {expr_to_text(expr.right)}"
    if isinstance(expr, RawExpr):
        return expr.text
    return "?"


def condition_to_text(expr: Expr) -> str:
    return expr_to_text(expr)


def statement_to_label(stmt: Stmt) -> str:
    if isinstance(stmt, Assignment):
        return f"{stmt.target} = {expr_to_text(stmt.value)}"
    if isinstance(stmt, Input):
        if stmt.prompt:
            return f'Read {stmt.target} ("{stmt.prompt}")'
        return f"Read {stmt.target}"
    if isinstance(stmt, Output):
        return f"Print {expr_to_text(stmt.value)}"
    if isinstance(stmt, Comment):
        return stmt.text
    return "?"
