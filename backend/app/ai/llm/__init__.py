from typing import Optional

from ..errors import LLMNotConfigured
from .base import LLMProvider


def build_provider(settings) -> Optional[LLMProvider]:
    """Provider from environment settings. Returns None when AI_PROVIDER is empty (assistant off).
    Raises LLMNotConfigured for a half-configured provider: never silently use an unavailable model."""
    name = (settings.ai_provider or "").strip().lower()
    if not name:
        return None
    if not settings.ai_model:
        raise LLMNotConfigured("AI_MODEL is not set")
    common = dict(timeout_s=settings.ai_timeout_s, max_tokens=settings.ai_max_output_tokens)
    if name == "anthropic":
        if not settings.ai_api_key:
            raise LLMNotConfigured("AI_API_KEY is not set")
        from .anthropic import AnthropicProvider

        kw = {"base_url": settings.ai_base_url} if settings.ai_base_url else {}
        return AnthropicProvider(settings.ai_api_key, settings.ai_model, **common, **kw)
    if name in ("openai", "openai_compatible"):
        if not settings.ai_api_key and not settings.ai_base_url:
            raise LLMNotConfigured("AI_API_KEY is not set")  # a local server (AI_BASE_URL) may run without a key
        from .openai_compat import OpenAICompatibleProvider

        kw = {"base_url": settings.ai_base_url} if settings.ai_base_url else {}
        return OpenAICompatibleProvider(settings.ai_api_key, settings.ai_model, **common, **kw)
    raise LLMNotConfigured(f"Unknown AI_PROVIDER '{name}' (use: anthropic | openai_compatible)")
