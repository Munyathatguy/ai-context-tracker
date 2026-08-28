"""htop-style live CLI dashboard reading the shared session state file."""
import time
from datetime import datetime, timezone

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

from .config import load_config
from .models import resolve_model
from .state import SessionState
from .timefmt import humanize_gap


def _bar(pct: float, width: int = 40) -> Text:
    color = "green" if pct < 70 else ("yellow" if pct < 85 else "red")
    filled = int(width * pct / 100)
    return Text("█" * filled + "░" * (width - filled) + f" {pct:.1f}%", style=color)


def render(config) -> Panel:
    st = SessionState.load_latest(config.state_dir)
    if not st:
        return Panel(Text("No session state yet. Waiting for the MCP server to record usage...", style="dim"),
                     title="ai-context-tracker", border_style="cyan")
    spec = resolve_model(st.model, config.model_overrides)
    pct = min(100.0, 100.0 * st.usage["total"] / spec["context_window"])
    gap = (datetime.now(timezone.utc) - datetime.fromisoformat(st.last_message_at)).total_seconds()

    usage = Table(show_header=False, box=None, pad_edge=False)
    usage.add_row("input", f"{st.usage['input']:,}")
    usage.add_row("output", f"{st.usage['output']:,}")
    usage.add_row("cached", f"{st.usage['cached']:,}")
    usage.add_row("reasoning", f"{st.usage['reasoning']:,}")
    usage.add_row(Text("total", style="bold"), Text(f"{st.usage['total']:,}", style="bold"))

    tasks = Table(show_header=False, box=None, pad_edge=False)
    for t in st.tasks or [{"status": "-", "title": "(no tasks registered)"}]:
        mark = {"done": "[green]✔[/]", "in_progress": "[yellow]◐[/]", "todo": "[dim]○[/]"}.get(t["status"], " ")
        tasks.add_row(mark, t["title"])

    alerts = Text("\n".join(a["message"] for a in (st.active_alerts or [])[-3:]) or "no active alerts", style="yellow" if st.active_alerts else "dim")

    head = Table(show_header=False, box=None, expand=True)
    head.add_row(f"[bold cyan]{spec['id']}[/] ({spec['provider']})",
                 f"turn [bold]{st.turn}[/]", f"cost [bold green]${st.cost_usd:.4f}[/]",
                 f"last msg {humanize_gap(gap)}", f"session {st.session_id}")

    return Panel(Group(
        head,
        Text(f"\ncontext window  {st.usage['total']:,} / {spec['context_window']:,}"),
        _bar(pct),
        Text("\ntoken breakdown", style="bold"), usage,
        Text("\ntasks", style="bold"), tasks,
        Text("\nalerts", style="bold"), alerts,
        Text(f"\nhandoffs saved: {len(st.handoffs)} | started {st.started_at[:19]}", style="dim"),
    ), title="ai-context-tracker — live session", border_style="cyan")


def run_dashboard(refresh: float = 1.0):
    config = load_config()
    console = Console()
    with Live(render(config), console=console, refresh_per_second=2, screen=True) as live:
        while True:
            time.sleep(refresh)
            live.update(render(config))
