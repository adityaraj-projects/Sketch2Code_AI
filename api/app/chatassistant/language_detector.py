from __future__ import annotations

import re

_LANGUAGE_KEYWORDS: dict[str, str] = {
    "c\\+\\+": "cpp", "cpp": "cpp",
    "c#": "csharp", "csharp": "csharp", "c sharp": "csharp",
    "python": "python", "py": "python",
    "java(?!script)": "java",
    "javascript": "javascript", "js": "javascript",
    "typescript": "typescript", "ts": "typescript",
    "golang": "go", "\\bgo\\b": "go",
    "rust": "rust",
    "php": "php",
}

DEFAULT_LANGUAGE = "python"


def detect_language(message: str) -> str:
    low = message.lower()
    for pattern, language_id in _LANGUAGE_KEYWORDS.items():
        if re.search(pattern, low):
            return language_id
    # Plain "c" is checked last, and only as an isolated word, so it
    # doesn't match inside "c++"/"c#"/"csharp" (already handled above).
    if re.search(r"\bc\b", low):
        return "c"
    return DEFAULT_LANGUAGE
