"""
Groups raw strokes into connected spatial components before classification.

A hand-drawn flowchart is rarely one stroke per shape — pens lift at
corners, outlines get redrawn, labels are written separately. This module
merges strokes whose (padded) bounding boxes overlap into a single
component using union-find, so the classifier downstream reasons about
"this cluster of ink" rather than individual pen strokes.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.recognition.geometry import BBox, Point, bbox_of, bbox_union, to_points


@dataclass
class RawStroke:
    id: str
    points: list[Point]
    bbox: BBox


@dataclass
class StrokeComponent:
    id: str
    strokes: list[RawStroke]
    bbox: BBox

    @property
    def all_points(self) -> list[Point]:
        pts: list[Point] = []
        for s in self.strokes:
            pts.extend(s.points)
        return pts


class _UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def build_raw_strokes(strokes_data: list[dict]) -> list[RawStroke]:
    raw: list[RawStroke] = []
    for s in strokes_data:
        pts = to_points(s["points"])
        if len(pts) < 2:
            continue
        raw.append(RawStroke(id=s["id"], points=pts, bbox=bbox_of(pts)))
    return raw


def group_strokes(raw_strokes: list[RawStroke], proximity_margin: float = 14.0) -> list[StrokeComponent]:
    """
    Merge strokes into components using bounding-box proximity. `margin`
    controls how close two strokes' boxes need to be to count as "the same
    piece of drawing" — small enough that separate shapes several pixels
    apart don't merge, large enough that a shape's outline strokes (drawn
    corner-to-corner in separate pen lifts) do.
    """
    n = len(raw_strokes)
    uf = _UnionFind(n)
    padded = [s.bbox.expanded(proximity_margin) for s in raw_strokes]

    for i in range(n):
        for j in range(i + 1, n):
            if padded[i].overlaps(raw_strokes[j].bbox) or padded[j].overlaps(raw_strokes[i].bbox):
                uf.union(i, j)

    groups: dict[int, list[RawStroke]] = {}
    for i, s in enumerate(raw_strokes):
        root = uf.find(i)
        groups.setdefault(root, []).append(s)

    components: list[StrokeComponent] = []
    for idx, (_, strokes) in enumerate(groups.items()):
        box = bbox_union([s.bbox for s in strokes])
        components.append(StrokeComponent(id=f"component-{idx}", strokes=strokes, bbox=box))
    return components
