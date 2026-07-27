from __future__ import annotations

from app.codegen.emitters.base import INDENT_UNIT, BaseEmitter
from app.codegen.ir import Assignment, If, Input, Output, Program, Stmt, While

PY_OP_MAP = {
    "and": "and", "or": "or", "not": "not",
    "+": "+", "-": "-", "*": "*", "/": "/", "%": "%", "//": "//",
    "<": "<", ">": ">", "<=": "<=", ">=": ">=", "==": "==", "!=": "!=",
}


class PythonEmitter(BaseEmitter):
    language_id = "python"
    file_extension = "py"
    op_map = PY_OP_MAP
    uses_braces = False
    statement_terminator = ""

    def _format_bool(self, value: bool) -> str:
        return "True" if value else "False"

    def emit_assignment(self, stmt: Assignment, indent: str) -> str:
        return f"{indent}{stmt.target} = {self.emit_expr(stmt.value)}"

    def emit_input(self, stmt: Input, indent: str) -> str:
        prompt = stmt.prompt or f"Enter {stmt.target}: "
        escaped = prompt.replace('"', '\\"')
        return f'{indent}{stmt.target} = int(input("{escaped}"))'

    def emit_output(self, stmt: Output, indent: str) -> str:
        return f"{indent}print({self.emit_expr(stmt.value)})"

    def emit_comment(self, stmt, indent: str) -> str:
        return f"{indent}# {stmt.text}"

    def emit_return(self, indent: str) -> str:
        return f"{indent}return"

    def emit_if(self, stmt: If, indent: str) -> str:
        lines = [f"{indent}if {self.emit_expr(stmt.condition)}:"]
        then_code = self.emit_block(stmt.then_body, indent + INDENT_UNIT)
        lines.append(then_code if then_code else f"{indent}{INDENT_UNIT}pass")
        if stmt.else_body:
            lines.append(f"{indent}else:")
            else_code = self.emit_block(stmt.else_body, indent + INDENT_UNIT)
            lines.append(else_code if else_code else f"{indent}{INDENT_UNIT}pass")
        return "\n".join(lines)

    def emit_while(self, stmt: While, indent: str) -> str:
        lines = [f"{indent}while {self.emit_expr(stmt.condition)}:"]
        body_code = self.emit_block(stmt.body, indent + INDENT_UNIT)
        lines.append(body_code if body_code else f"{indent}{INDENT_UNIT}pass")
        return "\n".join(lines)

    def emit_program(self, program: Program) -> str:
        self.program = program
        declarations = "\n".join(
            f"{INDENT_UNIT}{name} = {self.default_value_literal(t)}"
            for name, t in program.variable_types.items()
        )
        body = self.emit_block(program.body, INDENT_UNIT)
        if not body:
            body = f"{INDENT_UNIT}pass"
        parts = ["def main():"]
        if declarations:
            parts.append(declarations)
        parts.append(body)
        return "\n".join(parts) + '\n\n\nif __name__ == "__main__":\n' + f"{INDENT_UNIT}main()\n"
