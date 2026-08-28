import httpx

from ai_context_tracker.providers import OpenAIProvider, AnthropicProvider, GoogleProvider
from ai_context_tracker.providers.base import extract_usage


def test_extract_usage_openai():
    resp = {"model": "gpt-5.1", "usage": {"prompt_tokens": 120, "completion_tokens": 80,
            "prompt_tokens_details": {"cached_tokens": 40},
            "completion_tokens_details": {"reasoning_tokens": 30}}}
    u = extract_usage(resp)
    assert u == {"input": 120, "output": 80, "cached": 40, "reasoning": 30, "model": "gpt-5.1"}


def test_extract_usage_anthropic():
    resp = {"model": "claude-sonnet-4-5", "usage": {"input_tokens": 200, "output_tokens": 90, "cache_read_input_tokens": 50}}
    u = extract_usage(resp)
    assert u["input"] == 200 and u["output"] == 90 and u["cached"] == 50


def test_extract_usage_google():
    resp = {"model": "gemini-2.5-pro", "usageMetadata": {"promptTokenCount": 300, "candidatesTokenCount": 150,
            "cachedContentTokenCount": 20, "thoughtsTokenCount": 60}}
    u = extract_usage(resp)
    assert u == {"input": 300, "output": 150, "cached": 20, "reasoning": 60, "model": "gemini-2.5-pro"}


def test_extract_usage_object_duck_typing():
    class Usage:
        def model_dump(self):
            return {"input_tokens": 10, "output_tokens": 5}

    class Resp:
        model = "claude-haiku-4-5"

        def model_dump(self):
            return {"model": self.model, "usage": Usage().model_dump()}

    u = extract_usage(Resp())
    assert u["input"] == 10 and u["model"] == "claude-haiku-4-5"


def test_count_tokens_fallback_without_key(monkeypatch):
    for var in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    text = "x" * 400
    assert OpenAIProvider().count_tokens("gpt-5.1", text) == 100
    assert AnthropicProvider().count_tokens("claude-sonnet-4-5", text) == 100
    assert GoogleProvider().count_tokens("gemini-2.5-pro", text) == 100


def test_count_tokens_uses_endpoint(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    def fake_post(url, **kwargs):
        assert "count_tokens" in url
        return httpx.Response(200, json={"input_tokens": 1234}, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)
    assert AnthropicProvider().count_tokens("claude-sonnet-4-5", "hello") == 1234


def test_org_usage_requires_admin_key(monkeypatch):
    monkeypatch.delenv("OPENAI_ADMIN_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_ADMIN_KEY", raising=False)
    assert "error" in OpenAIProvider().get_org_usage()
    assert "error" in AnthropicProvider().get_org_usage()
    assert "note" in GoogleProvider().get_org_usage()


def test_org_usage_openai_parses_buckets(monkeypatch):
    monkeypatch.setenv("OPENAI_ADMIN_KEY", "admin-key")

    def fake_get(url, **kwargs):
        return httpx.Response(200, json={"data": [{"results": [{"input_tokens": 100, "output_tokens": 40}]}]},
                              request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    u = OpenAIProvider().get_org_usage()
    assert u["input_tokens"] == 100 and u["output_tokens"] == 40
