"""
Shared machinery for turning IR into source text. Each language emitter
subclasses `BaseEmitter`, overriding only the pieces that differ (variable
declaration syntax, input/output calls, program wrapper) while reusing the
default C-style block/if/while emission that most of the ten target
languages share.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.codegen.ir import (
    Assignment,
    BinOp,
    BoolLiteral,
    Break,
    Comment,
    Expr,
    Identifier,
    If,
    Input,
    NumberLiteral,
    Output,
    Program,
    RawExpr,
    Return,
    Stmt,
    StringLiteral,
    UnaryOp,
    While,
)

INDENT_UNIT = "    "

DEFAULT_OP_MAP = {
    "and": "&&",
    "or": "||",
    "not": "!",
    "+": "+", "-": "-", "*": "*", "/": "/", "%": "%", "//": "/",
    "<": "<", ">": ">", "<=": "<=", ">=": ">=", "==": "==", "!=": "!=",
}


class BaseEmitter(ABC):
    language_id: str
    file_extension: str
    op_map: dict[str, str] = DEFAULT_OP_MAP
    string_quote = '"'
    uses_braces = True
    statement_terminator = ";"
    program: Program | None = None

    def expr_type(self, expr: Expr) -> str:
        """Best-effort type lookup for an expression, using the inferred
        symbol table. Falls back to 'unknown' outside of assignment/typing
        context (e.g. no program set yet)."""
        from app.codegen.type_inference import infer_expr_type

        if self.program is None:
            return "unknown"
        return infer_expr_type(expr, self.program.variable_types)

    def emit_expr(self, expr: Expr) -> str:
        if isinstance(expr, NumberLiteral):
            if expr.is_float:
                return self._format_float(expr.value)
            return str(int(expr.value))
        if isinstance(expr, StringLiteral):
            escaped = expr.value.replace("\\", "\\\\").replace(self.string_quote, "\\" + self.string_quote)
            return f"{self.string_quote}{escaped}{self.string_quote}"
        if isinstance(expr, BoolLiteral):
            return self._format_bool(expr.value)
        if isinstance(expr, Identifier):
            return expr.name
        if isinstance(expr, UnaryOp):
            op = self.op_map.get(expr.op, expr.op)
            inner = self.emit_expr(expr.operand)
            if expr.op == "not":
                return f"{op}({inner})"
            return f"{op}{inner}"
        if isinstance(expr, BinOp):
            op = self.op_map.get(expr.op, expr.op)
            return f"({self.emit_expr(expr.left)} {op} {self.emit_expr(expr.right)})"
        if isinstance(expr, RawExpr):
            return expr.text
        return "/* unknown expression */"

    def _format_float(self, value: float) -> str:
        return repr(value)

    def _format_bool(self, value: bool) -> str:
        return "true" if value else "false"

    def emit_block(self, stmts: list[Stmt], indent: str) -> str:
        if not stmts:
            return ""
        return "\n".join(self.emit_stmt(s, indent) for s in stmts)

    def emit_stmt(self, stmt: Stmt, indent: str) -> str:
        if isinstance(stmt, Assignment):
            return self.emit_assignment(stmt, indent)
        if isinstance(stmt, Input):
            return self.emit_input(stmt, indent)
        if isinstance(stmt, Output):
            return self.emit_output(stmt, indent)
        if isinstance(stmt, Comment):
            return self.emit_comment(stmt, indent)
        if isinstance(stmt, If):
            return self.emit_if(stmt, indent)
        if isinstance(stmt, While):
            return self.emit_while(stmt, indent)
        if isinstance(stmt, Break):
            return f"{indent}break{self.statement_terminator}"
        if isinstance(stmt, Return):
            return self.emit_return(indent)
        return f"{indent}// unrecognized statement"

    def emit_comment(self, stmt: Comment, indent: str) -> str:
        return f"{indent}// {stmt.text}"

    def emit_return(self, indent: str) -> str:
        return f"{indent}return{self.statement_terminator}"

    def declared_type_of(self, name: str, program: Program) -> str:
        return program.variable_types.get(name, "unknown")

    def default_value_literal(self, generic_type: str) -> str:
        return {
            "int": "0",
            "float": "0.0",
            "string": f"{self.string_quote}{self.string_quote}",
            "bool": self._format_bool(False),
        }.get(generic_type, "0")

    @abstractmethod
    def emit_assignment(self, stmt: Assignment, indent: str) -> str: ...

    @abstractmethod
    def emit_input(self, stmt: Input, indent: str) -> str: ...

    @abstractmethod
    def emit_output(self, stmt: Output, indent: str) -> str: ...

    def emit_if(self, stmt: If, indent: str) -> str:
        header = f"{indent}if ({self.emit_expr(stmt.condition)}) {{"
        then_code = self.emit_block(stmt.then_body, indent + INDENT_UNIT)
        lines = [header, then_code, f"{indent}}}"]
        if stmt.else_body:
            else_code = self.emit_block(stmt.else_body, indent + INDENT_UNIT)
            lines = [header, then_code, f"{indent}}} else {{", else_code, f"{indent}}}"]
        return "\n".join(line for line in lines if line != "")

    def emit_while(self, stmt: While, indent: str) -> str:
        header = f"{indent}while ({self.emit_expr(stmt.condition)}) {{"
        body_code = self.emit_block(stmt.body, indent + INDENT_UNIT)
        return "\n".join(line for line in [header, body_code, f"{indent}}}"] if line != "")

    @abstractmethod
    def emit_program(self, program: Program) -> str: ...
