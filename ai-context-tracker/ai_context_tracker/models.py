"""Model registry: context windows, output limits, capabilities and pricing (USD per 1M tokens).

Pricing is approximate and user-overridable via config.yaml -> pricing_overrides / model_overrides.
"""

MODEL_REGISTRY = {
    # OpenAI
    "gpt-5.2": {"provider": "openai", "context_window": 400_000, "max_output": 128_000, "capabilities": ["tool_use", "vision", "code_exec"], "price_in": 1.75, "price_out": 14.0},
    "gpt-5.1": {"provider": "openai", "context_window": 400_000, "max_output": 128_000, "capabilities": ["tool_use", "vision", "code_exec"], "price_in": 1.25, "price_out": 10.0},
    "gpt-5": {"provider": "openai", "context_window": 400_000, "max_output": 128_000, "capabilities": ["tool_use", "vision", "code_exec"], "price_in": 1.25, "price_out": 10.0},
    "gpt-5-mini": {"provider": "openai", "context_window": 400_000, "max_output": 128_000, "capabilities": ["tool_use", "vision"], "price_in": 0.25, "price_out": 2.0},
    "gpt-4.1": {"provider": "openai", "context_window": 1_047_576, "max_output": 32_768, "capabilities": ["tool_use", "vision"], "price_in": 2.0, "price_out": 8.0},
    "gpt-4o": {"provider": "openai", "context_window": 128_000, "max_output": 16_384, "capabilities": ["tool_use", "vision"], "price_in": 2.5, "price_out": 10.0},
    "o3": {"provider": "openai", "context_window": 200_000, "max_output": 100_000, "capabilities": ["tool_use", "vision", "reasoning"], "price_in": 2.0, "price_out": 8.0},
    # Anthropic
    "claude-opus-4-1": {"provider": "anthropic", "context_window": 200_000, "max_output": 32_000, "capabilities": ["tool_use", "vision"], "price_in": 15.0, "price_out": 75.0},
    "claude-sonnet-5": {"provider": "anthropic", "context_window": 200_000, "max_output": 64_000, "capabilities": ["tool_use", "vision", "code_exec"], "price_in": 3.0, "price_out": 15.0},
    "claude-sonnet-4-5": {"provider": "anthropic", "context_window": 200_000, "max_output": 64_000, "capabilities": ["tool_use", "vision", "code_exec"], "price_in": 3.0, "price_out": 15.0},
    "claude-haiku-4-5": {"provider": "anthropic", "context_window": 200_000, "max_output": 64_000, "capabilities": ["tool_use", "vision"], "price_in": 1.0, "price_out": 5.0},
    # Google
    "gemini-3-pro": {"provider": "google", "context_window": 1_048_576, "max_output": 65_536, "capabilities": ["tool_use", "vision", "code_exec"], "price_in": 2.0, "price_out": 12.0},
    "gemini-3-flash": {"provider": "google", "context_window": 1_048_576, "max_output": 65_536, "capabilities": ["tool_use", "vision"], "price_in": 0.5, "price_out": 3.0},
    "gemini-2.5-pro": {"provider": "google", "context_window": 1_048_576, "max_output": 65_536, "capabilities": ["tool_use", "vision", "code_exec"], "price_in": 1.25, "price_out": 10.0},
    "gemini-2.5-flash": {"provider": "google", "context_window": 1_048_576, "max_output": 65_536, "capabilities": ["tool_use", "vision"], "price_in": 0.30, "price_out": 2.5},
}

_FALLBACK = {"provider": "unknown", "context_window": 128_000, "max_output": 8_192, "capabilities": ["tool_use"], "price_in": 0.0, "price_out": 0.0}


def resolve_model(model_id: str, overrides: dict | None = None) -> dict:
    registry = dict(MODEL_REGISTRY)
    for k, v in (overrides or {}).items():
        registry[k] = {**registry.get(k, _FALLBACK), **v}
    if not model_id:
        return {"id": "unknown", **_FALLBACK}
    mid = model_id.lower()
    if mid in registry:
        return {"id": mid, **registry[mid]}
    # prefix / substring match (e.g. claude-sonnet-4-5-20250929, gpt-5.1-2026-01-12)
    best = None
    for key in sorted(registry, key=len, reverse=True):
        if mid.startswith(key) or key in mid:
            best = key
            break
    if best:
        return {"id": best, **registry[best]}
    return {"id": model_id, **_FALLBACK}


def capabilities_line(spec: dict) -> str:
    caps = spec.get("capabilities", [])
    can = ", ".join(c.replace("_", " ") for c in caps) or "unknown"
    cannot = []
    if "image_gen" not in caps:
        cannot.append("generate images")
    if "code_exec" not in caps:
        cannot.append("execute code natively")
    line = f"You are {spec['id']} | {spec['context_window']:,} context | {spec['max_output']:,} max output | CAN: {can}"
    if cannot:
        line += f" | CANNOT: {', '.join(cannot)}"
    return line
