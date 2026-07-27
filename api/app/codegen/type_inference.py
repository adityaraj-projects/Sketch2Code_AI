"""
Statically-typed target languages (Java, C, C++, C#, Go, Rust) need a
declared type for every variable. Flowchart pseudocode never states one
explicitly, so this does a single forward pass over the structured
program, inferring each variable's type from how it's first assigned —
numeric literal without a decimal point -> int, with one -> float, quoted
text -> string, true/false -> bool, arithmetic between known types ->
the widened result type. A variable used inconsistently (e.g. assigned a
number in one branch and text in another) is marked "unknown" rather than
silently picked one way, and the emitters fall back to each language's
loosest reasonable type (e.g. `var`/`auto`/no annotation) for those.
"""
from __future__ import annotations

from app.codegen.ir import (
    Assignment,
    BinOp,
    BoolLiteral,
    Expr,
    Identifier,
    If,
    Input,
    NumberLiteral,
    Output,
    Program,
    RawExpr,
    Stmt,
    StringLiteral,
    UnaryOp,
    While,
)

COMPARISON_OPS = {"<", ">", "<=", ">=", "==", "!="}
LOGICAL_OPS = {"and", "or"}
_TYPE_RANK = {"unknown": 0, "bool": 1, "int": 2, "float": 3, "string": 4}


def _widen(a: str, b: str) -> str:
    if a == b:
        return a
    if "unknown" in (a, b):
        return "unknown"
    if "string" in (a, b):
        return "string" if (a == "string" or b == "string") else "unknown"
    return max(a, b, key=lambda t: _TYPE_RANK.get(t, 0))


def infer_expr_type(expr: Expr, symtab: dict[str, str]) -> str:
    if isinstance(expr, NumberLiteral):
        return "float" if expr.is_float else "int"
    if isinstance(expr, StringLiteral):
        return "string"
    if isinstance(expr, BoolLiteral):
        return "bool"
    if isinstance(expr, Identifier):
        return symtab.get(expr.name, "unknown")
    if isinstance(expr, UnaryOp):
        if expr.op == "not":
            return "bool"
        return infer_expr_type(expr.operand, symtab)
    if isinstance(expr, BinOp):
        if expr.op in COMPARISON_OPS or expr.op in LOGICAL_OPS:
            return "bool"
        left_t = infer_expr_type(expr.left, symtab)
        right_t = infer_expr_type(expr.right, symtab)
        return _widen(left_t, right_t)
    if isinstance(expr, RawExpr):
        return "unknown"
    return "unknown"


def _visit_statements(stmts: list[Stmt], symtab: dict[str, str]) -> None:
    for stmt in stmts:
        if isinstance(stmt, Assignment):
            inferred = infer_expr_type(stmt.value, symtab)
            if stmt.target in symtab:
                symtab[stmt.target] = _widen(symtab[stmt.target], inferred)
            else:
                symtab[stmt.target] = inferred
        elif isinstance(stmt, Input):
            if stmt.target not in symtab:
                symtab[stmt.target] = "int"
        elif isinstance(stmt, Output):
            infer_expr_type(stmt.value, symtab)
        elif isinstance(stmt, If):
            _visit_statements(stmt.then_body, symtab)
            _visit_statements(stmt.else_body, symtab)
        elif isinstance(stmt, While):
            _visit_statements(stmt.body, symtab)


def infer_types(program: Program) -> Program:
    symtab: dict[str, str] = {}
    _visit_statements(program.body, symtab)
    program.variable_types = symtab
    return program
