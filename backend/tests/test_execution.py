import pytest

from app.codegen.graph_structurer import GraphEdge, GraphNode
from app.execution.evaluator import EvalError, evaluate_expr
from app.execution.interpreter import FlowchartInterpreter
from app.codegen.expression_parser import parse_expression


def ev(text, env=None):
    return evaluate_expr(parse_expression(text), env or {})


def test_arithmetic():
    assert ev("2 + 3 * 4") == 14
    assert ev("(2 + 3) * 4") == 20
    assert ev("10 / 4") == 2.5
    assert ev("10 % 3") == 1


def test_comparisons_and_logic():
    assert ev("3 > 2 and 1 < 2") is True
    assert ev("3 < 2 or 5 == 5") is True
    assert ev("not (3 > 2)") is False


def test_string_concat():
    assert ev('"hi " + "there"') == "hi there"


def test_division_by_zero_raises():
    with pytest.raises(EvalError):
        ev("5 / 0")


def test_floor_division_tokenizes_and_evaluates_correctly():
    assert ev("47 // 10") == 4
    assert ev("n // 10", {"n": 236}) == 23


def test_undefined_variable_raises():
    with pytest.raises(EvalError):
        ev("x + 1")


def test_variable_lookup_works():
    assert ev("x + 1", {"x": 4}) == 5


def test_short_circuit_and_does_not_evaluate_right_side():
    # If short-circuiting weren't implemented, this would raise EvalError
    # on the undefined 'y' — it shouldn't, because the left side is False.
    assert ev("false and (y > 0)".replace("false", "0")) is False


# --- interpreter --------------------------------------------------------

def _node(id_, type_, text=""):
    return GraphNode(id=id_, type=type_, text=text)


def _edge(id_, a, b, label=None):
    return GraphEdge(id=id_, from_id=a, to_id=b, label=label)


def test_runs_simple_sequence_and_tracks_variables():
    nodes = [
        _node("start", "start"),
        _node("a", "process", "x = 5"),
        _node("b", "process", "y = x + 1"),
        _node("end", "end"),
    ]
    edges = [_edge("e1", "start", "a"), _edge("e2", "a", "b"), _edge("e3", "b", "end")]
    result = FlowchartInterpreter(nodes, edges).run()
    assert result.status == "completed"
    assert result.final_variables == {"x": 5, "y": 6}


def test_if_else_takes_correct_branch_based_on_runtime_value():
    nodes = [
        _node("start", "start"),
        _node("in", "process", "n = 10"),
        _node("dec", "decision", "n > 0"),
        _node("t", "process", 'msg = "positive"'),
        _node("f", "process", 'msg = "not positive"'),
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
    result = FlowchartInterpreter(nodes, edges).run()
    assert result.final_variables["msg"] == "positive"
    decision_step = next(s for s in result.steps if s.node_type == "decision")
    assert decision_step.branch_taken == "Yes"


def test_while_loop_runs_correct_number_of_iterations():
    nodes = [
        _node("start", "start"),
        _node("init", "process", "i = 0"),
        _node("dec", "decision", "i < 5"),
        _node("body", "process", "i = i + 1"),
        _node("end", "end"),
    ]
    edges = [
        _edge("e1", "start", "init"),
        _edge("e2", "init", "dec"),
        _edge("e3", "dec", "body", label="yes"),
        _edge("e4", "body", "dec"),
        _edge("e5", "dec", "end", label="no"),
    ]
    result = FlowchartInterpreter(nodes, edges).run()
    assert result.status == "completed"
    assert result.final_variables["i"] == 5
    decision_visits = [s for s in result.steps if s.node_type == "decision"]
    assert len(decision_visits) == 6  # 5 true visits + 1 false to exit


def test_sum_1_to_5_loop_produces_correct_total():
    nodes = [
        _node("start", "start"),
        _node("init_i", "process", "i = 1"),
        _node("init_sum", "process", "sum = 0"),
        _node("dec", "decision", "i <= 5"),
        _node("add", "process", "sum = sum + i"),
        _node("inc", "process", "i = i + 1"),
        _node("out", "process", "Print sum"),
        _node("end", "end"),
    ]
    edges = [
        _edge("e1", "start", "init_i"),
        _edge("e2", "init_i", "init_sum"),
        _edge("e3", "init_sum", "dec"),
        _edge("e4", "dec", "add", label="yes"),
        _edge("e5", "add", "inc"),
        _edge("e6", "inc", "dec"),
        _edge("e7", "dec", "out", label="no"),
        _edge("e8", "out", "end"),
    ]
    result = FlowchartInterpreter(nodes, edges).run()
    assert result.final_variables["sum"] == 15
    assert result.console_output == ["15"]


def test_division_by_zero_halts_with_error_at_correct_node():
    nodes = [
        _node("start", "start"),
        _node("bad", "process", "x = 10 / 0"),
        _node("end", "end"),
    ]
    edges = [_edge("e1", "start", "bad"), _edge("e2", "bad", "end")]
    result = FlowchartInterpreter(nodes, edges).run()
    assert result.status == "error"
    assert result.error_node_id == "bad"
    assert "zero" in result.error_message.lower()


def test_undefined_variable_halts_with_clear_error():
    nodes = [
        _node("start", "start"),
        _node("bad", "process", "y = x + 1"),  # x was never assigned
        _node("end", "end"),
    ]
    edges = [_edge("e1", "start", "bad"), _edge("e2", "bad", "end")]
    result = FlowchartInterpreter(nodes, edges).run()
    assert result.status == "error"
    assert "x" in result.error_message


def test_infinite_loop_is_caught_by_step_limit():
    nodes = [
        _node("start", "start"),
        _node("dec", "decision", "1 == 1"),  # always true, no exit
        _node("body", "process", "x = 1"),
    ]
    edges = [
        _edge("e1", "start", "dec"),
        _edge("e2", "dec", "body", label="yes"),
        _edge("e3", "body", "dec"),
    ]
    result = FlowchartInterpreter(nodes, edges).run()
    assert result.status == "step_limit"


def test_input_values_are_consumed_in_encounter_order():
    nodes = [
        _node("start", "start"),
        _node("in1", "input", "Read a"),
        _node("in2", "input", "Read b"),
        _node("sum", "process", "total = a + b"),
        _node("end", "end"),
    ]
    edges = [
        _edge("e1", "start", "in1"),
        _edge("e2", "in1", "in2"),
        _edge("e3", "in2", "sum"),
        _edge("e4", "sum", "end"),
    ]
    result = FlowchartInterpreter(nodes, edges, input_values=["3", "4"]).run()
    assert result.final_variables["total"] == 7


def test_missing_input_defaults_to_zero_with_warning():
    nodes = [_node("start", "start"), _node("in", "input", "Read n"), _node("end", "end")]
    edges = [_edge("e1", "start", "in"), _edge("e2", "in", "end")]
    result = FlowchartInterpreter(nodes, edges, input_values=[]).run()
    assert result.final_variables["n"] == 0
    assert any("input value" in w.lower() for w in result.warnings)


def test_missing_start_node_reports_error():
    nodes = [_node("only", "process", "x = 1")]
    result = FlowchartInterpreter(nodes, []).run()
    assert result.status == "error"
    assert "start" in result.error_message.lower()
