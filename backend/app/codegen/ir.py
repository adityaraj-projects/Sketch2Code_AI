"""
Intermediate representation for generated programs.

The graph structurer turns a flowchart's nodes/edges into this IR; each
language emitter turns this same IR into source code. Keeping one shared
IR is what makes adding an 11th target language later a matter of writing
one new emitter file, not touching the graph logic at all.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------

class Expr:
    pass


@dataclass
class NumberLiteral(Expr):
    value: float
    is_float: bool


@dataclass
class StringLiteral(Expr):
    value: str


@dataclass
class BoolLiteral(Expr):
    value: bool


@dataclass
class Identifier(Expr):
    name: str


@dataclass
class UnaryOp(Expr):
    op: str  # "-" | "not"
    operand: Expr


@dataclass
class BinOp(Expr):
    op: str  # "+" "-" "*" "/" "%" "<" ">" "<=" ">=" "==" "!=" "and" "or"
    left: Expr
    right: Expr


@dataclass
class RawExpr(Expr):
    """Fallback for text we couldn't confidently parse — emitted verbatim
    (as a best-effort identifier/expression) rather than dropped, so the
    generated code stays a faithful reflection of what was drawn."""
    text: str


# ---------------------------------------------------------------------------
# Statements
# ---------------------------------------------------------------------------

class Stmt:
    pass


@dataclass
class Assignment(Stmt):
    target: str
    value: Expr


@dataclass
class Input(Stmt):
    target: str
    prompt: str | None = None


@dataclass
class Output(Stmt):
    value: Expr


@dataclass
class Comment(Stmt):
    text: str


@dataclass
class If(Stmt):
    condition: Expr
    then_body: list[Stmt]
    else_body: list[Stmt] = field(default_factory=list)


@dataclass
class While(Stmt):
    condition: Expr
    body: list[Stmt]


@dataclass
class Break(Stmt):
    pass


@dataclass
class Return(Stmt):
    pass


@dataclass
class Program:
    body: list[Stmt]
    # name -> inferred type: "int" | "float" | "string" | "bool" | "unknown"
    variable_types: dict[str, str] = field(default_factory=dict)
