from __future__ import annotations

from app.codegen.emitters.base import INDENT_UNIT, BaseEmitter
from app.codegen.ir import Assignment, Input, Output, Program


class JavaScriptEmitter(BaseEmitter):
    language_id = "javascript"
    file_extension = "js"

    def emit_assignment(self, stmt: Assignment, indent: str) -> str:
        return f"{indent}{stmt.target} = {self.emit_expr(stmt.value)};"

    def emit_input(self, stmt: Input, indent: str) -> str:
        prompt = stmt.prompt or f"Enter {stmt.target}"
        # Browser/Node-agnostic: readline-sync-free approach using a prompt
        # helper the program defines at the top (see emit_program).
        return f'{indent}{stmt.target} = Number(promptSync("{prompt}: "));'

    def emit_output(self, stmt: Output, indent: str) -> str:
        return f"{indent}console.log({self.emit_expr(stmt.value)});"

    def _default_by_lang_type(self, t: str) -> str:
        return self.default_value_literal(t)

    def emit_program(self, program: Program) -> str:
        self.program = program
        decl_lines = [
            f"{INDENT_UNIT}let {name} = {self.default_value_literal(t)};"
            for name, t in program.variable_types.items()
        ]
        body = self.emit_block(program.body, INDENT_UNIT)

        header = (
            "// Node.js: npm install prompt-sync, or replace promptSync with your\n"
            "// own input source (e.g. reading from a form in the browser).\n"
            "const promptSync = require(\"prompt-sync\")();\n\n"
        )
        parts = [header + "function main() {"]
        if decl_lines:
            parts.append("\n".join(decl_lines))
        if body:
            parts.append(body)
        parts.append("}")
        return "\n".join(p for p in parts if p != "") + "\n\nmain();\n"
