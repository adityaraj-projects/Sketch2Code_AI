from __future__ import annotations

from app.codegen.emitters.base import INDENT_UNIT, BaseEmitter
from app.codegen.ir import Assignment, Input, Output, Program, RawExpr, StringLiteral

C_TYPES = {"int": "int", "float": "double", "string": "char*", "bool": "int", "unknown": "int"}


class CEmitter(BaseEmitter):
    language_id = "c"
    file_extension = "c"

    def native_type(self, generic_type: str) -> str:
        return C_TYPES.get(generic_type, "int")

    def _format_bool(self, value: bool) -> str:
        return "1" if value else "0"

    def emit_assignment(self, stmt: Assignment, indent: str) -> str:
        return f"{indent}{stmt.target} = {self.emit_expr(stmt.value)};"

    def emit_input(self, stmt: Input, indent: str) -> str:
        lines = []
        if stmt.prompt:
            lines.append(f'{indent}printf("{stmt.prompt}: ");')
        target_type = self.program.variable_types.get(stmt.target, "int") if self.program else "int"
        fmt = {"float": "%lf", "int": "%d"}.get(target_type, "%d")
        lines.append(f'{indent}scanf("{fmt}", &{stmt.target});')
        return "\n".join(lines)

    def emit_output(self, stmt: Output, indent: str) -> str:
        value = stmt.value
        if isinstance(value, StringLiteral):
            escaped = value.value.replace('"', '\\"')
            return f'{indent}printf("{escaped}\\n");'
        if isinstance(value, RawExpr):
            return f'{indent}printf("%s\\n", "{value.text}");'
        value_type = self.expr_type(value)
        fmt = {"float": "%f", "string": "%s"}.get(value_type, "%d")
        return f'{indent}printf("{fmt}\\n", {self.emit_expr(value)});'

    def emit_return(self, indent: str) -> str:
        return f"{indent}return 0;"

    def emit_program(self, program: Program) -> str:
        self.program = program
        decl_lines = [
            f"{INDENT_UNIT}{self.native_type(t)} {name} = {self.default_value_literal(t)};"
            for name, t in program.variable_types.items()
        ]
        body = self.emit_block(program.body, INDENT_UNIT)
        parts = ["#include <stdio.h>\n", "int main() {"]
        if decl_lines:
            parts.append("\n".join(decl_lines))
        if body:
            parts.append(body)
        parts.append(f"{INDENT_UNIT}return 0;")
        parts.append("}")
        return "\n".join(p for p in parts if p != "") + "\n"
