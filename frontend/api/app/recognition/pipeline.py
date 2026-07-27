"""
Top-level orchestration for Feature 1 (AI Flowchart Recognition).

Pipeline stages, each in its own module so later features (execution
simulator, bug detector) can reuse individual pieces:

  1. grouping        — cluster raw strokes into spatial components
  2. outline_chaining — find closed-loop outlines (shapes) within a component,
                        or the longest open chain (candidate arrows)
  3. shape_classifier — template-match a closed outline to a symbol type
  4. arrow_detector   — validate arrow-shaped strokes and resolve endpoints
                        to the nodes they connect, with direction
  5. label_ocr        — crop + transcribe handwritten text inside each shape
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.recognition.arrow_detector import detect_arrow
from app.recognition.geometry import BBox, bbox_of, is_closed_loop
from app.recognition.grouping import RawStroke, StrokeComponent, build_raw_strokes, group_strokes
from app.recognition.label_ocr import SnapshotContext, crop_node_png_bytes, decode_snapshot
from app.recognition.outline_chaining import find_open_chain, find_outline
from app.recognition.shape_classifier import classify_outline
from app.recognition.vision_providers import VisionProvider, VisionProviderError

# Only these tools represent structural ink; highlighter is decorative and
# eraser strokes never reach the backend (they remove ink client-side).
RECOGNIZABLE_TOOLS = {"pen"}

TEMPLATE_TO_NODE_TYPE = {
    "rectangle": "process",
    "diamond": "decision",
    "parallelogram": "input",
}

CONNECTOR_AREA_RATIO = 0.4


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


@dataclass
class _RecognizedNode:
    id: str
    node_type: str
    bbox: BBox
    label_strokes: list[RawStroke]
    text: str = ""


@dataclass
class _RecognizedEdge:
    id: str
    from_node_id: str
    to_node_id: str
    points: list[tuple[float, float]]


@dataclass
class PipelineResult:
    nodes: list[_RecognizedNode]
    edges: list[_RecognizedEdge]
    consumed_stroke_ids: set[str]
    unrecognized_stroke_ids: set[str]
    ocr_warning: str | None = None


def _label_strokes_inside(node_bbox: BBox, unclaimed: list[RawStroke], containment_ratio: float = 0.7) -> list[RawStroke]:
    claimed = []
    for s in unclaimed:
        if node_bbox.contains_ratio(s.bbox) >= containment_ratio:
            claimed.append(s)
    return claimed


def run_recognition_pipeline(
    strokes_data: list[dict],
    vision_provider: VisionProvider | None = None,
    snapshot: SnapshotContext | None = None,
) -> PipelineResult:
    all_raw = build_raw_strokes([s for s in strokes_data if s.get("tool") in RECOGNIZABLE_TOOLS])

    nodes: list[_RecognizedNode] = []
    consumed_ids: set[str] = set()

    # Pass 1a: a stroke that closes on its own (pen returns near its start
    # point) is almost certainly a complete shape by itself. We pull these
    # out *before* proximity grouping runs, so a connecting arrow that
    # happens to touch a shape's border can't bridge two separate shapes
    # into one bogus component.
    self_closed = [s for s in all_raw if is_closed_loop(s.points)]
    non_shape_strokes = [s for s in all_raw if s not in self_closed]

    for s in self_closed:
        candidate = classify_outline(s.points)
        if candidate is not None:
            node_type = "start" if candidate.template == "ellipse" else TEMPLATE_TO_NODE_TYPE[candidate.template]
            nodes.append(_RecognizedNode(id=_new_id(), node_type=node_type, bbox=candidate.bbox, label_strokes=[]))
            consumed_ids.add(s.id)
        else:
            # Closed loop but didn't match any known symbol (e.g. a circled
            # label) — leave it for the label/arrow passes instead of
            # forcing a guess.
            non_shape_strokes.append(s)

    # Pass 1b: shapes drawn as several pen-lift strokes (e.g. a rectangle
    # drawn as four separate sides) still need proximity grouping + cycle
    # chaining to close, but now only among strokes that aren't already
    # known to be complete shapes on their own.
    remaining_components: list[StrokeComponent] = []
    for component in group_strokes(non_shape_strokes):
        outline = find_outline(component)
        if outline is not None:
            candidate = classify_outline(outline.outline_points)
            if candidate is not None:
                node_type = (
                    "start" if candidate.template == "ellipse" else TEMPLATE_TO_NODE_TYPE[candidate.template]
                )
                node = _RecognizedNode(
                    id=_new_id(),
                    node_type=node_type,
                    bbox=candidate.bbox,
                    label_strokes=list(outline.leftover_strokes),
                )
                nodes.append(node)
                consumed_ids.update(outline.outline_stroke_ids)
                consumed_ids.update(s.id for s in outline.leftover_strokes)
                continue
        remaining_components.append(component)

    # Pass 2: any stroke from a non-shape component that sits mostly inside
    # a recognized shape is a label, not a stray line — claim it before
    # arrow detection sees it.
    still_remaining: list[StrokeComponent] = []
    for component in remaining_components:
        unclaimed = list(component.strokes)
        for node in nodes:
            found = _label_strokes_inside(node.bbox, unclaimed)
            if found:
                node.label_strokes.extend(found)
                consumed_ids.update(s.id for s in found)
                unclaimed = [s for s in unclaimed if s not in found]
        if unclaimed:
            still_remaining.append(StrokeComponent(id=component.id, strokes=unclaimed, bbox=bbox_of(
                [p for s in unclaimed for p in s.points]
            )))

    # Pass 3: whatever's left is either an arrow or unrecognized ink.
    node_boxes = [n.bbox for n in nodes]
    edges: list[_RecognizedEdge] = []
    unrecognized_ids: set[str] = set()

    for component in still_remaining:
        chain = find_open_chain(component)
        arrow = None
        # Try the full chained path first (handles multi-stroke arrows),
        # then fall back to each individual stroke.
        dummy_stroke = RawStroke(id="__chain__", points=chain.points, bbox=bbox_of(chain.points))
        arrow = detect_arrow(dummy_stroke, node_boxes)

        if arrow is None:
            for s in component.strokes:
                arrow = detect_arrow(s, node_boxes)
                if arrow is not None:
                    consumed_ids.add(s.id)
                    break
        else:
            consumed_ids.update(chain.stroke_ids)

        if arrow is not None and arrow.from_node_index is not None and arrow.to_node_index is not None and arrow.from_node_index != arrow.to_node_index:
            from_node = nodes[arrow.from_node_index]
            to_node = nodes[arrow.to_node_index]
            edges.append(
                _RecognizedEdge(
                    id=_new_id(),
                    from_node_id=from_node.id,
                    to_node_id=to_node.id,
                    points=[from_node.bbox.center, to_node.bbox.center],
                )
            )
        else:
            unrecognized_ids.update(s.id for s in component.strokes)

    # Pass 4: resolve ambiguous ellipses (start/end vs connector) using
    # relative size, and start-vs-end using arrow connectivity.
    non_ellipse_areas = [n.bbox.area for n in nodes if n.node_type != "start"]
    reference_area = (
        sum(non_ellipse_areas) / len(non_ellipse_areas)
        if non_ellipse_areas
        else (sum(n.bbox.area for n in nodes) / len(nodes) if nodes else 0)
    )
    in_degree = {n.id: 0 for n in nodes}
    out_degree = {n.id: 0 for n in nodes}
    for e in edges:
        out_degree[e.from_node_id] += 1
        in_degree[e.to_node_id] += 1

    for node in nodes:
        if node.node_type != "start":
            continue
        if reference_area > 0 and node.bbox.area < CONNECTOR_AREA_RATIO * reference_area:
            node.node_type = "connector"
        elif in_degree[node.id] > 0 and out_degree[node.id] == 0:
            node.node_type = "end"
        else:
            node.node_type = "start"

    # Pass 5: OCR handwritten labels, if we have both a vision provider and
    # a rendered snapshot to crop from.
    ocr_warning: str | None = None
    if snapshot is not None and vision_provider is not None:
        for node in nodes:
            if not node.label_strokes:
                continue
            crop_bytes = crop_node_png_bytes(snapshot, node.bbox)
            if crop_bytes is None:
                continue
            try:
                node.text = vision_provider.transcribe_handwriting(crop_bytes)
            except VisionProviderError as e:
                ocr_warning = str(e)
                break
            except Exception as e:  # network/API errors from the provider itself
                ocr_warning = f"Label recognition failed: {e}"
                break
    elif any(n.label_strokes for n in nodes):
        ocr_warning = (
            "Shapes were recognized but handwritten labels weren't transcribed — "
            "configure AI_PROVIDER and an API key in .env, and make sure the "
            "frontend sends a canvas snapshot."
        )

    return PipelineResult(
        nodes=nodes,
        edges=edges,
        consumed_stroke_ids=consumed_ids,
        unrecognized_stroke_ids=unrecognized_ids,
        ocr_warning=ocr_warning,
    )
