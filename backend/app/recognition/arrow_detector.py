"""
Identifies which non-shape strokes are actually arrows connecting two
nodes, then figures out direction.

Two real signals are used together:
1. Path shape: an arrow is elongated (its path length is close to the
   straight-line distance between its endpoints) rather than a closed or
   scribbly blob.
2. Arrowhead geometry: near one end, the pen typically draws a tighter,
   sharper zig-zag (the barbs of the arrowhead) than the rest of the
   stroke. We measure total absolute turning angle in the last portion of
   the path from each end and call the end with more "turning energy" the
   head. If both ends are equally straight (no drawn arrowhead), we fall
   back to stroke draw order — the pen conventionally travels from source
   to target — which is the same convention most sketch-recognition
   systems use in the absence of an explicit arrowhead glyph.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.recognition.geometry import BBox, Point, distance, path_length, turning_angle
from app.recognition.grouping import RawStroke

STRAIGHTNESS_MIN_RATIO = 0.62  # path_length vs straight-line distance
MIN_LENGTH = 24.0
ENDPOINT_SNAP_MARGIN = 26.0
ARROWHEAD_SAMPLE_FRACTION = 0.28


@dataclass
class RecognizedArrow:
    points: list[Point]
    from_node_index: int | None
    to_node_index: int | None


def is_arrow_like(points: list[Point]) -> bool:
    straight_dist = distance(points[0], points[-1])
    length = path_length(points)
    if length < MIN_LENGTH:
        return False
    if straight_dist < 1e-6:
        return False
    return (straight_dist / length) >= STRAIGHTNESS_MIN_RATIO


def _turning_energy(points: list[Point], from_start: bool) -> float:
    sample_count = max(3, int(len(points) * ARROWHEAD_SAMPLE_FRACTION))
    segment = points[:sample_count] if from_start else points[-sample_count:]
    if len(segment) < 3:
        return 0.0
    total = 0.0
    for i in range(1, len(segment) - 1):
        total += abs(turning_angle(segment[i - 1], segment[i], segment[i + 1]))
    return total


def _nearest_node(point: Point, node_boxes: list[BBox]) -> int | None:
    best_index: int | None = None
    best_dist = ENDPOINT_SNAP_MARGIN
    for i, box in enumerate(node_boxes):
        padded = box.expanded(ENDPOINT_SNAP_MARGIN)
        if padded.contains_point(point):
            cx, cy = box.center
            d = distance(point, (cx, cy))
            if best_index is None or d < best_dist:
                best_index = i
                best_dist = d
    return best_index


def detect_arrow(stroke: RawStroke, node_boxes: list[BBox]) -> RecognizedArrow | None:
    points = stroke.points
    if not is_arrow_like(points):
        return None

    start_energy = _turning_energy(points, from_start=True)
    end_energy = _turning_energy(points, from_start=False)

    # More turning energy at the end than the start => arrowhead barbs were
    # drawn at the end => stroke was drawn source -> target already.
    # Meaningfully more energy at the *start* means the pen drew the
    # arrowhead first, i.e. target -> source, so we flip the points.
    if start_energy > end_energy * 1.35:
        points = list(reversed(points))

    from_idx = _nearest_node(points[0], node_boxes)
    to_idx = _nearest_node(points[-1], node_boxes)

    return RecognizedArrow(points=points, from_node_index=from_idx, to_node_index=to_idx)
