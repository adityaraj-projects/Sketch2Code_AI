"""
Classifies what the person is asking for so the assistant can route to
the right *existing* pipeline (Bug Detector, Complexity, Code Generation,
Beautifier, Explainer) instead of asking an LLM to reimplement all of
those from scratch inside a chat reply. This is deliberately simple,
deterministic keyword/phrase matching — routing intent doesn't need an
AI call, and keeping it rule-based means the assistant works even
without an AI_PROVIDER key configured for every intent except open-ended
questions and prose explanations.
"""
from __future__ import annotations

import re
from enum import Enum


class Intent(str, Enum):
    BUG_CHECK = "bug_check"
    COMPLEXITY = "complexity"
    GENERATE_CODE = "generate_code"
    BEAUTIFY = "beautify"
    EXPLAIN = "explain"
    GENERAL = "general"


_BUG_RE = re.compile(r"\b(bugs?|errors?|wrong|broken|not working|fix(?:ed|ing)? (?:the )?(?:error|bug|issue)|find problems?|check problems?)\b", re.IGNORECASE)
_COMPLEXITY_RE = re.compile(r"\b(complexity|big-?o|efficient|efficiency|optimi[sz]e|optimi[sz]ation|faster|slow|runtime)\b", re.IGNORECASE)
_LANGUAGE_NAMES = r"(python|java|c\+\+|cpp|c#|csharp|javascript|typescript|golang|go|rust|php|\bc\b)"
_CODE_RE = re.compile(
    rf"\b(generate|write|give me|create)\b.*\bcode\b"
    rf"|\bcode in\b"
    rf"|\bconvert.*to code\b"
    rf"|\b(generate|write|give me|create)\b.*\b(in|using)\b\s*{_LANGUAGE_NAMES}",
    re.IGNORECASE,
)
_BEAUTIFY_RE = re.compile(r"\b(beautify|clean ?up|arrange|align|tidy|re-?layout|rearrange)\b", re.IGNORECASE)
_EXPLAIN_RE = re.compile(r"\b(explain|what does|how does|walk me through|understand|describe)\b", re.IGNORECASE)


def classify_intent(message: str) -> Intent:
    if _BUG_RE.search(message):
        return Intent.BUG_CHECK
    if _COMPLEXITY_RE.search(message):
        return Intent.COMPLEXITY
    if _CODE_RE.search(message):
        return Intent.GENERATE_CODE
    if _BEAUTIFY_RE.search(message):
        return Intent.BEAUTIFY
    if _EXPLAIN_RE.search(message):
        return Intent.EXPLAIN
    return Intent.GENERAL
