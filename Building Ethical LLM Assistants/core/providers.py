from abc import ABC, abstractmethod
from core.config import ANTHROPIC_API_KEY, GOOGLE_API_KEY
import os


class LLMProvider(ABC):
    model: str = ""

    @abstractmethod
    def complete(self, system: str, messages: list[dict]) -> str:
        """Send messages to the model and return the reply text."""


class AnthropicProvider(LLMProvider):
    model = "claude-haiku-4-5"

    def __init__(self):
        import anthropic
        self._client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def complete(self, system: str, messages: list[dict]) -> str:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=1000,
            system=system,
            messages=messages,
        )
        return response.content[0].text


class GemmaProvider(LLMProvider):
    """
    Google Gemma adapter via the google-genai SDK.

    Model id: The Gemini API lists Gemma 4 as free-tier on the pricing page but
    it did not appear in the models API at build time (2026-06-15). We use the
    most recent confirmed Gemma model available via the Gemini API
    (gemma-3-27b-it) and make it configurable via GEMMA_MODEL_ID.

    Update GEMMA_MODEL_ID in your .env to switch to a newer Gemma model
    when one becomes available (e.g. "gemma-4-27b-it" or similar).

    Teaching note: Gemma has no native system role — the adapter prepends
    the system prompt to the first user turn as "System: ...\n\nUser: ...".
    This is why the same system prompt may be adhered to differently across
    providers — a real representation/faithfulness teaching point for Module 2.
    """
    model: str  # set in __init__ from env or default

    DEFAULT_MODEL = "gemma-3-27b-it"  # last confirmed available via Gemini API

    def __init__(self):
        self.model = os.getenv("GEMMA_MODEL_ID", self.DEFAULT_MODEL)
        self._client = None  # lazy-initialized on first complete() call

    def _get_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=GOOGLE_API_KEY)
        return self._client

    def complete(self, system: str, messages: list[dict]) -> str:
        # Prepend system prompt to the first user message — Gemma has no system role
        prepended_messages = list(messages)
        if prepended_messages and prepended_messages[0]["role"] == "user":
            first_content = prepended_messages[0]["content"]
            prepended_messages[0] = {
                "role": "user",
                "content": f"System: {system}\n\nUser: {first_content}",
            }
        elif system:
            prepended_messages.insert(0, {
                "role": "user",
                "content": f"System: {system}",
            })

        # Convert to google-genai format
        contents = [
            {"role": msg["role"], "parts": [{"text": msg["content"]}]}
            for msg in prepended_messages
        ]

        response = self._get_client().models.generate_content(
            model=self.model,
            contents=contents,
        )
        return response.text


def get_provider(name: str) -> LLMProvider:
    name = (name or "anthropic").lower()
    if name == "anthropic":
        return AnthropicProvider()
    if name == "gemma":
        return GemmaProvider()
    raise ValueError(f"Unknown provider: {name!r}. Choose 'anthropic' or 'gemma'.")
