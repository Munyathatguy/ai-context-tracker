from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def _tz(name: str):
    try:
        return ZoneInfo(name)
    except Exception:
        return timezone.utc


def now_local(tz_name: str) -> datetime:
    return datetime.now(_tz(tz_name))


def fmt(dt_iso: str, tz_name: str, with_date: bool = False) -> str:
    dt = datetime.fromisoformat(dt_iso).astimezone(_tz(tz_name))
    pattern = "%Y-%m-%d %-I:%M %p %Z" if with_date else "%-I:%M %p"
    return dt.strftime(pattern)


def humanize_gap(seconds: float) -> str:
    seconds = max(0, int(seconds))
    if seconds < 60:
        return f"{seconds} sec ago"
    if seconds < 3600:
        return f"{seconds // 60} min ago"
    if seconds < 86400:
        h, m = divmod(seconds // 60, 60)
        return f"{h} hr {m} min ago"
    return f"{seconds // 86400} days ago"


def time_line(tz_name: str, started_at: str, last_message_at: str) -> str:
    now = now_local(tz_name)
    gap = (datetime.now(timezone.utc) - datetime.fromisoformat(last_message_at)).total_seconds()
    return (f"Current time: {now.strftime('%Y-%m-%d %-I:%M %p %Z')} | "
            f"Session started: {fmt(started_at, tz_name)} | "
            f"Last message: {humanize_gap(gap)}")
