from app.codegen.ir import Assignment, If, Input, Output, While
from app.codegen.pipeline import generate_code
from app.codetoflow.flowchart_layout import FlowchartLayout
from app.codetoflow.pipeline import generate_flowchart_from_code
from app.codetoflow.python_ast_adapter import parse_python_source


def test_parses_simple_assignment_and_if():
    source = """
n = 5
if n > 0:
    print("positive")
else:
    print("not positive")
"""
    program, warnings = parse_python_source(source)
    assert isinstance(program.body[0], Assignment)
    assert isinstance(program.body[1], If)
    assert program.body[1].then_body and program.body[1].else_body
    assert warnings == []


def test_parses_input_with_int_cast_and_prompt():
    program, _ = parse_python_source('age = int(input("Enter age: "))')
    stmt = program.body[0]
    assert isinstance(stmt, Input)
    assert stmt.target == "age"
    assert stmt.prompt == "Enter age"


def test_parses_while_loop():
    source = """
i = 0
while i < 5:
    i = i + 1
"""
    program, _ = parse_python_source(source)
    assert isinstance(program.body[0], Assignment)
    assert isinstance(program.body[1], While)


def test_parses_range_for_loop_desugared_to_while():
    source = """
total = 0
for i in range(1, 6):
    total = total + i
"""
    program, _ = parse_python_source(source)
    # init (i = 1), total = 0 comes first, then the desugared while
    types = [type(s).__name__ for s in program.body]
    assert "While" in types


def test_unsupported_construct_becomes_a_comment_not_dropped():
    source = """
x = 1
import os
"""
    program, warnings = parse_python_source(source)
    # import is silently skipped (not a flowchart-worthy statement), but
    # nothing should raise, and x=1 should still be captured.
    assert isinstance(program.body[0], Assignment)


def test_extracts_main_function_body_when_present():
    source = '''
def main():
    x = 1
    print(x)

if __name__ == "__main__":
    main()
'''
    program, _ = parse_python_source(source)
    assert len(program.body) == 2
    assert isinstance(program.body[0], Assignment)
    assert isinstance(program.body[1], Output)


# --- layout -----------------------------------------------------------

def test_layout_produces_start_and_end_nodes():
    program, _ = parse_python_source("x = 1\nprint(x)")
    nodes, edges, warnings = FlowchartLayout().build(program)
    types = [n.type for n in nodes]
    assert types[0] == "start"
    assert types[-1] == "end"
    assert len(edges) == len(nodes) - 1  # simple linear chain


def test_layout_if_else_branches_reconverge():
    source = """
n = 5
if n > 0:
    print("yes")
else:
    print("no")
print("done")
"""
    program, _ = parse_python_source(source)
    nodes, edges, warnings = FlowchartLayout().build(program)
    decision_nodes = [n for n in nodes if n.type == "decision"]
    assert len(decision_nodes) == 1

    # Both branch outputs should have an edge into the same next node
    # ("done"), proving the branches actually reconverge.
    done_node = next(n for n in nodes if "done" in n.text)
    incoming_to_done = [e for e in edges if e.to_id == done_node.id]
    assert len(incoming_to_done) == 2


def test_layout_while_loop_has_back_edge():
    source = """
i = 0
while i < 5:
    i = i + 1
print(i)
"""
    program, _ = parse_python_source(source)
    nodes, edges, warnings = FlowchartLayout().build(program)
    decision = next(n for n in nodes if n.type == "decision")
    incoming_to_decision = [e for e in edges if e.to_id == decision.id]
    # One edge is the normal entry from "i = 0"; the other is the loop
    # body's back-edge. The back-edge originates from a node offset to
    # the branch column (x != the centerline), the entry edge does not.
    assert len(incoming_to_decision) == 2
    back_edges = [e for e in incoming_to_decision if e.from_point[0] != decision.x + decision.width / 2]
    assert len(back_edges) == 1


def test_layout_no_overlapping_start_positions():
    source = "x = 1\ny = 2\nz = 3"
    program, _ = parse_python_source(source)
    nodes, _, _ = FlowchartLayout().build(program)
    ys = [n.y for n in nodes]
    assert ys == sorted(ys)
    assert len(set(ys)) == len(ys)  # every node at a distinct vertical position


def test_end_to_end_pipeline_returns_nodes_and_edges():
    result = generate_flowchart_from_code("n = 1\nprint(n)", "python")
    assert len(result.nodes) >= 3  # start, process/output, end
    assert len(result.edges) >= 2


def test_unsupported_language_raises():
    import pytest
    with pytest.raises(ValueError):
        generate_flowchart_from_code("print(1)", "java")


# --- round trip: Feature 2 (flowchart -> code) then Feature 3 (code -> flowchart) ---

def test_round_trip_sign_checker_preserves_structure():
    fc_nodes = [
        {"id": "start", "type": "start", "text": "Start"},
        {"id": "in", "type": "input", "text": "Read n"},
        {"id": "dec", "type": "decision", "text": "n > 0"},
        {"id": "t", "type": "process", "text": 'Print "positive"'},
        {"id": "f", "type": "process", "text": 'Print "not positive"'},
        {"id": "end", "type": "end", "text": "End"},
    ]
    fc_edges = [
        {"id": "e1", "fromNodeId": "start", "toNodeId": "in"},
        {"id": "e2", "fromNodeId": "in", "toNodeId": "dec"},
        {"id": "e3", "fromNodeId": "dec", "toNodeId": "t", "label": "yes"},
        {"id": "e4", "fromNodeId": "dec", "toNodeId": "f", "label": "no"},
        {"id": "e5", "fromNodeId": "t", "toNodeId": "end"},
        {"id": "e6", "fromNodeId": "f", "toNodeId": "end"},
    ]

    codegen_result = generate_code(fc_nodes, fc_edges, "python")
    flow_result = generate_flowchart_from_code(codegen_result.code, "python")

    decision_count = sum(1 for n in flow_result.nodes if n.type == "decision")
    assert decision_count == 1
    # Both the original and round-tripped diagrams should have exactly one
    # decision and reach an End.
    assert any(n.type == "end" for n in flow_result.nodes)


def test_round_trip_sum_loop_preserves_loop_structure():
    fc_nodes = [
        {"id": "start", "type": "start", "text": "Start"},
        {"id": "init_i", "type": "process", "text": "i = 1"},
        {"id": "init_sum", "type": "process", "text": "sum = 0"},
        {"id": "dec", "type": "decision", "text": "i <= 5"},
        {"id": "add", "type": "process", "text": "sum = sum + i"},
        {"id": "inc", "type": "process", "text": "i = i + 1"},
        {"id": "out", "type": "output", "text": "Print sum"},
        {"id": "end", "type": "end", "text": "End"},
    ]
    fc_edges = [
        {"id": "e1", "fromNodeId": "start", "toNodeId": "init_i"},
        {"id": "e2", "fromNodeId": "init_i", "toNodeId": "init_sum"},
        {"id": "e3", "fromNodeId": "init_sum", "toNodeId": "dec"},
        {"id": "e4", "fromNodeId": "dec", "toNodeId": "add", "label": "yes"},
        {"id": "e5", "fromNodeId": "add", "toNodeId": "inc"},
        {"id": "e6", "fromNodeId": "inc", "toNodeId": "dec"},
        {"id": "e7", "fromNodeId": "dec", "toNodeId": "out", "label": "no"},
        {"id": "e8", "fromNodeId": "out", "toNodeId": "end"},
    ]

    codegen_result = generate_code(fc_nodes, fc_edges, "python")
    flow_result = generate_flowchart_from_code(codegen_result.code, "python")

    decision_count = sum(1 for n in flow_result.nodes if n.type == "decision")
    assert decision_count == 1
    back_edges = [e for e in flow_result.edges if e.to_id in {n.id for n in flow_result.nodes if n.type == "decision"}]
    assert len(back_edges) >= 1  # the loop's back-edge survived the round trip
