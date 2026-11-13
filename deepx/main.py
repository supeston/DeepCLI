import sys
import os
import asyncio
from deepx.core.version import get_local_version
from deepx.ui.terminal import setup_windows_terminal, console

def main():
    import argparse
    parser = argparse.ArgumentParser(description="DEEPX AGENT: Autonomous AI Engineering CLI")
    parser.add_argument("--headful", action="store_true", help="Launch browser in visible mode")
    parser.add_argument("--state", type=str, default=os.path.join(os.path.dirname(__file__), "core", "state.json"), help="Path to playwright state file")
    parser.add_argument("--version", action="store_true", help="Show installed DEEPX CLI version and exit")
    parser.add_argument("--update", action="store_true", help="Check and install latest update from GitHub")
    args = parser.parse_args()

    setup_windows_terminal()
    if args.version:
        console.print(f"[bold #536DFE]DEEPX CLI[/bold #536DFE] v{get_local_version()}")
        return
    if args.update:
        from deepx.core.updater import perform_self_update
        ok, message = perform_self_update()
        style = "bold #10B981" if ok else "bold red"
        console.print(message, style=style, markup=False, highlight=False)
        sys.exit(0 if ok else 1)

    from deepx.agent.runner import DeepCLIApp

    app = DeepCLIApp(state_file=args.state, headless=not args.headful)
    asyncio.run(app.run())

if __name__ == "__main__":
    main()
