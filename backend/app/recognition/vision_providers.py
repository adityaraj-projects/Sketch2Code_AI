"""
Real handwriting transcription needs an actual vision model — there is no
honest deterministic substitute for that part of the pipeline, unlike
shape/arrow recognition which is solvable with geometry alone. This module
wraps whichever vision API the deployment is configured for behind one
interface, so the pipeline never has to know which provider is active.

Both providers require the operator's own API key (same pattern as the
Google OAuth client ID in Phase 1) — set AI_PROVIDER + the matching key in
.env. Until a key is configured, `describe()` raises VisionProviderError
rather than silently returning fake text.
"""
from __future__ import annotations

import base64
from abc import ABC, abstractmethod

from app.core.config import settings


class VisionProviderError(RuntimeError):
    pass


class VisionProvider(ABC):
    @abstractmethod
    def transcribe_handwriting(self, image_png_bytes: bytes) -> str:
        """Returns the best-effort transcription of handwritten text in the
        image. Returns an empty string if the crop contains no legible text
        (e.g. it was just the shape's border re-traced) rather than
        guessing."""
        raise NotImplementedError


_TRANSCRIBE_PROMPT = (
    "This image is a small cropped region from inside a hand-drawn "
    "flowchart shape. Transcribe only the handwritten text visible in the "
    "image, exactly as written. If there is no legible text, respond with "
    "an empty string. Do not add commentary, punctuation guesses, or "
    "quotation marks — return the raw text only."
)


class GeminiVisionProvider(VisionProvider):
    def __init__(self, api_key: str, model: str = "gemini-3.5-flash"):
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self._genai = genai
        self._model_name = model

    def transcribe_handwriting(self, image_png_bytes: bytes) -> str:
        model = self._genai.GenerativeModel(self._model_name)
        response = model.generate_content(
            [
                _TRANSCRIBE_PROMPT,
                {"mime_type": "image/png", "data": image_png_bytes},
            ]
        )
        return (response.text or "").strip()


class OpenAIVisionProvider(VisionProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def transcribe_handwriting(self, image_png_bytes: bytes) -> str:
        b64 = base64.b64encode(image_png_bytes).decode("utf-8")
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": _TRANSCRIBE_PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                    ],
                }
            ],
            max_tokens=64,
        )
        return (response.choices[0].message.content or "").strip()


def get_configured_vision_provider() -> VisionProvider:
    provider = settings.AI_PROVIDER.lower()

    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            raise VisionProviderError(
                "AI_PROVIDER is 'gemini' but GEMINI_API_KEY is not set in .env"
            )
        return GeminiVisionProvider(settings.GEMINI_API_KEY)

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise VisionProviderError(
                "AI_PROVIDER is 'openai' but OPENAI_API_KEY is not set in .env"
            )
        return OpenAIVisionProvider(settings.OPENAI_API_KEY)

    raise VisionProviderError(f"Unknown AI_PROVIDER '{settings.AI_PROVIDER}' — use 'gemini' or 'openai'")
