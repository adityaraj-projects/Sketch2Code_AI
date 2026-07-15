from __future__ import annotations

_SYSTEM_PROMPT = (
    "You convert a spoken description of a flowchart or algorithm into real, valid Python "
    "source code that a simple flowchart generator can parse. Follow these rules exactly:\n"
    "- Output ONLY Python code. No markdown code fences, no explanation, no comments about what you did.\n"
    "- Use only: variable assignments, input(), print(), if/elif/else, while loops, and "
    "range()-based for loops. Do not define functions, classes, or import anything.\n"
    "- Keep it short and directly runnable top-to-bottom as a script.\n"
    "- If the request describes a well-known algorithm (factorial, Fibonacci, prime check, "
    "a login check, etc.), implement it straightforwardly.\n"
    "- If the request is vague, make a reasonable, simple interpretation rather than asking "
    "a clarifying question — you cannot ask questions, only produce code."
)


def build_voice_prompt(description: str, previous_error: str | None = None) -> tuple[str, str]:
    user_prompt = f'Spoken request: "{description}"\n\nWrite the Python code now.'
    if previous_error:
        user_prompt += (
            f"\n\nYour previous attempt had a Python syntax error: {previous_error}\n"
            "Fix it and output only corrected, valid Python code."
        )
    return _SYSTEM_PROMPT, user_prompt


def strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines)
    return stripped.strip()
