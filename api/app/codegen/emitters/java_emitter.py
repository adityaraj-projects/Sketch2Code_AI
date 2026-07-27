from __future__ import annotations

from app.codegen.emitters.base import INDENT_UNIT, BaseEmitter
from app.codegen.ir import Assignment, Input, Output, Program

JAVA_TYPES = {"int": "int", "float": "double", "string": "String", "bool": "boolean", "unknown": "Object"}


class JavaEmitter(BaseEmitter):
    language_id = "java"
    file_extension = "java"

    def native_type(self, generic_type: str) -> str:
        return JAVA_TYPES.get(generic_type, "Object")

    def emit_assignment(self, stmt: Assignment, indent: str) -> str:
        return f"{indent}{stmt.target} = {self.emit_expr(stmt.value)};"

    def emit_input(self, stmt: Input, indent: str) -> str:
        lines = []
        if stmt.prompt:
            lines.append(f'{indent}System.out.print("{stmt.prompt}: ");')
        lines.append(f"{indent}{stmt.target} = scanner.nextInt();")
        return "\n".join(lines)

    def emit_output(self, stmt: Output, indent: str) -> str:
        return f"{indent}System.out.println({self.emit_expr(stmt.value)});"

    def emit_program(self, program: Program) -> str:
        self.program = program
        decl_lines = [
            f"{INDENT_UNIT * 2}{self.native_type(t)} {name} = {self.default_value_literal(t)};"
            for name, t in program.variable_types.items()
        ]
        body = self.emit_block(program.body, INDENT_UNIT * 2)

        parts = [
            "import java.util.Scanner;\n",
            "public class Main {",
            f"{INDENT_UNIT}public static void main(String[] args) {{",
            f"{INDENT_UNIT * 2}Scanner scanner = new Scanner(System.in);",
        ]
        if decl_lines:
            parts.append("\n".join(decl_lines))
        if body:
            parts.append(body)
        parts.append(f"{INDENT_UNIT}}}")
        parts.append("}")
        return "\n".join(p for p in parts if p != "") + "\n"
