"""Optional SDK-side hooks: wrap provider responses so usage lands in the shared state file.

Example:
    from ai_context_tracker.integrations import track_response
    resp = client.chat.completions.create(...)
    track_response(resp, tracker)
"""
from .providers.base import extract_usage
from .tracker import ContextTracker

_RL_REMAINING = ("x-ratelimit-remaining-tokens", "anthropic-ratelimit-tokens-remaining",
                 "anthropic-ratelimit-input-tokens-remaining")
_RL_LIMIT = ("x-ratelimit-limit-tokens", "anthropic-ratelimit-tokens-limit",
             "anthropic-ratelimit-input-tokens-limit")


def parse_rate_limit_headers(headers) -> tuple[int | None, int | None]:
    if not headers:
        return None, None
    h = {str(k).lower(): v for k, v in dict(headers).items()}
    rem = next((h[k] for k in _RL_REMAINING if h.get(k)), None)
    lim = next((h[k] for k in _RL_LIMIT if h.get(k)), None)
    try:
        return (int(rem) if rem is not None else None, int(lim) if lim is not None else None)
    except (TypeError, ValueError):
        return None, None


def track_response(response, tracker: ContextTracker, summary: str = "", headers=None) -> dict:
    usage = extract_usage(response)
    rl_rem, rl_lim = parse_rate_limit_headers(headers)
    return tracker.record_usage(
        input_tokens=usage["input"], output_tokens=usage["output"],
        cached_tokens=usage["cached"], reasoning_tokens=usage["reasoning"],
        model=usage.get("model", ""), summary=summary,
        rl_remaining_tokens=rl_rem, rl_limit_tokens=rl_lim)
