from __future__ import annotations

from app.codegen.ir import (
    Assignment,
    BinOp,
    Expr,
    Identifier,
    If,
    Input,
    Output,
    Stmt,
    UnaryOp,
    While,
)


def expr_identifiers(expr: Expr) -> set[str]:
    if isinstance(expr, Identifier):
        return {expr.name}
    if isinstance(expr, UnaryOp):
        return expr_identifiers(expr.operand)
    if isinstance(expr, BinOp):
        return expr_identifiers(expr.left) | expr_identifiers(expr.right)
    return set()


def collect_assignment_targets(stmts: list[Stmt]) -> set[str]:
    targets: set[str] = set()
    for stmt in stmts:
        if isinstance(stmt, Assignment):
            targets.add(stmt.target)
        elif isinstance(stmt, Input):
            targets.add(stmt.target)
        elif isinstance(stmt, If):
            targets |= collect_assignment_targets(stmt.then_body)
            targets |= collect_assignment_targets(stmt.else_body)
        elif isinstance(stmt, While):
            targets |= collect_assignment_targets(stmt.body)
    return targets


def find_variable_update(stmts: list[Stmt], var: str) -> Assignment | None:
    for stmt in stmts:
        if isinstance(stmt, Assignment) and stmt.target == var:
            return stmt
        if isinstance(stmt, If):
            found = find_variable_update(stmt.then_body, var) or find_variable_update(stmt.else_body, var)
            if found:
                return found
        if isinstance(stmt, While):
            found = find_variable_update(stmt.body, var)
            if found:
                return found
    return None
