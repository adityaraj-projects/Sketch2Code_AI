"""
Tests the recognition pipeline against synthetic hand-drawn-style stroke
data. Coordinates are jittered slightly to mimic real pen input rather than
testing against mathematically perfect shapes only.
"""
import math
import random

from app.recognition.pipeline import run_recognition_pipeline
from app.recognition.vision_providers import VisionProvider

random.seed(7)


def jitter(points, amount=1.5):
    return [(x + random.uniform(-amount, amount), y + random.uniform(-amount, amount)) for x, y in points]


def densify(p1, p2, n=6):
    return [(p1[0] + (p2[0] - p1[0]) * i / n, p1[1] + (p2[1] - p1[1]) * i / n) for i in range(n + 1)]


def rectangle_points(x, y, w, h):
    corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
    pts = []
    for i in range(len(corners) - 1):
        pts.extend(densify(corners[i], corners[i + 1]))
    return jitter(pts)


def diamond_points(x, y, w, h):
    cx, cy = x + w / 2, y + h / 2
    corners = [(cx, y), (x + w, cy), (cx, y + h), (x, cy), (cx, y)]
    pts = []
    for i in range(len(corners) - 1):
        pts.extend(densify(corners[i], corners[i + 1]))
    return jitter(pts)


def parallelogram_points(x, y, w, h):
    skew = w * 0.2
    corners = [(x + skew, y), (x + w, y), (x + w - skew, y + h), (x, y + h), (x + skew, y)]
    pts = []
    for i in range(len(corners) - 1):
        pts.extend(densify(corners[i], corners[i + 1]))
    return jitter(pts)


def oval_points(x, y, w, h, n=28):
    cx, cy = x + w / 2, y + h / 2
    pts = [
        (cx + (w / 2) * math.cos(2 * math.pi * i / n), cy + (h / 2) * math.sin(2 * math.pi * i / n))
        for i in range(n + 1)
    ]
    return jitter(pts, amount=1.0)


def stroke(id_, points, tool="pen"):
    flat = []
    for x, y in points:
        flat.extend([x, y])
    return {
        "id": id_,
        "tool": tool,
        "points": flat,
        "pressures": [0.5] * len(points),
        "color": "#EDEBE6",
        "width": 3,
    }


def flat_points(pts):
    flat = []
    for x, y in pts:
        flat.extend([x, y])
    return flat


class FakeVisionProvider(VisionProvider):
    """Deterministic stand-in used only in tests, so pipeline logic can be
    verified without a real network call or API key."""

    def __init__(self, text_by_call=None):
        self.calls = 0
        self._texts = text_by_call or []

    def transcribe_handwriting(self, image_png_bytes: bytes) -> str:
        text = self._texts[self.calls] if self.calls < len(self._texts) else "Process"
        self.calls += 1
        return text


def test_recognizes_rectangle_as_process():
    strokes = [stroke("s1", rectangle_points(100, 100, 160, 80))]
    result = run_recognition_pipeline(strokes)
    assert len(result.nodes) == 1
    assert result.nodes[0].node_type == "process"
    assert "s1" in result.consumed_stroke_ids


def test_recognizes_diamond_as_decision():
    strokes = [stroke("s1", diamond_points(0, 0, 180, 120))]
    result = run_recognition_pipeline(strokes)
    assert len(result.nodes) == 1
    assert result.nodes[0].node_type == "decision"


def test_recognizes_parallelogram_as_input():
    strokes = [stroke("s1", parallelogram_points(0, 0, 180, 90))]
    result = run_recognition_pipeline(strokes)
    assert len(result.nodes) == 1
    assert result.nodes[0].node_type == "input"


def test_recognizes_oval_as_start_when_alone():
    strokes = [stroke("s1", oval_points(0, 0, 150, 80))]
    result = run_recognition_pipeline(strokes)
    assert len(result.nodes) == 1
    assert result.nodes[0].node_type == "start"


def test_small_circle_among_larger_shapes_becomes_connector():
    strokes = [
        stroke("rect1", rectangle_points(0, 0, 160, 80)),
        stroke("rect2", rectangle_points(400, 0, 160, 80)),
        stroke("circle1", oval_points(200, 20, 40, 40)),  # much smaller than the rectangles
    ]
    result = run_recognition_pipeline(strokes)
    types = {n.node_type for n in result.nodes}
    assert "connector" in types


def test_multi_stroke_rectangle_closes_via_outline_chaining():
    # Same rectangle, but drawn as four separate pen-lift strokes like a
    # real hand-drawn shape, instead of one continuous stroke.
    x, y, w, h = 50, 50, 150, 90
    top = stroke("top", densify((x, y), (x + w, y)))
    right = stroke("right", densify((x + w, y), (x + w, y + h)))
    bottom = stroke("bottom", densify((x + w, y + h), (x, y + h)))
    left = stroke("left", densify((x, y + h), (x, y)))
    result = run_recognition_pipeline([top, right, bottom, left])
    assert len(result.nodes) == 1
    assert result.nodes[0].node_type == "process"
    assert {"top", "right", "bottom", "left"} <= result.consumed_stroke_ids


def test_detects_arrow_between_two_recognized_shapes():
    rect1 = stroke("rect1", rectangle_points(0, 0, 140, 70))
    rect2 = stroke("rect2", rectangle_points(0, 220, 140, 70))
    # Arrow drawn downward from the bottom of rect1 to the top of rect2.
    arrow_pts = densify((70, 70), (70, 220), n=10)
    arrow = stroke("arrow1", arrow_pts)

    result = run_recognition_pipeline([rect1, rect2, arrow])
    assert len(result.nodes) == 2
    assert len(result.edges) == 1
    edge = result.edges[0]
    from_node = next(n for n in result.nodes if n.id == edge.from_node_id)
    to_node = next(n for n in result.nodes if n.id == edge.to_node_id)
    # Arrow was drawn from the top rectangle down to the bottom one.
    assert from_node.bbox.min_y < to_node.bbox.min_y


def test_unrecognized_scribble_is_left_alone():
    scribble_pts = [(0, 0), (5, 30), (-10, 15), (20, 5), (3, 40), (25, 22)]
    strokes = [stroke("scribble", scribble_pts)]
    result = run_recognition_pipeline(strokes)
    assert len(result.nodes) == 0
    assert "scribble" not in result.consumed_stroke_ids


def test_label_inside_shape_is_transcribed_via_vision_provider():
    from app.recognition.label_ocr import SnapshotContext
    from PIL import Image

    rect = stroke("rect1", rectangle_points(0, 0, 200, 120))
    # A small scribble sitting well inside the rectangle - the "handwriting".
    label_pts = [(70, 40), (90, 60), (110, 45), (130, 55)]
    label = stroke("label1", label_pts)

    fake_image = Image.new("RGB", (400, 300), color="black")
    snapshot = SnapshotContext(image=fake_image, viewport_x=0, viewport_y=0, viewport_zoom=1, pixel_ratio=1)
    provider = FakeVisionProvider(text_by_call=["Check age"])

    result = run_recognition_pipeline([rect, label], vision_provider=provider, snapshot=snapshot)

    assert len(result.nodes) == 1
    assert result.nodes[0].text == "Check age"
    assert provider.calls == 1
    assert "label1" in result.consumed_stroke_ids


def test_ocr_skipped_gracefully_without_provider_but_shape_still_recognized():
    rect = stroke("rect1", rectangle_points(0, 0, 200, 120))
    label = stroke("label1", [(70, 40), (90, 60), (110, 45)])

    result = run_recognition_pipeline([rect, label])  # no provider, no snapshot

    assert len(result.nodes) == 1
    assert result.nodes[0].text == ""
    assert result.ocr_warning is not None
