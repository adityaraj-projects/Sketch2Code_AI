"""
Geometry primitives for the sketch recognition pipeline.

Deliberately dependency-free (no numpy) so the pipeline stays easy to
install and unit test. Everything operates on flat point lists
[x0, y0, x1, y1, ...] to match how strokes are stored on the canvas.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


Point = tuple[float, float]


def to_points(flat: list[float]) -> list[Point]:
    return [(flat[i], flat[i + 1]) for i in range(0, len(flat) - 1, 2)]


def flatten(points: list[Point]) -> list[float]:
    flat: list[float] = []
    for x, y in points:
        flat.extend([x, y])
    return flat


def distance(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def path_length(points: list[Point]) -> float:
    return sum(distance(points[i], points[i + 1]) for i in range(len(points) - 1))


@dataclass(frozen=True)
class BBox:
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y

    @property
    def area(self) -> float:
        return max(self.width, 1e-6) * max(self.height, 1e-6)

    @property
    def center(self) -> Point:
        return (self.min_x + self.width / 2, self.min_y + self.height / 2)

    @property
    def diagonal(self) -> float:
        return math.hypot(self.width, self.height)

    def expanded(self, margin: float) -> "BBox":
        return BBox(self.min_x - margin, self.min_y - margin, self.max_x + margin, self.max_y + margin)

    def overlaps(self, other: "BBox") -> bool:
        return not (
            self.max_x < other.min_x
            or other.max_x < self.min_x
            or self.max_y < other.min_y
            or other.max_y < self.min_y
        )

    def contains_point(self, p: Point, margin: float = 0.0) -> bool:
        return (
            self.min_x - margin <= p[0] <= self.max_x + margin
            and self.min_y - margin <= p[1] <= self.max_y + margin
        )

    def contains_ratio(self, other: "BBox") -> float:
        """Fraction of `other`'s area that overlaps this box — used to decide
        whether a small stroke (e.g. a letter) sits inside a bigger shape."""
        ix_min = max(self.min_x, other.min_x)
        iy_min = max(self.min_y, other.min_y)
        ix_max = min(self.max_x, other.max_x)
        iy_max = min(self.max_y, other.max_y)
        if ix_max <= ix_min or iy_max <= iy_min:
            return 0.0
        inter_area = (ix_max - ix_min) * (iy_max - iy_min)
        return inter_area / other.area


def bbox_of(points: list[Point]) -> BBox:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return BBox(min(xs), min(ys), max(xs), max(ys))


def bbox_union(boxes: list[BBox]) -> BBox:
    return BBox(
        min(b.min_x for b in boxes),
        min(b.min_y for b in boxes),
        max(b.max_x for b in boxes),
        max(b.max_y for b in boxes),
    )


def polygon_area(points: list[Point]) -> float:
    """Shoelace formula. Points need not be explicitly closed."""
    if len(points) < 3:
        return 0.0
    total = 0.0
    n = len(points)
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


def point_in_polygon(p: Point, polygon: list[Point]) -> bool:
    """Standard ray-casting point-in-polygon test."""
    x, y = p
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        intersects = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def ramer_douglas_peucker(points: list[Point], epsilon: float) -> list[Point]:
    """Simplifies a polyline down to its dominant corner points. This is
    what turns a wobbly hand-drawn edge into a small set of vertices we can
    reason about geometrically (corner count, angles, etc.)."""
    if len(points) < 3:
        return points

    def perpendicular_distance(pt: Point, start: Point, end: Point) -> float:
        if start == end:
            return distance(pt, start)
        x0, y0 = pt
        x1, y1 = start
        x2, y2 = end
        num = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
        den = math.hypot(y2 - y1, x2 - x1)
        return num / den if den else 0.0

    dmax = 0.0
    index = 0
    for i in range(1, len(points) - 1):
        d = perpendicular_distance(points[i], points[0], points[-1])
        if d > dmax:
            index = i
            dmax = d

    if dmax > epsilon:
        left = ramer_douglas_peucker(points[: index + 1], epsilon)
        right = ramer_douglas_peucker(points[index:], epsilon)
        return left[:-1] + right
    return [points[0], points[-1]]


def turning_angle(a: Point, b: Point, c: Point) -> float:
    """Signed turning angle (radians) at vertex b, going a -> b -> c."""
    v1 = (b[0] - a[0], b[1] - a[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    cross = v1[0] * v2[1] - v1[1] * v2[0]
    mag1 = math.hypot(*v1)
    mag2 = math.hypot(*v2)
    if mag1 < 1e-9 or mag2 < 1e-9:
        return 0.0
    cos_theta = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    angle = math.acos(cos_theta)
    return angle if cross >= 0 else -angle


def circularity(points: list[Point]) -> float:
    """Isoperimetric ratio: 1.0 for a perfect circle, lower for elongated
    or angular shapes. Used to separate ovals/connectors from polygons."""
    area = polygon_area(points)
    perimeter = path_length(points + [points[0]])
    if perimeter < 1e-6:
        return 0.0
    return max(0.0, min(1.0, (4 * math.pi * area) / (perimeter**2)))


def is_closed_loop(points: list[Point], closure_ratio: float = 0.22) -> bool:
    """A stroke is 'closed' if its endpoints are close relative to its own
    bounding box diagonal — i.e. the pen came back near where it started."""
    box = bbox_of(points)
    if box.diagonal < 1e-6:
        return False
    return distance(points[0], points[-1]) <= closure_ratio * box.diagonal


def resample_closed_polyline(points: list[Point], n: int) -> list[Point]:
    """Returns `n` points evenly spaced by arc length around a closed loop.
    This lets us compare a hand-drawn shape to an ideal template on equal
    terms, regardless of how many raw points the pen happened to record."""
    closed = points if points[0] == points[-1] else points + [points[0]]
    total_len = path_length(closed)
    if total_len < 1e-6:
        return [points[0]] * n

    step = total_len / n
    resampled: list[Point] = [closed[0]]
    accumulated = 0.0
    seg_index = 0

    while len(resampled) < n and seg_index < len(closed) - 1:
        seg_start = closed[seg_index]
        seg_end = closed[seg_index + 1]
        seg_len = distance(seg_start, seg_end)

        target = len(resampled) * step
        if accumulated + seg_len >= target or seg_index == len(closed) - 2:
            if seg_len < 1e-9:
                resampled.append(seg_end)
            else:
                t = max(0.0, min(1.0, (target - accumulated) / seg_len))
                x = seg_start[0] + (seg_end[0] - seg_start[0]) * t
                y = seg_start[1] + (seg_end[1] - seg_start[1]) * t
                resampled.append((x, y))
        else:
            accumulated += seg_len
            seg_index += 1

    while len(resampled) < n:
        resampled.append(closed[-1])
    return resampled[:n]


def normalize_to_unit_square(points: list[Point], box: BBox) -> list[Point]:
    w = max(box.width, 1e-6)
    h = max(box.height, 1e-6)
    return [((x - box.min_x) / w, (y - box.min_y) / h) for x, y in points]


def average_nearest_distance(a: list[Point], b: list[Point]) -> float:
    """Symmetric point-set similarity: mean distance from each point in `a`
    to its nearest neighbour in `b`, averaged both directions."""

    def one_way(src: list[Point], dst: list[Point]) -> float:
        total = 0.0
        for p in src:
            total += min(distance(p, q) for q in dst)
        return total / len(src)

    return (one_way(a, b) + one_way(b, a)) / 2.0
