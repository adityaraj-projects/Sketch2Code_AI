from __future__ import annotations

from app.codegen.emitters.base import INDENT_UNIT, BaseEmitter
from app.codegen.ir import Assignment, If, Input, Output, Program, While

GO_TYPES = {"int": "int", "float": "float64", "string": "string", "bool": "bool", "unknown": "interface{}"}


class GoEmitter(BaseEmitter):
    language_id = "go"
    file_extension = "go"

    def native_type(self, generic_type: str) -> str:
        return GO_TYPES.get(generic_type, "interface{}")

    def emit_assignment(self, stmt: Assignment, indent: str) -> str:
        return f"{indent}{stmt.target} = {self.emit_expr(stmt.value)}"

    def emit_input(self, stmt: Input, indent: str) -> str:
        lines = []
        if stmt.prompt:
            lines.append(f'{indent}fmt.Print("{stmt.prompt}: ")')
        lines.append(f'{indent}fmt.Scan(&{stmt.target})')
        return "\n".join(lines)

    def emit_output(self, stmt: Output, indent: str) -> str:
        return f"{indent}fmt.Println({self.emit_expr(stmt.value)})"

    def emit_if(self, stmt: If, indent: str) -> str:
        header = f"{indent}if {self.emit_expr(stmt.condition)} {{"
        then_code = self.emit_block(stmt.then_body, indent + INDENT_UNIT)
        lines = [header, then_code, f"{indent}}}"]
        if stmt.else_body:
            else_code = self.emit_block(stmt.else_body, indent + INDENT_UNIT)
            lines = [header, then_code, f"{indent}}} else {{", else_code, f"{indent}}}"]
        return "\n".join(line for line in lines if line != "")

    def emit_while(self, stmt: While, indent: str) -> str:
        header = f"{indent}for {self.emit_expr(stmt.condition)} {{"
        body_code = self.emit_block(stmt.body, indent + INDENT_UNIT)
        return "\n".join(line for line in [header, body_code, f"{indent}}}"] if line != "")

    def emit_program(self, program: Program) -> str:
        self.program = program
        decl_lines = [
            f"{INDENT_UNIT}var {name} {self.native_type(t)} = {self.default_value_literal(t)}"
            for name, t in program.variable_types.items()
        ]
        body = self.emit_block(program.body, INDENT_UNIT)
        parts = ['package main\n\nimport "fmt"\n', "func main() {"]
        if decl_lines:
            parts.append("\n".join(decl_lines))
        if body:
            parts.append(body)
        parts.append("}")
        return "\n".join(p for p in parts if p != "") + "\n"
