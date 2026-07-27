"""
Classifies a closed shape outline into one of the standard flowchart
symbols using normalized template matching: the outline is resampled to a
fixed point count, scaled into its own bounding box, and compared against
ideal templates (rectangle, diamond, parallelogram, ellipse) scaled the
same way. Whichever template has the lowest average nearest-point distance
wins, provided it clears a rejection threshold — sketches that don't
resemble any known symbol are correctly left unclassified rather than
forced into the closest guess.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from app.recognition.geometry import (
    BBox,
    Point,
    average_nearest_distance,
    bbox_of,
    circularity,
    normalize_to_unit_square,
    resample_closed_polyline,
)

RESAMPLE_POINTS = 48
REJECTION_THRESHOLD = 0.16  # in normalized [0,1] units; empirically tuned
CIRCULARITY_OVAL_THRESHOLD = 0.74


def _template_rectangle() -> list[Point]:
    return [(0, 0), (1, 0), (1, 1), (0, 1)]


def _template_diamond() -> list[Point]:
    return [(0.5, 0), (1, 0.5), (0.5, 1), (0, 0.5)]


def _template_parallelogram() -> list[Point]:
    # Slanted left/right edges — the classic input/output symbol.
    return [(0.22, 0), (1, 0), (0.78, 1), (0, 1)]


def _template_ellipse(n: int = RESAMPLE_POINTS) -> list[Point]:
    return [
        (0.5 + 0.5 * math.cos(2 * math.pi * i / n), 0.5 + 0.5 * math.sin(2 * math.pi * i / n))
        for i in range(n)
    ]


_TEMPLATES = {
    "rectangle": _template_rectangle(),
    "diamond": _template_diamond(),
    "parallelogram": _template_parallelogram(),
}


@dataclass
class ShapeCandidate:
    template: str  # "rectangle" | "diamond" | "parallelogram" | "ellipse"
    outline_points: list[Point]
    bbox: BBox
    score: float
    circularity: float
    aspect_ratio: float


def classify_outline(outline_points: list[Point]) -> ShapeCandidate | None:
    box = bbox_of(outline_points)
    if box.width < 8 or box.height < 8:
        return None  # too small to be a meaningful symbol, likely noise

    circ = circularity(outline_points)
    aspect = box.width / max(box.height, 1e-6)

    # Ellipse gets a dedicated, cheap check first since round hand-drawn
    # shapes resample poorly against sharp-cornered polygon templates.
    if circ >= CIRCULARITY_OVAL_THRESHOLD:
        return ShapeCandidate(
            template="ellipse", outline_points=outline_points, bbox=box,
            score=1.0 - circ, circularity=circ, aspect_ratio=aspect,
        )

    resampled = resample_closed_polyline(outline_points, RESAMPLE_POINTS)
    normalized = normalize_to_unit_square(resampled, box)

    best_name: str | None = None
    best_score = math.inf
    for name, template in _TEMPLATES.items():
        template_resampled = resample_closed_polyline(template, RESAMPLE_POINTS)
        score = average_nearest_distance(normalized, template_resampled)
        if score < best_score:
            best_score = score
            best_name = name

    if best_name is None or best_score > REJECTION_THRESHOLD:
        return None

    return ShapeCandidate(
        template=best_name, outline_points=outline_points, bbox=box,
        score=best_score, circularity=circ, aspect_ratio=aspect,
    )
