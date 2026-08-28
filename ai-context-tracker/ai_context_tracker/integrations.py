"""Optional SDK-side hooks: wrap provider responses so usage lands in the shared state file.

Example:
    from ai_context_tracker.integrations import track_response
    resp = client.chat.completions.create(...)
    track_response(resp, tracker)
"""
from .providers.base import extract_usage
from .tracker import ContextTracker


def track_response(response, tracker: ContextTracker, summary: str = "") -> dict:
    usage = extract_usage(response)
    return tracker.record_usage(
        input_tokens=usage["input"], output_tokens=usage["output"],
        cached_tokens=usage["cached"], reasoning_tokens=usage["reasoning"],
        model=usage.get("model", ""), summary=summary)
