"""
Turns the structured program (built by the same GraphStructurer that
powers Feature 2's code generation) into clean, language-neutral
pseudocode. This is what actually gets handed to the LLM as context — the
model is asked to explain this already-correct structure in natural
language, not to infer control flow from a raw node/edge list itself.
Keeping the deterministic, tested graph_structurer in charge of "what the
algorithm actually does" and only asking the LLM to write the prose is
what keeps this feature honest.
"""
from __future__ import annotations

from app.codegen.ir import Assignment, Break, Comment, If, Input, Output, Program, Return, Stmt, While
from app.codetoflow.ir_to_text import condition_to_text, statement_to_label

INDENT = "    "


def _render_block(stmts: list[Stmt], indent: str, lines: list[str]) -> None:
    if not stmts:
        lines.append(f"{indent}(nothing)")
        return
    for stmt in stmts:
        if isinstance(stmt, If):
            lines.append(f"{indent}if {condition_to_text(stmt.condition)}:")
            _render_block(stmt.then_body, indent + INDENT, lines)
            if stmt.else_body:
                lines.append(f"{indent}else:")
                _render_block(stmt.else_body, indent + INDENT, lines)
        elif isinstance(stmt, While):
            lines.append(f"{indent}while {condition_to_text(stmt.condition)}:")
            _render_block(stmt.body, indent + INDENT, lines)
        elif isinstance(stmt, Break):
            lines.append(f"{indent}break")
        elif isinstance(stmt, Return):
            lines.append(f"{indent}return")
        elif isinstance(stmt, (Assignment, Input, Output, Comment)):
            lines.append(f"{indent}{statement_to_label(stmt)}")
        else:
            lines.append(f"{indent}?")


def program_to_pseudocode(program: Program) -> str:
    lines: list[str] = []
    _render_block(program.body, "", lines)
    return "\n".join(lines)
