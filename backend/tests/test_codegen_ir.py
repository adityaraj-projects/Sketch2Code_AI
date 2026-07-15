from app.codegen.expression_parser import parse_expression
from app.codegen.graph_structurer import GraphEdge, GraphNode, GraphStructurer
from app.codegen.ir import Assignment, BinOp, If, Input, Output, While
from app.codegen.pseudocode_parser import parse_condition, parse_statement
from app.codegen.type_inference import infer_types


def test_expression_parser_precedence():
    expr = parse_expression("a + b * c")
    assert isinstance(expr, BinOp) and expr.op == "+"
    assert isinstance(expr.right, BinOp) and expr.right.op == "*"


def test_expression_parser_comparison_and_parens():
    expr = parse_expression("(a + b) > 10")
    assert isinstance(expr, BinOp) and expr.op == ">"
    assert isinstance(expr.left, BinOp) and expr.left.op == "+"


def test_expression_parser_logical_words_and_symbols():
    e1 = parse_expression("a > 0 and b > 0")
    e2 = parse_expression("a > 0 && b > 0")
    assert isinstance(e1, BinOp) and e1.op == "and"
    assert isinstance(e2, BinOp) and e2.op == "and"


def test_pseudocode_parser_assignment():
    stmt = parse_statement("total = total + n")
    assert isinstance(stmt, Assignment)
    assert stmt.target == "total"


def test_pseudocode_parser_input():
    stmt = parse_statement("Read n")
    assert isinstance(stmt, Input)
    assert stmt.target == "n"


def test_pseudocode_parser_input_with_prompt_round_trips_correctly():
    # This is exactly the display format ir_to_text.py produces for an
    # Input with a prompt — it must parse back to the same target name,
    # since the execution simulator re-parses node text on every run.
    stmt = parse_statement('Read n ("Enter a number")')
    assert isinstance(stmt, Input)
    assert stmt.target == "n"
    assert stmt.prompt == "Enter a number"


def test_pseudocode_parser_output():
    stmt = parse_statement('Print "Hello"')
    assert isinstance(stmt, Output)


def test_pseudocode_parser_does_not_confuse_comparison_with_assignment():
    stmt = parse_statement("n >= 0")
    # No single top-level '=' -> should not be treated as an assignment.
    assert not isinstance(stmt, Assignment)


def test_condition_strips_trailing_question_mark():
    expr = parse_condition("n > 0?")
    assert isinstance(expr, BinOp) and expr.op == ">"


# --- graph structuring -----------------------------------------------------

def _node(id_, type_, text=""):
    return GraphNode(id=id_, type=type_, text=text)


def _edge(id_, a, b, label=None):
    return GraphEdge(id=id_, from_id=a, to_id=b, label=label)


def test_structures_simple_if_else():
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
    program = GraphStructurer(nodes, edges).structure()
    # input, if/else, (end merges as both branches independently return)
    assert isinstance(program.body[0], Input)
    if_stmt = program.body[1]
    assert isinstance(if_stmt, If)
    assert len(if_stmt.then_body) >= 1
    assert len(if_stmt.else_body) >= 1


def test_structures_while_loop_from_back_edge():
    nodes = [
        _node("start", "start"),
        _node("init", "process", "i = 0"),
        _node("dec", "decision", "i < 5"),
        _node("body", "process", "i = i + 1"),
        _node("after", "process", 'Print "done"'),
        _node("end", "end"),
    ]
    edges = [
        _edge("e1", "start", "init"),
        _edge("e2", "init", "dec"),
        _edge("e3", "dec", "body", label="yes"),
        _edge("e4", "body", "dec"),  # back edge -> loop
        _edge("e5", "dec", "after", label="no"),
        _edge("e6", "after", "end"),
    ]
    program = GraphStructurer(nodes, edges).structure()
    types = [type(s).__name__ for s in program.body]
    assert "While" in types
    while_stmt = next(s for s in program.body if isinstance(s, While))
    assert any(isinstance(s, Assignment) for s in while_stmt.body)
    # statement after the loop should still be present
    assert any(isinstance(s, Output) for s in program.body)


def test_type_inference_widens_int_and_float():
    nodes = [
        _node("start", "start"),
        _node("a", "process", "x = 5"),
        _node("b", "process", "x = 2.5"),
        _node("end", "end"),
    ]
    edges = [_edge("e1", "start", "a"), _edge("e2", "a", "b"), _edge("e3", "b", "end")]
    program = GraphStructurer(nodes, edges).structure()
    program = infer_types(program)
    assert program.variable_types["x"] == "float"


def test_input_defaults_to_int_type():
    nodes = [_node("start", "start"), _node("in", "input", "Read age"), _node("end", "end")]
    edges = [_edge("e1", "start", "in"), _edge("e2", "in", "end")]
    program = infer_types(GraphStructurer(nodes, edges).structure())
    assert program.variable_types["age"] == "int"
