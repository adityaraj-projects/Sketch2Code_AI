from app.beautifier.pipeline import beautify_flowchart


def _node(id_, type_, text="", x=0, y=0, width=160, height=72):
    return {"id": id_, "type": type_, "text": text, "x": x, "y": y, "width": width, "height": height}


def _edge(id_, a, b, label=None):
    return {"id": id_, "fromNodeId": a, "toNodeId": b, "label": label}


def boxes_overlap(a, b) -> bool:
    return not (
        a.x + a.width <= b.x
        or b.x + b.width <= a.x
        or a.y + a.height <= b.y
        or b.y + b.height <= a.y
    )


def test_beautify_eliminates_overlap_from_a_messy_manual_layout():
    nodes = [
        _node("start", "start", x=10, y=10),
        _node("in", "input", "Read n", x=12, y=11),
        _node("dec", "decision", "n > 0", x=15, y=9),
        _node("t", "process", 'Print "positive"', x=11, y=14),
        _node("f", "process", 'Print "not positive"', x=13, y=12),
        _node("end", "end", x=9, y=13),
    ]
    edges = [
        _edge("e1", "start", "in"),
        _edge("e2", "in", "dec"),
        _edge("e3", "dec", "t", label="yes"),
        _edge("e4", "dec", "f", label="no"),
        _edge("e5", "t", "end"),
        _edge("e6", "f", "end"),
    ]
    result = beautify_flowchart(nodes, edges)

    for i in range(len(result.nodes)):
        for j in range(i + 1, len(result.nodes)):
            assert not boxes_overlap(result.nodes[i], result.nodes[j]), (
                f"{result.nodes[i].id} and {result.nodes[j].id} still overlap after beautify"
            )


def test_beautify_preserves_decision_and_shape_count():
    nodes = [
        _node("start", "start"),
        _node("in", "input", "Read n"),
        _node("dec", "decision", "n > 0"),
        _node("t", "process", 'Print "positive"'),
        _node("f", "process", 'Print "not positive"'),
        _node("end", "end"),
    ]
    edges = [
        _edge("e1", "start", "in"),
        _edge("e2", "in", "dec"),
        _edge("e3", "dec", "t", label="yes"),
        _edge("e4", "dec", "f", label="no"),
        _edge("e5", "t", "end"),
        _edge("e6", "f", "end"),
    ]
    result = beautify_flowchart(nodes, edges)
    decisions = [n for n in result.nodes if n.type == "decision"]
    assert len(decisions) == 1
    assert len(result.nodes) == 6


def test_beautify_normalizes_condition_text_spacing():
    nodes = [
        _node("start", "start"),
        _node("dec", "decision", "n>0"),
        _node("t", "process", "x=1"),
        _node("end", "end"),
    ]
    edges = [_edge("e1", "start", "dec"), _edge("e2", "dec", "t", label="yes"), _edge("e3", "t", "end")]
    result = beautify_flowchart(nodes, edges)
    decision = next(n for n in result.nodes if n.type == "decision")
    assert decision.text == "n > 0"


def test_beautify_is_stable_when_run_again_on_its_own_output():
    nodes = [
        _node("start", "start"),
        _node("dec", "decision", "i < 5"),
        _node("body", "process", "i = i + 1"),
        _node("end", "end"),
    ]
    edges = [
        _edge("e1", "start", "dec"),
        _edge("e2", "dec", "body", label="yes"),
        _edge("e3", "body", "dec"),
        _edge("e4", "dec", "end", label="no"),
    ]
    first_pass = beautify_flowchart(nodes, edges)

    second_input_nodes = [
        {"id": n.id, "type": n.type, "text": n.text, "x": n.x, "y": n.y, "width": n.width, "height": n.height}
        for n in first_pass.nodes
    ]
    second_input_edges = [
        {"id": e.id, "fromNodeId": e.from_id, "toNodeId": e.to_id, "label": e.label} for e in first_pass.edges
    ]
    second_pass = beautify_flowchart(second_input_nodes, second_input_edges)

    assert len(second_pass.nodes) == len(first_pass.nodes)
    assert len(second_pass.edges) == len(first_pass.edges)
    assert any(n.type == "decision" for n in second_pass.nodes)


def test_beautify_reports_warnings_for_unlabeled_branches():
    nodes = [
        _node("start", "start"),
        _node("dec", "decision", "x > 0"),
        _node("a", "process", "a = 1"),
        _node("b", "process", "b = 1"),
        _node("end", "end"),
    ]
    edges = [
        _edge("e1", "start", "dec"),
        _edge("e2", "dec", "a"),
        _edge("e3", "dec", "b"),
        _edge("e4", "a", "end"), _edge("e5", "b", "end"),
    ]
    result = beautify_flowchart(nodes, edges)
    assert any("Yes/No" in w for w in result.warnings)
