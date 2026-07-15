from __future__ import annotations

from app.codegen.emitters.base import INDENT_UNIT
from app.codegen.emitters.javascript_emitter import JavaScriptEmitter
from app.codegen.ir import Program

TS_TYPES = {"int": "number", "float": "number", "string": "string", "bool": "boolean", "unknown": "any"}


class TypeScriptEmitter(JavaScriptEmitter):
    language_id = "typescript"
    file_extension = "ts"

    def native_type(self, generic_type: str) -> str:
        return TS_TYPES.get(generic_type, "any")

    def emit_program(self, program: Program) -> str:
        self.program = program
        decl_lines = [
            f"{INDENT_UNIT}let {name}: {self.native_type(t)} = {self.default_value_literal(t)};"
            for name, t in program.variable_types.items()
        ]
        body = self.emit_block(program.body, INDENT_UNIT)

        header = (
            "// Node.js: npm install prompt-sync @types/prompt-sync, or replace\n"
            "// promptSync with your own input source.\n"
            "import promptSyncFactory from \"prompt-sync\";\n"
            "const promptSync = promptSyncFactory();\n\n"
        )
        parts = [header + "function main(): void {"]
        if decl_lines:
            parts.append("\n".join(decl_lines))
        if body:
            parts.append(body)
        parts.append("}")
        return "\n".join(p for p in parts if p != "") + "\n\nmain();\n"
