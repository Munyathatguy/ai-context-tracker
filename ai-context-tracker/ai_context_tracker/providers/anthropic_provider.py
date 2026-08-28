import os
from datetime import UTC, datetime, timedelta

import httpx

from .base import ProviderAdapter

BASE = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"


class AnthropicProvider(ProviderAdapter):
    name = "anthropic"

    def count_tokens(self, model: str, text: str) -> int:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            return self.estimate_tokens(text)
        try:
            r = httpx.post(f"{BASE}/messages/count_tokens", timeout=15,
                           headers={"x-api-key": key, "anthropic-version": VERSION},
                           json={"model": model, "messages": [{"role": "user", "content": text}]})
            r.raise_for_status()
            return int(r.json().get("input_tokens", 0))
        except (httpx.HTTPError, ValueError, KeyError):
            return self.estimate_tokens(text)

    def get_org_usage(self, days: int = 1) -> dict:
        key = os.environ.get("ANTHROPIC_ADMIN_KEY")
        if not key:
            return {"error": "ANTHROPIC_ADMIN_KEY not set — org-level usage requires an Admin API key"}
        start = (datetime.now(UTC) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            r = httpx.get(f"{BASE}/organizations/usage_report/messages", timeout=20,
                          headers={"x-api-key": key, "anthropic-version": VERSION},
                          params={"starting_at": start, "bucket_width": "1d"})
            r.raise_for_status()
            data = r.json()
            total_in = total_out = 0
            for bucket in data.get("data", []):
                for res in bucket.get("results", []):
                    total_in += res.get("uncached_input_tokens", 0) + res.get("cache_read_input_tokens", 0)
                    total_out += res.get("output_tokens", 0)
            return {"provider": "anthropic", "days": days, "input_tokens": total_in, "output_tokens": total_out, "raw_buckets": len(data.get("data", []))}
        except httpx.HTTPError as e:
            return {"error": f"anthropic usage api: {e}"}
