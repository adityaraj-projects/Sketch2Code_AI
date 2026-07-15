"""
Voice Mode doesn't have its own understanding of flowcharts or its own
layout logic — it's Feature 3 (Code -> Flowchart) with an LLM standing in
for "paste some Python". The AI's only job is turning a spoken sentence
into a short, real Python script; the exact same `parse_python_source`
(real `ast`-based parsing) and `FlowchartLayout` (real auto-layout) that
already power Code -> Flowchart do everything after that. If the model's
code doesn't parse, one retry is attempted with the actual syntax error
fed back — and if that still fails, this returns a clear error rather
than fabricating a flowchart from nothing.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.codetoflow.flowchart_layout import FlowchartLayout
from app.codetoflow.python_ast_adapter import UnsupportedSourceError, parse_python_source
from app.explainer.providers import TextProvider
from app.voicemode.prompts import build_voice_prompt, strip_code_fences

MAX_ATTEMPTS = 2


@dataclass
class VoiceModeResult:
    success: bool
    nodes: list
    edges: list
    warnings: list[str]
    generated_code: str
    error_message: str | None = None


def generate_flowchart_from_speech(description: str, provider: TextProvider) -> VoiceModeResult:
    previous_error: str | None = None
    last_code = ""

    for attempt in range(MAX_ATTEMPTS):
        system_prompt, user_prompt = build_voice_prompt(description, previous_error)
        raw = provider.generate(system_prompt, user_prompt)
        code = strip_code_fences(raw)
        last_code = code

        try:
            program, parse_warnings = parse_python_source(code)
        except UnsupportedSourceError as e:
            previous_error = str(e)
            if attempt == MAX_ATTEMPTS - 1:
                return VoiceModeResult(
                    success=False, nodes=[], edges=[], warnings=[], generated_code=code,
                    error_message=(
                        "Couldn't turn that into a working flowchart — try describing it more "
                        "simply, e.g. 'a flowchart that checks if a number is even or odd'."
                    ),
                )
            continue

        layout = FlowchartLayout()
        nodes, edges, layout_warnings = layout.build(program)
        return VoiceModeResult(
            success=True, nodes=nodes, edges=edges,
            warnings=parse_warnings + layout_warnings, generated_code=code,
        )

    return VoiceModeResult(
        success=False, nodes=[], edges=[], warnings=[], generated_code=last_code,
        error_message="Couldn't turn that into a working flowchart. Please try rephrasing.",
    )
