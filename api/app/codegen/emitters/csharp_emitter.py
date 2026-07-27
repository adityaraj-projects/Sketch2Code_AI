from __future__ import annotations

from app.codegen.emitters.base import INDENT_UNIT, BaseEmitter
from app.codegen.ir import Assignment, Input, Output, Program

CSHARP_TYPES = {"int": "int", "float": "double", "string": "string", "bool": "bool", "unknown": "dynamic"}


class CSharpEmitter(BaseEmitter):
    language_id = "csharp"
    file_extension = "cs"

    def native_type(self, generic_type: str) -> str:
        return CSHARP_TYPES.get(generic_type, "dynamic")

    def emit_assignment(self, stmt: Assignment, indent: str) -> str:
        return f"{indent}{stmt.target} = {self.emit_expr(stmt.value)};"

    def emit_input(self, stmt: Input, indent: str) -> str:
        lines = []
        if stmt.prompt:
            lines.append(f'{indent}Console.Write("{stmt.prompt}: ");')
        target_type = self.program.variable_types.get(stmt.target, "int") if self.program else "int"
        parse_fn = {"float": "Convert.ToDouble", "int": "Convert.ToInt32"}.get(target_type, "Convert.ToInt32")
        lines.append(f"{indent}{stmt.target} = {parse_fn}(Console.ReadLine());")
        return "\n".join(lines)

    def emit_output(self, stmt: Output, indent: str) -> str:
        return f"{indent}Console.WriteLine({self.emit_expr(stmt.value)});"

    def emit_program(self, program: Program) -> str:
        self.program = program
        decl_lines = [
            f"{INDENT_UNIT * 2}{self.native_type(t)} {name} = {self.default_value_literal(t)};"
            for name, t in program.variable_types.items()
        ]
        body = self.emit_block(program.body, INDENT_UNIT * 2)
        parts = [
            "using System;\n",
            "class Program {",
            f"{INDENT_UNIT}static void Main(string[] args) {{",
        ]
        if decl_lines:
            parts.append("\n".join(decl_lines))
        if body:
            parts.append(body)
        parts.append(f"{INDENT_UNIT}}}")
        parts.append("}")
        return "\n".join(p for p in parts if p != "") + "\n"
