def evaluate(pct_remaining: float, thresholds: list[int], red_threshold: int, already_fired: list[int]) -> list[dict]:
    """Return newly-crossed threshold alerts, red alert last."""
    alerts = []
    for t in sorted(thresholds, reverse=True):
        if pct_remaining <= t and t not in already_fired:
            level = "red" if t <= red_threshold else ("danger" if t <= red_threshold * 2 else "warn")
            alerts.append({"threshold": t, "level": level, "message": alert_message(t, level, pct_remaining)})
    return alerts


def alert_message(threshold: int, level: str, pct_remaining: float) -> str:
    if level == "red":
        return (f"🔴 RED ALERT: only {pct_remaining:.1f}% of the context window remains (threshold {threshold}%). "
                "STOP expanding scope. Begin wrapping up NOW: summarize progress, finalize outputs, "
                "and call create_handoff to persist a session summary.")
    if level == "danger":
        return (f"⚠️ DANGER: {pct_remaining:.1f}% of the context window remains (threshold {threshold}%). "
                "Prioritize essential work and prepare a handoff summary soon.")
    return (f"⚡ WARNING: {pct_remaining:.1f}% of the context window remains (threshold {threshold}%). "
            "Be economical with long outputs and avoid re-reading large content.")
