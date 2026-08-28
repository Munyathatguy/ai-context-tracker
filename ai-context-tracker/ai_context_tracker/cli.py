import argparse
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(prog="ai-context-tracker",
                                     description="MCP server for real-time AI operational awareness")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("serve", help="run the MCP server (stdio transport)")
    dash = sub.add_parser("dashboard", help="live htop-style CLI dashboard of the current session")
    dash.add_argument("--refresh", type=float, default=1.0)
    sub.add_parser("sessions", help="list saved sessions")
    init = sub.add_parser("init", help="write a starter config.yaml to the current directory")
    init.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.cmd == "dashboard":
        from .dashboard import run_dashboard
        try:
            run_dashboard(args.refresh)
        except KeyboardInterrupt:
            pass
    elif args.cmd == "sessions":
        from .config import load_config
        from .state import SessionState
        for s in SessionState.list_sessions(load_config().state_dir):
            print(f"{s['session_id']}  {s['model']:<22} turn {s['turn']:>3}  {s['total_tokens']:>10,} tok  ${s['cost_usd']:.4f}  last {s['last_message_at'][:19]}")
    elif args.cmd == "init":
        target = Path.cwd() / "config.yaml"
        if target.exists() and not args.force:
            print("config.yaml already exists (use --force to overwrite)")
            return
        example = Path(__file__).parent / "config.example.yaml"
        shutil.copy(example, target)
        print(f"wrote {target}")
    else:
        from .server import main as serve
        serve()


if __name__ == "__main__":
    main()
