from __future__ import annotations

from app.codegen.emitters.base import BaseEmitter
from app.codegen.emitters.c_emitter import CEmitter
from app.codegen.emitters.cpp_emitter import CppEmitter
from app.codegen.emitters.csharp_emitter import CSharpEmitter
from app.codegen.emitters.go_emitter import GoEmitter
from app.codegen.emitters.java_emitter import JavaEmitter
from app.codegen.emitters.javascript_emitter import JavaScriptEmitter
from app.codegen.emitters.php_emitter import PhpEmitter
from app.codegen.emitters.python_emitter import PythonEmitter
from app.codegen.emitters.rust_emitter import RustEmitter
from app.codegen.emitters.typescript_emitter import TypeScriptEmitter

EMITTER_REGISTRY: dict[str, type[BaseEmitter]] = {
    "python": PythonEmitter,
    "java": JavaEmitter,
    "c": CEmitter,
    "cpp": CppEmitter,
    "javascript": JavaScriptEmitter,
    "typescript": TypeScriptEmitter,
    "csharp": CSharpEmitter,
    "go": GoEmitter,
    "rust": RustEmitter,
    "php": PhpEmitter,
}


def get_emitter(language_id: str) -> BaseEmitter:
    cls = EMITTER_REGISTRY.get(language_id)
    if cls is None:
        supported = ", ".join(sorted(EMITTER_REGISTRY))
        raise ValueError(f"Unsupported language '{language_id}'. Supported: {supported}")
    return cls()
