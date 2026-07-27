from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

SupportedLanguage = Literal[
    "python", "java", "c", "cpp", "javascript", "typescript", "csharp", "go", "rust", "php"
]


class CodegenNodeIn(BaseModel):
    id: str
    type: str
    text: str = ""


class CodegenEdgeIn(BaseModel):
    id: str
    fromNodeId: str
    toNodeId: str
    label: str | None = None


class CodegenRequest(BaseModel):
    nodes: list[CodegenNodeIn]
    edges: list[CodegenEdgeIn]
    language: SupportedLanguage


class CodegenResponse(BaseModel):
    code: str
    language: str
    file_extension: str
    warnings: list[str]


class SupportedLanguagesResponse(BaseModel):
    languages: list[str]
