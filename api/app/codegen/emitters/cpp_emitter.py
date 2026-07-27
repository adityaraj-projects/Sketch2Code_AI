from __future__ import annotations

from app.codegen.emitters.base import INDENT_UNIT, BaseEmitter
from app.codegen.ir import Assignment, Input, Output, Program

CPP_TYPES = {"int": "int", "float": "double", "string": "std::string", "bool": "bool", "unknown": "auto"}


class CppEmitter(BaseEmitter):
    language_id = "cpp"
    file_extension = "cpp"

    def native_type(self, generic_type: str) -> str:
        return CPP_TYPES.get(generic_type, "auto")

    def emit_assignment(self, stmt: Assignment, indent: str) -> str:
        return f"{indent}{stmt.target} = {self.emit_expr(stmt.value)};"

    def emit_input(self, stmt: Input, indent: str) -> str:
        lines = []
        if stmt.prompt:
            lines.append(f'{indent}std::cout << "{stmt.prompt}: ";')
        lines.append(f"{indent}std::cin >> {stmt.target};")
        return "\n".join(lines)

    def emit_output(self, stmt: Output, indent: str) -> str:
        return f'{indent}std::cout << {self.emit_expr(stmt.value)} << "\\n";'

    def emit_return(self, indent: str) -> str:
        return f"{indent}return 0;"

    def emit_program(self, program: Program) -> str:
        self.program = program
        decl_lines = [
            f"{INDENT_UNIT}{self.native_type(t)} {name} = {self.default_value_literal(t)};"
            for name, t in program.variable_types.items()
        ]
        body = self.emit_block(program.body, INDENT_UNIT)
        parts = ["#include <iostream>\n#include <string>\n", "int main() {"]
        if decl_lines:
            parts.append("\n".join(decl_lines))
        if body:
            parts.append(body)
        parts.append(f"{INDENT_UNIT}return 0;")
        parts.append("}")
        return "\n".join(p for p in parts if p != "") + "\n"
