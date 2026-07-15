from app.codegen.graph_structurer import GraphEdge, GraphNode, GraphStructurer
from app.complexity.analyzer import analyze_complexity
from app.complexity.pipeline import analyze_flowchart_complexity
from app.explainer.providers import TextProvider


def _node(id_, type_, text=""):
    return GraphNode(id=id_, type=type_, text=text)


def _edge(id_, a, b, label=None):
    return GraphEdge(id=id_, from_id=a, to_id=b, label=label)


def _program(nodes, edges):
    return GraphStructurer(nodes, edges).structure()


def test_no_loop_is_constant_time():
    nodes = [_node("start", "start"), _node("a", "process", "x = 1"), _node("end", "end")]
    edges = [_edge("e1", "start", "a"), _edge("e2", "a", "end")]
    result = analyze_complexity(_program(nodes, edges))
    assert result.time_complexity == "O(1)"
    assert result.confidence == "high"


def test_single_linear_loop_is_on():
    nodes = [
        _node("start", "start"),
        _node("init", "process", "i = 0"),
        _node("dec", "decision", "i < n"),
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
    result = analyze_complexity(_program(nodes, edges))
    assert result.time_complexity == "O(n)"
    assert result.confidence == "high"


def test_nested_linear_loops_is_on_squared():
    nodes = [
        _node("start", "start"),
        _node("init_i", "process", "i = 0"),
        _node("dec_i", "decision", "i < n"),
        _node("init_j", "process", "j = 0"),
        _node("dec_j", "decision", "j < n"),
        _node("body_j", "process", "j = j + 1"),
        _node("inc_i", "process", "i = i + 1"),
        _node("end", "end"),
    ]
    edges = [
        _edge("e1", "start", "init_i"),
        _edge("e2", "init_i", "dec_i"),
        _edge("e3", "dec_i", "init_j", label="yes"),
        _edge("e4", "init_j", "dec_j"),
        _edge("e5", "dec_j", "body_j", label="yes"),
        _edge("e6", "body_j", "dec_j"),
        _edge("e7", "dec_j", "inc_i", label="no"),
        _edge("e8", "inc_i", "dec_i"),
        _edge("e9", "dec_i", "end", label="no"),
    ]
    result = analyze_complexity(_program(nodes, edges))
    assert result.time_complexity == "O(n^2)"
    assert any("nested loops" in s.lower() for s in result.suggestions)


def test_halving_loop_is_logarithmic():
    nodes = [
        _node("start", "start"),
        _node("init", "process", "i = n"),
        _node("dec", "decision", "i > 1"),
        _node("body", "process", "i = i / 2"),
        _node("end", "end"),
    ]
    edges = [
        _edge("e1", "start", "init"),
        _edge("e2", "init", "dec"),
        _edge("e3", "dec", "body", label="yes"),
        _edge("e4", "body", "dec"),
        _edge("e5", "dec", "end", label="no"),
    ]
    result = analyze_complexity(_program(nodes, edges))
    assert result.time_complexity == "O(log n)"


def test_if_else_takes_worse_branch_for_worst_case():
    nodes = [
        _node("start", "start"),
        _node("dec_if", "decision", "flag == 1"),
        _node("init", "process", "i = 0"),
        _node("dec", "decision", "i < n"),
        _node("body", "process", "i = i + 1"),
        _node("noop", "process", "x = 1"),
        _node("end", "end"),
    ]
    edges = [
        _edge("e1", "start", "dec_if"),
        _edge("e2", "dec_if", "init", label="yes"),
        _edge("e3", "init", "dec"),
        _edge("e4", "dec", "body", label="yes"),
        _edge("e5", "body", "dec"),
        _edge("e6", "dec", "end", label="no"),
        _edge("e7", "dec_if", "noop", label="no"),
        _edge("e8", "noop", "end"),
    ]
    result = analyze_complexity(_program(nodes, edges))
    assert result.time_complexity == "O(n)"


def test_loop_invariant_computation_flagged_for_hoisting():
    nodes = [
        _node("start", "start"),
        _node("init", "process", "i = 0"),
        _node("dec", "decision", "i < n"),
        _node("invariant", "process", "constant_val = a + b"),
        _node("body", "process", "i = i + 1"),
        _node("end", "end"),
    ]
    edges = [
        _edge("e1", "start", "init"),
        _edge("e2", "init", "dec"),
        _edge("e3", "dec", "invariant", label="yes"),
        _edge("e4", "invariant", "body"),
        _edge("e5", "body", "dec"),
        _edge("e6", "dec", "end", label="no"),
    ]
    result = analyze_complexity(_program(nodes, edges))
    assert any("constant_val" in s for s in result.suggestions)


def test_unrecognized_loop_growth_lowers_confidence():
    nodes = [
        _node("start", "start"),
        _node("dec", "decision", "flag == 0"),
        _node("body", "process", 'flag = "changed"'),
        _node("end", "end"),
    ]
    edges = [
        _edge("e1", "start", "dec"),
        _edge("e2", "dec", "body", label="yes"),
        _edge("e3", "body", "dec"),
        _edge("e4", "dec", "end", label="no"),
    ]
    result = analyze_complexity(_program(nodes, edges))
    assert result.confidence == "estimated"


class FakeTextProvider(TextProvider):
    def __init__(self):
        self.last_user_prompt = None
        self.call_count = 0

    def generate(self, system_prompt: str, user_prompt: str, images: list[str] | None = None) -> str:
        self.call_count += 1
        self.last_user_prompt = user_prompt
        return "fake narrative"


def test_pipeline_includes_narrative_when_provider_given():
    nodes = [_node("start", "start"), _node("a", "process", "x = 1"), _node("end", "end")]
    edges = [_edge("e1", "start", "a"), _edge("e2", "a", "end")]
    fake = FakeTextProvider()
    output = analyze_flowchart_complexity(
        [n.__dict__ for n in nodes],
        [{"id": e.id, "fromNodeId": e.from_id, "toNodeId": e.to_id, "label": e.label} for e in edges],
        narrative_provider=fake,
    )
    assert fake.call_count == 1
    assert output.narrative == "fake narrative"
    assert "O(1)" in fake.last_user_prompt


def test_pipeline_works_without_narrative_provider():
    nodes = [_node("start", "start"), _node("a", "process", "x = 1"), _node("end", "end")]
    edges = [_edge("e1", "start", "a"), _edge("e2", "a", "end")]
    output = analyze_flowchart_complexity(
        [n.__dict__ for n in nodes],
        [{"id": e.id, "fromNodeId": e.from_id, "toNodeId": e.to_id, "label": e.label} for e in edges],
        narrative_provider=None,
    )
    assert output.narrative is None
    assert output.result.time_complexity == "O(1)"
