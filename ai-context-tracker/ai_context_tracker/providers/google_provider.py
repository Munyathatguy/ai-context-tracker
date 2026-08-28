import os

import httpx

from .base import ProviderAdapter

BASE = "https://generativelanguage.googleapis.com/v1beta"


class GoogleProvider(ProviderAdapter):
    name = "google"

    def count_tokens(self, model: str, text: str) -> int:
        key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not key:
            return self.estimate_tokens(text)
        try:
            r = httpx.post(f"{BASE}/models/{model}:countTokens", timeout=15,
                           params={"key": key},
                           json={"contents": [{"parts": [{"text": text}]}]})
            r.raise_for_status()
            return int(r.json().get("totalTokens", 0))
        except (httpx.HTTPError, ValueError, KeyError):
            return self.estimate_tokens(text)

    def get_org_usage(self, days: int = 1) -> dict:
        return {"provider": "google", "note": "Google exposes account usage via AI Studio dashboard / BigQuery export, "
                                              "not a public REST usage API. Per-request usage_metadata is tracked automatically."}
