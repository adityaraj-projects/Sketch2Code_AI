from __future__ import annotations

from app.codegen.emitters.base import INDENT_UNIT, BaseEmitter
from app.codegen.ir import Assignment, Expr, Identifier, If, Input, Output, Program, While


class PhpEmitter(BaseEmitter):
    language_id = "php"
    file_extension = "php"

    def emit_expr(self, expr: Expr) -> str:
        if isinstance(expr, Identifier):
            return f"${expr.name}"
        return super().emit_expr(expr)

    def emit_assignment(self, stmt: Assignment, indent: str) -> str:
        return f"{indent}${stmt.target} = {self.emit_expr(stmt.value)};"

    def emit_input(self, stmt: Input, indent: str) -> str:
        lines = []
        if stmt.prompt:
            lines.append(f'{indent}echo "{stmt.prompt}: ";')
        target_type = self.program.variable_types.get(stmt.target, "int") if self.program else "int"
        cast = {"float": "(float)", "int": "(int)"}.get(target_type, "(int)")
        lines.append(f"{indent}${stmt.target} = {cast}trim(fgets(STDIN));")
        return "\n".join(lines)

    def emit_output(self, stmt: Output, indent: str) -> str:
        return f'{indent}echo {self.emit_expr(stmt.value)} . "\\n";'

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

    def emit_program(self, program: Program) -> str:
        self.program = program
        decl_lines = [
            f"{INDENT_UNIT}${name} = {self.default_value_literal(t)};"
            for name, t in program.variable_types.items()
        ]
        body = self.emit_block(program.body, INDENT_UNIT)
        parts = ["<?php\n", "function main() {"]
        if decl_lines:
            parts.append("\n".join(decl_lines))
        if body:
            parts.append(body)
        parts.append("}")
        return "\n".join(p for p in parts if p != "") + "\n\nmain();\n"
