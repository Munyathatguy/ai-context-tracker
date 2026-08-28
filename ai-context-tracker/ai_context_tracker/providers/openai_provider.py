import os
import time

import httpx

from .base import ProviderAdapter

BASE = "https://api.openai.com/v1"


class OpenAIProvider(ProviderAdapter):
    name = "openai"

    def _key(self, admin: bool = False) -> str | None:
        return os.environ.get("OPENAI_ADMIN_KEY") if admin else os.environ.get("OPENAI_API_KEY")

    def count_tokens(self, model: str, text: str) -> int:
        key = self._key()
        if not key:
            return self.estimate_tokens(text)
        try:
            r = httpx.post(f"{BASE}/responses/input_tokens", timeout=15,
                           headers={"Authorization": f"Bearer {key}"},
                           json={"model": model, "input": text})
            r.raise_for_status()
            return int(r.json().get("input_tokens", 0))
        except (httpx.HTTPError, ValueError, KeyError):
            return self.estimate_tokens(text)

    def get_org_usage(self, days: int = 1) -> dict:
        key = self._key(admin=True)
        if not key:
            return {"error": "OPENAI_ADMIN_KEY not set — org-level usage requires an Admin API key"}
        start = int(time.time()) - days * 86400
        try:
            r = httpx.get(f"{BASE}/organization/usage/completions", timeout=20,
                          headers={"Authorization": f"Bearer {key}"},
                          params={"start_time": start, "bucket_width": "1d", "limit": days})
            r.raise_for_status()
            data = r.json()
            total_in = total_out = 0
            for bucket in data.get("data", []):
                for res in bucket.get("results", []):
                    total_in += res.get("input_tokens", 0)
                    total_out += res.get("output_tokens", 0)
            return {"provider": "openai", "days": days, "input_tokens": total_in, "output_tokens": total_out, "raw_buckets": len(data.get("data", []))}
        except httpx.HTTPError as e:
            return {"error": f"openai usage api: {e}"}

    @staticmethod
    def rate_limit_from_headers(headers: dict) -> dict:
        return {k: headers.get(k) for k in (
            "x-ratelimit-remaining-tokens", "x-ratelimit-limit-tokens",
            "x-ratelimit-remaining-requests", "x-ratelimit-reset-tokens") if headers.get(k)}
