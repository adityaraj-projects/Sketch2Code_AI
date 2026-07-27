from __future__ import annotations

from app.codegen.emitters.base import INDENT_UNIT, BaseEmitter
from app.codegen.ir import Assignment, If, Input, Output, Program, While

RUST_TYPES = {"int": "i32", "float": "f64", "string": "String", "bool": "bool", "unknown": "i32"}


class RustEmitter(BaseEmitter):
    language_id = "rust"
    file_extension = "rs"

    def __init__(self):
        self._input_counter = 0

    def native_type(self, generic_type: str) -> str:
        return RUST_TYPES.get(generic_type, "i32")

    def default_value_literal(self, generic_type: str) -> str:
        if generic_type == "string":
            return "String::new()"
        return super().default_value_literal(generic_type)

    def emit_assignment(self, stmt: Assignment, indent: str) -> str:
        return f"{indent}{stmt.target} = {self.emit_expr(stmt.value)};"

    def emit_input(self, stmt: Input, indent: str) -> str:
        self._input_counter += 1
        buf = f"input_buf_{self._input_counter}"
        lines = []
        if stmt.prompt:
            lines.append(f'{indent}println!("{stmt.prompt}: ");')
        lines.append(f"{indent}let mut {buf} = String::new();")
        lines.append(f'{indent}std::io::stdin().read_line(&mut {buf}).expect("Failed to read line");')
        target_type = self.program.variable_types.get(stmt.target, "int") if self.program else "int"
        if target_type == "string":
            lines.append(f"{indent}{stmt.target} = {buf}.trim().to_string();")
        else:
            lines.append(f'{indent}{stmt.target} = {buf}.trim().parse().expect("Please enter a valid number");')
        return "\n".join(lines)

    def emit_output(self, stmt: Output, indent: str) -> str:
        return f'{indent}println!("{{}}", {self.emit_expr(stmt.value)});'

    def emit_if(self, stmt: If, indent: str) -> str:
        header = f"{indent}if {self.emit_expr(stmt.condition)} {{"
        then_code = self.emit_block(stmt.then_body, indent + INDENT_UNIT)
        lines = [header, then_code, f"{indent}}}"]
        if stmt.else_body:
            else_code = self.emit_block(stmt.else_body, indent + INDENT_UNIT)
            lines = [header, then_code, f"{indent}}} else {{", else_code, f"{indent}}}"]
        return "\n".join(line for line in lines if line != "")

    def emit_while(self, stmt: While, indent: str) -> str:
        header = f"{indent}while {self.emit_expr(stmt.condition)} {{"
        body_code = self.emit_block(stmt.body, indent + INDENT_UNIT)
        return "\n".join(line for line in [header, body_code, f"{indent}}}"] if line != "")

    def emit_program(self, program: Program) -> str:
        self.program = program
        self._input_counter = 0
        decl_lines = [
            f"{INDENT_UNIT}let mut {name}: {self.native_type(t)} = {self.default_value_literal(t)};"
            for name, t in program.variable_types.items()
        ]
        body = self.emit_block(program.body, INDENT_UNIT)
        parts = ["fn main() {"]
        if decl_lines:
            parts.append("\n".join(decl_lines))
        if body:
            parts.append(body)
        parts.append("}")
        return "\n".join(p for p in parts if p != "") + "\n"
