"""
Real hand-drawn shapes are rarely a single unbroken stroke — a rectangle is
often four separate strokes (one per side) because the pen lifts at
corners. This module treats each stroke as a graph edge between its two
endpoints, clusters nearby endpoints together (the pen doesn't land on the
exact same pixel twice), and looks for a cycle — i.e. a set of strokes that
chain end-to-end back to where they started. That cycle is the shape's
outline. Strokes left over are candidates for text labels.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.recognition.geometry import Point, distance
from app.recognition.grouping import RawStroke, StrokeComponent

ENDPOINT_CLUSTER_RADIUS = 20.0


@dataclass
class OutlineResult:
    outline_points: list[Point]
    outline_stroke_ids: set[str]
    leftover_strokes: list[RawStroke]


def _cluster_endpoints(strokes: list[RawStroke]) -> tuple[list[Point], dict[str, tuple[int, int]]]:
    """Returns cluster centers and, for each stroke id, which cluster its
    (start, end) points belong to."""
    endpoints: list[Point] = []
    owner: list[tuple[str, str]] = []  # (stroke_id, 'start'|'end') per endpoint index

    for s in strokes:
        endpoints.append(s.points[0])
        owner.append((s.id, "start"))
        endpoints.append(s.points[-1])
        owner.append((s.id, "end"))

    cluster_of: list[int] = [-1] * len(endpoints)
    centers: list[Point] = []

    for i, p in enumerate(endpoints):
        matched = -1
        for c_idx, c in enumerate(centers):
            if distance(p, c) <= ENDPOINT_CLUSTER_RADIUS:
                matched = c_idx
                break
        if matched == -1:
            centers.append(p)
            cluster_of[i] = len(centers) - 1
        else:
            cluster_of[i] = matched

    stroke_endpoint_clusters: dict[str, tuple[int, int]] = {}
    for idx in range(0, len(endpoints), 2):
        stroke_id = owner[idx][0]
        stroke_endpoint_clusters[stroke_id] = (cluster_of[idx], cluster_of[idx + 1])

    return centers, stroke_endpoint_clusters


def find_outline(component: StrokeComponent) -> OutlineResult | None:
    strokes = component.strokes

    # Fast path: a single stroke that already returns near its own start.
    if len(strokes) == 1:
        s = strokes[0]
        if distance(s.points[0], s.points[-1]) <= ENDPOINT_CLUSTER_RADIUS * 1.5:
            return OutlineResult(outline_points=s.points, outline_stroke_ids={s.id}, leftover_strokes=[])
        return None

    centers, endpoint_clusters = _cluster_endpoints(strokes)

    # Build adjacency: cluster -> list of (other_cluster, stroke)
    adjacency: dict[int, list[tuple[int, RawStroke]]] = {}
    for s in strokes:
        c1, c2 = endpoint_clusters[s.id]
        adjacency.setdefault(c1, []).append((c2, s))
        adjacency.setdefault(c2, []).append((c1, s))

    # DFS for a cycle, tracking the path of strokes taken.
    best_cycle: list[RawStroke] | None = None

    def dfs(start: int, current: int, visited_strokes: set[str], path: list[RawStroke]):
        nonlocal best_cycle
        if best_cycle is not None:
            return
        for neighbor, stroke in adjacency.get(current, []):
            if stroke.id in visited_strokes:
                continue
            new_path = path + [stroke]
            if neighbor == start and len(new_path) >= 3:
                best_cycle = new_path
                return
            dfs(start, neighbor, visited_strokes | {stroke.id}, new_path)
            if best_cycle is not None:
                return

    for start_cluster in adjacency:
        dfs(start_cluster, start_cluster, set(), [])
        if best_cycle is not None:
            break

    if best_cycle is None:
        return None

    # Chain the cycle's strokes into one ordered polyline, flipping each
    # stroke's point order as needed so consecutive strokes connect head-to-tail.
    ordered_points: list[Point] = list(best_cycle[0].points)
    used_ids = {best_cycle[0].id}
    for stroke in best_cycle[1:]:
        tail = ordered_points[-1]
        if distance(tail, stroke.points[0]) <= distance(tail, stroke.points[-1]):
            ordered_points.extend(stroke.points)
        else:
            ordered_points.extend(reversed(stroke.points))
        used_ids.add(stroke.id)

    leftover = [s for s in strokes if s.id not in used_ids]
    return OutlineResult(outline_points=ordered_points, outline_stroke_ids=used_ids, leftover_strokes=leftover)


@dataclass
class ChainResult:
    points: list[Point]
    stroke_ids: set[str]


def find_open_chain(component: StrokeComponent) -> ChainResult:
    """
    For components that aren't a closed shape (find_outline returned None),
    this chains whichever of its strokes connect end-to-end into the
    longest continuous path — e.g. an arrow shaft drawn as two strokes, or
    a shaft plus a separately-drawn arrowhead. Falls back to the single
    longest stroke if nothing chains.
    """
    strokes = component.strokes
    if len(strokes) == 1:
        return ChainResult(points=strokes[0].points, stroke_ids={strokes[0].id})

    centers, endpoint_clusters = _cluster_endpoints(strokes)
    adjacency: dict[int, list[tuple[int, RawStroke]]] = {}
    for s in strokes:
        c1, c2 = endpoint_clusters[s.id]
        adjacency.setdefault(c1, []).append((c2, s))
        adjacency.setdefault(c2, []).append((c1, s))

    best_points: list[Point] = []
    best_ids: set[str] = set()

    def dfs(current: int, visited: set[str], points: list[Point]):
        nonlocal best_points, best_ids
        if len(points) > len(best_points):
            best_points = points
            best_ids = visited
        for neighbor, stroke in adjacency.get(current, []):
            if stroke.id in visited:
                continue
            tail = points[-1] if points else None
            if tail is not None and distance(tail, stroke.points[0]) > distance(tail, stroke.points[-1]):
                next_points = points + list(reversed(stroke.points))
            else:
                next_points = points + list(stroke.points)
            dfs(neighbor, visited | {stroke.id}, next_points)

    for start_cluster, edges in adjacency.items():
        # Only start from "leaf-ish" clusters (degree 1) so we walk the
        # chain from an actual endpoint rather than the middle.
        if len(edges) == 1:
            neighbor, stroke = edges[0]
            dfs(start_cluster, {stroke.id}, list(stroke.points))

    if not best_points:
        longest = max(strokes, key=lambda s: len(s.points))
        return ChainResult(points=longest.points, stroke_ids={longest.id})

    return ChainResult(points=best_points, stroke_ids=best_ids)
