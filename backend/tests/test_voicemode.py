from app.explainer.providers import TextProvider
from app.voicemode.pipeline import generate_flowchart_from_speech
from app.voicemode.prompts import build_voice_prompt, strip_code_fences


class FakeTextProvider(TextProvider):
    def __init__(self, replies: list[str]):
        self.replies = replies
        self.call_count = 0
        self.prompts_seen: list[str] = []

    def generate(self, system_prompt: str, user_prompt: str, images: list[str] | None = None) -> str:
        self.prompts_seen.append(user_prompt)
        reply = self.replies[min(self.call_count, len(self.replies) - 1)]
        self.call_count += 1
        return reply


def test_strip_code_fences_removes_markdown_wrapper():
    wrapped = "```python\nx = 1\nprint(x)\n```"
    assert strip_code_fences(wrapped) == "x = 1\nprint(x)"


def test_strip_code_fences_leaves_plain_code_untouched():
    plain = "x = 1\nprint(x)"
    assert strip_code_fences(plain) == plain


def test_build_voice_prompt_embeds_the_description():
    _, user_prompt = build_voice_prompt("a flowchart that checks if a number is even")
    assert "even" in user_prompt


def test_build_voice_prompt_includes_previous_error_on_retry():
    _, user_prompt = build_voice_prompt("some request", previous_error="invalid syntax at line 2")
    assert "invalid syntax at line 2" in user_prompt


def test_successful_generation_produces_a_real_layout():
    code = 'n = int(input("Enter a number: "))\nif n % 2 == 0:\n    print("Even")\nelse:\n    print("Odd")\n'
    provider = FakeTextProvider([code])
    result = generate_flowchart_from_speech("a flowchart that checks even or odd", provider)

    assert result.success is True
    assert provider.call_count == 1
    types = [n.type for n in result.nodes]
    assert "start" in types and "end" in types and "decision" in types


def test_retries_once_on_syntax_error_and_succeeds_on_second_attempt():
    bad_code = "if x > :\n    print(oops"
    good_code = 'x = int(input("Enter x: "))\nprint(x)\n'
    provider = FakeTextProvider([bad_code, good_code])

    result = generate_flowchart_from_speech("something", provider)

    assert result.success is True
    assert provider.call_count == 2
    assert "syntax error" in provider.prompts_seen[1].lower()


def test_gives_up_after_max_attempts_with_a_clear_error_not_a_crash():
    bad_code = "if x > :\n    print(oops"
    provider = FakeTextProvider([bad_code, bad_code])

    result = generate_flowchart_from_speech("something unparseable", provider)

    assert result.success is False
    assert result.error_message is not None
    assert result.nodes == []
    assert provider.call_count == 2
