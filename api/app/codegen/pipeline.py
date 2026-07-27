from __future__ import annotations

from dataclasses import dataclass

from app.codegen.emitters.registry import get_emitter
from app.codegen.graph_structurer import GraphEdge, GraphNode, GraphStructurer
from app.codegen.type_inference import infer_types


@dataclass
class CodegenResult:
    code: str
    language: str
    file_extension: str
    warnings: list[str]


def generate_code(nodes_data: list[dict], edges_data: list[dict], language: str) -> CodegenResult:
    nodes = [GraphNode(id=n["id"], type=n["type"], text=n.get("text", "")) for n in nodes_data]
    edges = [
        GraphEdge(id=e["id"], from_id=e["fromNodeId"], to_id=e["toNodeId"], label=e.get("label"))
        for e in edges_data
    ]

    structurer = GraphStructurer(nodes, edges)
    program = structurer.structure()
    program = infer_types(program)

    emitter = get_emitter(language)
    code = emitter.emit_program(program)

    return CodegenResult(
        code=code,
        language=language,
        file_extension=emitter.file_extension,
        warnings=structurer.warnings,
    )
