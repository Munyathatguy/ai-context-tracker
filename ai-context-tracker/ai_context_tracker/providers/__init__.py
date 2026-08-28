from .base import ProviderAdapter, extract_usage
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .google_provider import GoogleProvider

PROVIDERS = {"openai": OpenAIProvider, "anthropic": AnthropicProvider, "google": GoogleProvider}


def get_provider(name: str) -> ProviderAdapter:
    cls = PROVIDERS.get(name)
    return cls() if cls else None

__all__ = ["ProviderAdapter", "extract_usage", "OpenAIProvider", "AnthropicProvider", "GoogleProvider", "get_provider", "PROVIDERS"]
