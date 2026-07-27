"""
Turns the free text a person writes inside a flowchart shape into an IR
statement (for process/input/output nodes) or a condition expression (for
decision nodes). Recognizes the vocabulary people actually write in
flowchart pseudocode — "Read x", "Print total", "x = x + 1" — and falls
back to an honest Comment/RawExpr rather than guessing when it doesn't.
"""
from __future__ import annotations

import re

from app.codegen.expression_parser import parse_expression
from app.codegen.ir import Assignment, Comment, Input, Output, Stmt

_INPUT_RE = re.compile(r"^\s*(read|input|get|scan|enter)\b[:\-]?\s*(.+)$", re.IGNORECASE)
_INPUT_WITH_QUOTED_PROMPT_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*"(.*)"\s*\)$')
_OUTPUT_RE = re.compile(r"^\s*(print|output|display|show|write|println)\b[:\-]?\s*(.+)$", re.IGNORECASE)
_ASSIGNMENT_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:=|←|:=)(?!=)\s*(.+)$")
_BARE_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def parse_statement(text: str) -> Stmt:
    text = text.strip()
    if not text:
        return Comment(text="(empty)")

    m = _INPUT_RE.match(text)
    if m:
        rest = m.group(2).strip()
        # This tool's own display format for "target with a prompt" —
        # e.g. 'n ("Enter a number")' — must parse back exactly, since
        # the execution simulator re-parses node text on every run.
        quoted_match = _INPUT_WITH_QUOTED_PROMPT_RE.match(rest)
        if quoted_match:
            return Input(target=quoted_match.group(1), prompt=quoted_match.group(2))
        if _BARE_IDENTIFIER_RE.match(rest):
            return Input(target=rest)
        tokens = rest.split()
        if tokens and _BARE_IDENTIFIER_RE.match(tokens[-1]):
            target = tokens[-1]
            prompt_text = rest[: -len(target)].strip().strip('"\'') or None
            return Input(target=target, prompt=prompt_text)
        return Input(target="value", prompt=rest.strip('"\''))

    m = _OUTPUT_RE.match(text)
    if m:
        return Output(value=parse_expression(m.group(2).strip()))

    m = _ASSIGNMENT_RE.match(text)
    if m:
        return Assignment(target=m.group(1), value=parse_expression(m.group(2).strip()))

    return Comment(text=text)


def parse_condition(text: str):
    text = text.strip()
    if text.endswith("?"):
        text = text[:-1].strip()
    return parse_expression(text)
