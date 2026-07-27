from __future__ import annotations

from dataclasses import dataclass

from app.codegen.type_inference import infer_types
from app.codetoflow.flowchart_layout import FlowchartLayout
from app.codetoflow.python_ast_adapter import UnsupportedSourceError, parse_python_source


@dataclass
class CodeToFlowchartResult:
    nodes: list
    edges: list
    warnings: list[str]


def generate_flowchart_from_code(source: str, language: str) -> CodeToFlowchartResult:
    if language != "python":
        raise ValueError(
            f"Code-to-flowchart currently supports Python only, not '{language}'. "
            "Other languages are a natural extension of the same pipeline — see the README."
        )

    program, parse_warnings = parse_python_source(source)
    program = infer_types(program)  # not strictly needed for layout, but keeps parity with codegen's IR

    layout = FlowchartLayout()
    nodes, edges, layout_warnings = layout.build(program)

    return CodeToFlowchartResult(nodes=nodes, edges=edges, warnings=parse_warnings + layout_warnings)
