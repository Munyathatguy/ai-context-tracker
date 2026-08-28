from abc import ABC, abstractmethod


class ProviderAdapter(ABC):
    name = "base"

    @abstractmethod
    def count_tokens(self, model: str, text: str) -> int:
        """Exact pre-request token count via the provider's native endpoint."""

    @abstractmethod
    def get_org_usage(self, days: int = 1) -> dict:
        """Org/account-level usage from the provider's Admin API."""

    @staticmethod
    def estimate_tokens(text: str) -> int:
        return max(1, len(text) // 4)


def _to_dict(obj) -> dict:
    if isinstance(obj, dict):
        return obj
    for attr in ("model_dump", "to_dict", "dict"):
        fn = getattr(obj, attr, None)
        if callable(fn):
            try:
                return fn()
            except TypeError:
                continue
    return getattr(obj, "__dict__", {}) or {}


def extract_usage(response) -> dict:
    """Duck-typed usage extraction from OpenAI / Anthropic / Google response payloads."""
    data = _to_dict(response)
    usage = _to_dict(data.get("usage") or data.get("usageMetadata") or data.get("usage_metadata") or {})
    out = {"input": 0, "output": 0, "cached": 0, "reasoning": 0, "model": data.get("model", "")}
    if not usage:
        return out
    # OpenAI chat/responses
    out["input"] = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
    out["output"] = usage.get("completion_tokens") or usage.get("output_tokens") or 0
    ptd = _to_dict(usage.get("prompt_tokens_details") or usage.get("input_tokens_details") or {})
    ctd = _to_dict(usage.get("completion_tokens_details") or usage.get("output_tokens_details") or {})
    out["cached"] = ptd.get("cached_tokens", 0) or usage.get("cache_read_input_tokens", 0) or 0
    out["reasoning"] = ctd.get("reasoning_tokens", 0) or 0
    # Google usage_metadata
    if usage.get("promptTokenCount") is not None or usage.get("prompt_token_count") is not None:
        out["input"] = usage.get("promptTokenCount") or usage.get("prompt_token_count") or 0
        out["output"] = usage.get("candidatesTokenCount") or usage.get("candidates_token_count") or 0
        out["cached"] = usage.get("cachedContentTokenCount") or usage.get("cached_content_token_count") or 0
        out["reasoning"] = usage.get("thoughtsTokenCount") or usage.get("thoughts_token_count") or 0
    return out
