"""
Parses the free-form text a person writes inside a flowchart shape (e.g.
"x = x + 1", "n > 0 and n < 100", "\"Enter a number\"") into the Expr AST
from ir.py. This is a real operator-precedence (Pratt) parser — not a
lookup table — so it correctly handles nesting, precedence, and
parentheses.
"""
from __future__ import annotations

import re

from app.codegen.ir import BinOp, BoolLiteral, Expr, Identifier, NumberLiteral, RawExpr, StringLiteral, UnaryOp

TOKEN_PATTERN = re.compile(
    r"""
    \s*(?:
        (?P<STRING>"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')
      | (?P<NUMBER>\d+\.\d+|\d+)
      | (?P<OP>//|<=|>=|==|!=|&&|\|\||[+\-*/%<>()=])
      | (?P<WORD>[A-Za-z_][A-Za-z0-9_]*)
    )
    """,
    re.VERBOSE,
)

WORD_OPERATORS = {"and": "and", "or": "or", "not": "not", "mod": "%"}
BOOL_WORDS = {"true": True, "false": False}

# Binding power: higher binds tighter.
PRECEDENCE = {
    "or": 1,
    "and": 2,
    "==": 3, "!=": 3,
    "<": 4, ">": 4, "<=": 4, ">=": 4,
    "+": 5, "-": 5,
    "*": 6, "/": 6, "%": 6, "//": 6,
}


class ParseError(Exception):
    pass


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    pos = 0
    while pos < len(text):
        m = TOKEN_PATTERN.match(text, pos)
        if not m or m.end() == pos:
            if text[pos].isspace():
                pos += 1
                continue
            raise ParseError(f"Unrecognized character '{text[pos]}' at position {pos}")
        token = next(v for v in m.groupdict().values() if v is not None)
        tokens.append(token)
        pos = m.end()
    return tokens


class _Parser:
    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def advance(self) -> str:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def normalized_peek(self) -> str | None:
        tok = self.peek()
        if tok is None:
            return None
        low = tok.lower()
        if low in WORD_OPERATORS:
            return WORD_OPERATORS[low]
        if low == "&&":
            return "and"
        if low == "||":
            return "or"
        return tok

    def parse_expression(self, min_bp: int = 0) -> Expr:
        left = self.parse_unary()

        while True:
            op = self.normalized_peek()
            if op is None or op not in PRECEDENCE:
                break
            bp = PRECEDENCE[op]
            if bp < min_bp:
                break
            self.advance()
            right = self.parse_expression(bp + 1)
            left = BinOp(op=op, left=left, right=right)

        return left

    def parse_unary(self) -> Expr:
        tok = self.peek()
        if tok is None:
            raise ParseError("Unexpected end of expression")

        low = tok.lower()
        if tok == "-" :
            self.advance()
            return UnaryOp(op="-", operand=self.parse_unary())
        if low == "not" or tok == "!":
            self.advance()
            return UnaryOp(op="not", operand=self.parse_unary())

        return self.parse_primary()

    def parse_primary(self) -> Expr:
        tok = self.advance()

        if tok == "(":
            expr = self.parse_expression()
            if self.peek() != ")":
                raise ParseError("Expected closing ')'")
            self.advance()
            return expr

        if tok[0] in ("'", '"'):
            return StringLiteral(value=tok[1:-1])

        if re.fullmatch(r"\d+\.\d+|\d+", tok):
            is_float = "." in tok
            return NumberLiteral(value=float(tok), is_float=is_float)

        low = tok.lower()
        if low in BOOL_WORDS:
            return BoolLiteral(value=BOOL_WORDS[low])

        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", tok):
            return Identifier(name=tok)

        raise ParseError(f"Unexpected token '{tok}'")


def parse_expression(text: str) -> Expr:
    text = text.strip()
    try:
        tokens = tokenize(text)
        if not tokens:
            return RawExpr(text=text)
        parser = _Parser(tokens)
        expr = parser.parse_expression()
        if parser.pos != len(tokens):
            # Trailing tokens we couldn't fold in — safer to fall back to
            # the raw text than to silently drop part of what was written.
            return RawExpr(text=text)
        return expr
    except ParseError:
        return RawExpr(text=text)
