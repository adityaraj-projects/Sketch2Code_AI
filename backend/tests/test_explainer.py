import pytest

from app.explainer.pipeline import explain_flowchart
from app.explainer.providers import TextProvider
from app.explainer.prompts import build_prompt
from app.explainer.pseudocode_renderer import program_to_pseudocode
from app.codegen.graph_structurer import GraphEdge, GraphNode, GraphStructurer


class FakeTextProvider(TextProvider):
    def __init__(self, reply: str = "This is a fake explanation."):
        self.reply = reply
        self.last_system_prompt: str | None = None
        self.last_user_prompt: str | None = None
        self.call_count = 0

    def generate(self, system_prompt: str, user_prompt: str, images: list[str] | None = None) -> str:
        self.call_count += 1
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        return self.reply


def _node(id_, type_, text=""):
    return GraphNode(id=id_, type=type_, text=text)


def _edge(id_, a, b, label=None):
    return GraphEdge(id=id_, from_id=a, to_id=b, label=label)


def _sign_checker():
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
    return nodes, edges


def test_pseudocode_renderer_produces_readable_if_else():
    nodes, edges = _sign_checker()
    program = GraphStructurer(nodes, edges).structure()
    text = program_to_pseudocode(program)
    assert "if n > 0:" in text
    assert "else:" in text
    assert "Read n" in text


def test_build_prompt_embeds_pseudocode_and_selects_mode():
    system_prompt, user_prompt = build_prompt("if x > 0:\n    y = 1", "interview")
    assert "interview" in system_prompt.lower()
    assert "if x > 0:" in user_prompt


@pytest.mark.parametrize("mode", ["simple", "line_by_line", "interview"])
def test_explain_flowchart_calls_provider_with_correct_mode(mode):
    nodes, edges = _sign_checker()
    provider = FakeTextProvider(reply="explanation text")
    result = explain_flowchart(
        [n.__dict__ for n in nodes],
        [{"id": e.id, "fromNodeId": e.from_id, "toNodeId": e.to_id, "label": e.label} for e in edges],
        mode,
        provider,
    )
    assert provider.call_count == 1
    assert result.explanation == "explanation text"
    assert "n > 0" in result.pseudocode


def test_explain_flowchart_handles_empty_diagram_without_calling_provider():
    provider = FakeTextProvider()
    result = explain_flowchart([], [], "simple", provider)
    assert provider.call_count == 0
    assert "start" in result.explanation.lower() or "flowchart" in result.explanation.lower()


def test_explain_flowchart_includes_loop_structure_in_pseudocode():
    nodes = [
        {"id": "start", "type": "start", "text": "Start"},
        {"id": "init", "type": "process", "text": "i = 0"},
        {"id": "dec", "type": "decision", "text": "i < 5"},
        {"id": "body", "type": "process", "text": "i = i + 1"},
        {"id": "end", "type": "end", "text": "End"},
    ]
    edges = [
        {"id": "e1", "fromNodeId": "start", "toNodeId": "init"},
        {"id": "e2", "fromNodeId": "init", "toNodeId": "dec"},
        {"id": "e3", "fromNodeId": "dec", "toNodeId": "body", "label": "yes"},
        {"id": "e4", "fromNodeId": "body", "toNodeId": "dec"},
        {"id": "e5", "fromNodeId": "dec", "toNodeId": "end", "label": "no"},
    ]
    provider = FakeTextProvider()
    result = explain_flowchart(nodes, edges, "simple", provider)
    assert "while i < 5:" in result.pseudocode
