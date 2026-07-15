import pytest

from app.chatassistant.intent_router import Intent, classify_intent
from app.chatassistant.language_detector import detect_language
from app.chatassistant.pipeline import handle_chat_message
from app.explainer.providers import TextProvider


class FakeTextProvider(TextProvider):
    def __init__(self, reply: str = "fake reply"):
        self.reply = reply
        self.call_count = 0
        self.last_user_prompt = None

    def generate(self, system_prompt: str, user_prompt: str, images: list[str] | None = None) -> str:
        self.call_count += 1
        self.last_user_prompt = user_prompt
        return self.reply


@pytest.mark.parametrize("message,expected", [
    ("Is there a bug in this flowchart?", Intent.BUG_CHECK),
    ("Something seems wrong here", Intent.BUG_CHECK),
    ("What's the time complexity of this?", Intent.COMPLEXITY),
    ("Can this be made more efficient?", Intent.COMPLEXITY),
    ("Generate code for this", Intent.GENERATE_CODE),
    ("Write the code in Java", Intent.GENERATE_CODE),
    ("Can you clean up this layout?", Intent.BEAUTIFY),
    ("Please tidy up the flowchart", Intent.BEAUTIFY),
    ("Explain what this does", Intent.EXPLAIN),
    ("How does this loop work?", Intent.EXPLAIN),
    ("Hello there", Intent.GENERAL),
])
def test_classify_intent(message, expected):
    assert classify_intent(message) == expected


@pytest.mark.parametrize("message,expected", [
    ("Generate this in Python please", "python"),
    ("Give me the Java code", "java"),
    ("Write it in C++", "cpp"),
    ("write it in c#", "csharp"),
    ("convert to javascript", "javascript"),
    ("give me typescript", "typescript"),
    ("in Go please", "go"),
    ("write rust code", "rust"),
    ("php version please", "php"),
    ("write this in C", "c"),
    ("generate the code", "python"),
])
def test_detect_language(message, expected):
    assert detect_language(message) == expected


def _sign_checker():
    nodes = [
        {"id": "start", "type": "start", "text": "Start"},
        {"id": "in", "type": "input", "text": "Read n"},
        {"id": "dec", "type": "decision", "text": "n > 0"},
        {"id": "t", "type": "process", "text": 'Print "positive"'},
        {"id": "f", "type": "process", "text": 'Print "not positive"'},
        {"id": "end", "type": "end", "text": "End"},
    ]
    edges = [
        {"id": "e1", "fromNodeId": "start", "toNodeId": "in"},
        {"id": "e2", "fromNodeId": "in", "toNodeId": "dec"},
        {"id": "e3", "fromNodeId": "dec", "toNodeId": "t", "label": "yes"},
        {"id": "e4", "fromNodeId": "dec", "toNodeId": "f", "label": "no"},
        {"id": "e5", "fromNodeId": "t", "toNodeId": "end"},
        {"id": "e6", "fromNodeId": "f", "toNodeId": "end"},
    ]
    return nodes, edges


def test_bug_check_routes_to_real_bug_detector_and_finds_nothing_wrong():
    nodes, edges = _sign_checker()
    result = handle_chat_message("any bugs in here?", nodes, edges, provider=None)
    assert result.intent == "bug_check"
    assert "didn't find any" in result.reply.lower()


def test_bug_check_surfaces_a_real_structural_problem():
    nodes = [{"id": "start", "type": "start", "text": "Start"}, {"id": "a", "type": "process", "text": "x = 1"}]
    edges = [{"id": "e1", "fromNodeId": "start", "toNodeId": "a"}]
    result = handle_chat_message("check for bugs", nodes, edges, provider=None)
    assert result.intent == "bug_check"
    assert result.data is not None
    assert len(result.data["findings"]) > 0


def test_complexity_intent_returns_real_big_o():
    nodes, edges = _sign_checker()
    result = handle_chat_message("what's the complexity here?", nodes, edges, provider=None)
    assert result.intent == "complexity"
    assert "O(1)" in result.reply


def test_generate_code_intent_produces_real_python_by_default():
    nodes, edges = _sign_checker()
    result = handle_chat_message("generate code for this", nodes, edges, provider=None)
    assert result.intent == "generate_code"
    assert "def main" in result.reply
    assert result.data["language"] == "python"


def test_generate_code_intent_respects_requested_language():
    nodes, edges = _sign_checker()
    result = handle_chat_message("write this in java please", nodes, edges, provider=None)
    assert result.data["language"] == "java"
    assert "public class Main" in result.reply


def test_beautify_intent_returns_relaid_out_nodes():
    nodes, edges = _sign_checker()
    result = handle_chat_message("clean up this flowchart", nodes, edges, provider=None)
    assert result.intent == "beautify"
    assert result.data is not None
    assert len(result.data["nodes"]) == len(nodes)


def test_explain_without_provider_falls_back_to_pseudocode_not_silence():
    nodes, edges = _sign_checker()
    result = handle_chat_message("explain this to me", nodes, edges, provider=None)
    assert result.intent == "explain"
    assert "if n > 0" in result.reply


def test_explain_with_provider_calls_the_ai_and_returns_its_reply():
    nodes, edges = _sign_checker()
    fake = FakeTextProvider(reply="This checks if a number is positive.")
    result = handle_chat_message("explain this to me", nodes, edges, provider=fake)
    assert result.intent == "explain"
    assert fake.call_count == 1
    assert result.reply == "This checks if a number is positive."


def test_general_without_provider_gives_honest_fallback_not_silence():
    nodes, edges = _sign_checker()
    result = handle_chat_message("hello!", nodes, edges, provider=None)
    assert result.intent == "general"
    assert "AI provider" in result.reply


def test_general_with_provider_is_grounded_in_the_flowchart():
    nodes, edges = _sign_checker()
    fake = FakeTextProvider(reply="Sure, here's my answer.")
    result = handle_chat_message("what would happen if n was 0?", nodes, edges, provider=fake)
    assert result.intent == "general"
    assert fake.call_count == 1
    assert "n > 0" in fake.last_user_prompt
