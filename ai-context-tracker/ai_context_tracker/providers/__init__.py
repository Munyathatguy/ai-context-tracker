from .anthropic_provider import AnthropicProvider
from .base import ProviderAdapter, extract_usage
from .google_provider import GoogleProvider
from .openai_provider import OpenAIProvider

PROVIDERS = {"openai": OpenAIProvider, "anthropic": AnthropicProvider, "google": GoogleProvider}


def get_provider(name: str) -> ProviderAdapter:
    cls = PROVIDERS.get(name)
    return cls() if cls else None

__all__ = ["PROVIDERS", "AnthropicProvider", "GoogleProvider", "OpenAIProvider", "ProviderAdapter", "extract_usage", "get_provider"]
