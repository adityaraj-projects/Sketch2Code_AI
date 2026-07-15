from app.bugdetector.detector import detect_bugs
from app.codegen.graph_structurer import GraphEdge, GraphNode


def _node(id_, type_, text=""):
    return GraphNode(id=id_, type=type_, text=text)


def _edge(id_, a, b, label=None):
    return GraphEdge(id=id_, from_id=a, to_id=b, label=label)


def categories(findings):
    return [f.category for f in findings]


def test_valid_flowchart_has_no_errors():
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
    findings = detect_bugs(nodes, edges)
    errors = [f for f in findings if f.severity == "error"]
    assert errors == []


def test_missing_start_is_flagged():
    nodes = [_node("a", "process", "x = 1"), _node("end", "end")]
    edges = [_edge("e1", "a", "end")]
    findings = detect_bugs(nodes, edges)
    assert "structure" in categories(findings)
    assert any("no Start" in f.message for f in findings)


def test_missing_end_is_flagged_as_warning():
    nodes = [_node("start", "start"), _node("a", "process", "x = 1")]
    edges = [_edge("e1", "start", "a")]
    findings = detect_bugs(nodes, edges)
    struct_findings = [f for f in findings if f.category == "structure" and "End" in f.message]
    assert struct_findings
    assert struct_findings[0].severity == "warning"


def test_dead_end_process_node_flagged_as_missing_arrow():
    nodes = [_node("start", "start"), _node("a", "process", "x = 1"), _node("end", "end")]
    edges = [_edge("e1", "start", "a")]
    findings = detect_bugs(nodes, edges)
    missing_arrow = [f for f in findings if f.category == "missing_arrow" and "a" in f.node_ids]
    assert missing_arrow
    assert missing_arrow[0].severity == "error"


def test_disconnected_node_flagged():
    nodes = [
        _node("start", "start"),
        _node("a", "process", "x = 1"),
        _node("orphan", "process", "y = 2"),
        _node("end", "end"),
    ]
    edges = [_edge("e1", "start", "a"), _edge("e2", "a", "end")]
    findings = detect_bugs(nodes, edges)
    disconnected = [f for f in findings if f.category == "disconnected_node" and "orphan" in f.node_ids]
    assert disconnected
    assert disconnected[0].severity == "warning"


def test_decision_with_one_output_is_error():
    nodes = [
        _node("start", "start"),
        _node("dec", "decision", "n > 0"),
        _node("t", "process", "x = 1"),
        _node("end", "end"),
    ]
    edges = [_edge("e1", "start", "dec"), _edge("e2", "dec", "t"), _edge("e3", "t", "end")]
    findings = detect_bugs(nodes, edges)
    invalid = [f for f in findings if f.category == "invalid_decision" and f.severity == "error"]
    assert invalid
    assert "one outgoing connector" in invalid[0].message


def test_decision_with_three_outputs_is_warning():
    nodes = [
        _node("start", "start"),
        _node("dec", "decision", "x"),
        _node("a", "process", "a = 1"),
        _node("b", "process", "b = 1"),
        _node("c", "process", "c = 1"),
        _node("end", "end"),
    ]
    edges = [
        _edge("e1", "start", "dec"),
        _edge("e2", "dec", "a", label="yes"),
        _edge("e3", "dec", "b", label="no"),
        _edge("e4", "dec", "c"),
        _edge("e5", "a", "end"), _edge("e6", "b", "end"), _edge("e7", "c", "end"),
    ]
    findings = detect_bugs(nodes, edges)
    assert any(f.category == "invalid_decision" and "3 outgoing" in f.message for f in findings)


def test_decision_both_branches_same_target_flagged():
    nodes = [
        _node("start", "start"),
        _node("dec", "decision", "x"),
        _node("a", "process", "a = 1"),
        _node("end", "end"),
    ]
    edges = [
        _edge("e1", "start", "dec"),
        _edge("e2", "dec", "a", label="yes"),
        _edge("e3", "dec", "a", label="no"),
        _edge("e4", "a", "end"),
    ]
    findings = detect_bugs(nodes, edges)
    assert any("no effect" in f.message for f in findings)


def test_unlabeled_decision_branches_produce_warning():
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
    findings = detect_bugs(nodes, edges)
    assert any("Yes/No labeled" in f.message for f in findings)


def test_infinite_loop_detected_when_no_exit_reaches_end():
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
        _edge("e4", "dec", "body", label="no"),
    ]
    findings = detect_bugs(nodes, edges)
    infinite = [f for f in findings if f.category == "infinite_loop"]
    assert infinite
    assert infinite[0].severity == "error"
    assert "dec" in infinite[0].node_ids
    assert "body" in infinite[0].node_ids


def test_self_loop_node_is_caught_by_infinite_loop_check():
    nodes = [_node("start", "start"), _node("a", "process", "x = 1"), _node("end", "end")]
    edges = [_edge("e1", "start", "a"), _edge("e2", "a", "a")]
    findings = detect_bugs(nodes, edges)
    assert any(f.category == "infinite_loop" for f in findings)


def test_start_with_multiple_outputs_flagged():
    nodes = [
        _node("start", "start"),
        _node("a", "process", "a = 1"),
        _node("b", "process", "b = 1"),
        _node("end", "end"),
    ]
    edges = [
        _edge("e1", "start", "a"),
        _edge("e2", "start", "b"),
        _edge("e3", "a", "end"), _edge("e4", "b", "end"),
    ]
    findings = detect_bugs(nodes, edges)
    assert any(f.category == "structure" and "Start" in f.message and "more than one" in f.message for f in findings)


def test_end_with_outgoing_edge_flagged():
    nodes = [_node("start", "start"), _node("end", "end"), _node("a", "process", "x = 1")]
    edges = [_edge("e1", "start", "end"), _edge("e2", "end", "a")]
    findings = detect_bugs(nodes, edges)
    assert any(f.category == "structure" and "End shape has an outgoing" in f.message for f in findings)
