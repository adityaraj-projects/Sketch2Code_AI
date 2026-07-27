"""
Given a decision node's outgoing edges, figures out which one is the
"true"/Yes branch and which is "false"/No — by label when the connectors
are labeled, falling back to declared order otherwise. Shared by
graph_structurer.py (code generation) and the execution simulator, so a
flowchart is guaranteed to branch the same way whether you generate code
from it or run it.
"""
from __future__ import annotations

from typing import Protocol


class EdgeLike(Protocol):
    id: str
    to_id: str
    label: str | None


def _label_truth(label: str | None) -> bool | None:
    if not label:
        return None
    low = label.strip().lower()
    if low in ("yes", "true", "y"):
        return True
    if low in ("no", "false", "n"):
        return False
    return None


def resolve_branch(node_id: str, outgoing: list[EdgeLike]) -> tuple[EdgeLike | None, EdgeLike | None, list[str]]:
    """Returns (true_edge, false_edge, warnings)."""
    warnings: list[str] = []

    if len(outgoing) == 0:
        return None, None, [f"Decision '{node_id}' has no outgoing connectors."]

    if len(outgoing) == 1:
        return outgoing[0], None, [f"Decision '{node_id}' only has one outgoing connector."]

    labeled_true = next((e for e in outgoing if _label_truth(e.label) is True), None)
    labeled_false = next((e for e in outgoing if _label_truth(e.label) is False), None)
    if labeled_true and labeled_false:
        return labeled_true, labeled_false, warnings

    warnings.append(
        f"Decision '{node_id}' has no Yes/No labeled connectors — assuming the first "
        "connector is the 'true' branch."
    )
    return outgoing[0], outgoing[1], warnings
