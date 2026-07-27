"""
Natural-language explanation genuinely needs an LLM — there's no honest
deterministic substitute for "explain this in plain English" the way
there was for shape recognition or code generation. This wraps whichever
provider is configured behind one interface, same pattern as
app.recognition.vision_providers: requires the operator's own API key in
.env, and raises a clear error rather than returning fake text when one
isn't configured.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.config import settings


class TextProviderError(RuntimeError):
    pass


class TextProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, images: list[str] | None = None) -> str:
        raise NotImplementedError


class GeminiTextProvider(TextProvider):
    def __init__(self, api_key: str, model: str = "gemini-3.5-flash"):
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self._genai = genai
        self._model_name = model

    def generate(self, system_prompt: str, user_prompt: str, images: list[str] | None = None) -> str:
        model = self._genai.GenerativeModel(self._model_name, system_instruction=system_prompt)
        contents = [user_prompt]
        if images:
            import base64
            for img_b64 in images:
                if "," in img_b64:
                    header, data = img_b64.split(",", 1)
                    mime_type = header.split(";")[0].split(":")[1]
                else:
                    data = img_b64
                    mime_type = "image/png"
                img_bytes = base64.b64decode(data)
                contents.append({
                    "mime_type": mime_type,
                    "data": img_bytes
                })
        response = model.generate_content(contents)
        return (response.text or "").strip()


class OpenAITextProvider(TextProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate(self, system_prompt: str, user_prompt: str, images: list[str] | None = None) -> str:
        content_parts = [{"type": "text", "text": user_prompt}]
        if images:
            for img_b64 in images:
                url = img_b64 if img_b64.startswith("data:") else f"data:image/png;base64,{img_b64}"
                content_parts.append({
                    "type": "image_url",
                    "image_url": {"url": url}
                })

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content_parts},
            ],
            max_tokens=900,
        )
        return (response.choices[0].message.content or "").strip()


def get_configured_text_provider() -> TextProvider:
    provider = settings.AI_PROVIDER.lower()

    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            raise TextProviderError("AI_PROVIDER is 'gemini' but GEMINI_API_KEY is not set in .env")
        return GeminiTextProvider(settings.GEMINI_API_KEY)

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise TextProviderError("AI_PROVIDER is 'openai' but OPENAI_API_KEY is not set in .env")
        return OpenAITextProvider(settings.OPENAI_API_KEY)

    raise TextProviderError(f"Unknown AI_PROVIDER '{settings.AI_PROVIDER}' — use 'gemini' or 'openai'")
