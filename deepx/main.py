import argparse
import asyncio
import ctypes
import os
from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

from deepx.core.version import get_local_version
from deepx.core.windows_launch import (
    install_system_command,
    relaunch_in_windows_terminal,
    should_relaunch_in_windows_terminal,
    uninstall_system_command,
)
from deepx.ui.terminal import (
    console,
    disable_quick_edit_mode,
    setup_windows_terminal,
    shutdown_child_processes,
)


def main(argv=None):
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    default_state = str(Path(__file__).resolve().parent / "core" / "state.json")

    parser = argparse.ArgumentParser(description="DEEPX AGENT: Autonomous AI Engineering CLI")
    parser.add_argument("--headful", action="store_true", help="Launch browser in visible mode")
    parser.add_argument("--state", type=str, default=default_state, help="Path to playwright state file")
    parser.add_argument("--cwd", type=str, default=None, help="Working directory for the session")
    parser.add_argument("--launcher", action="store_true", help="Open DEEPX Interactive Launcher Hub")
    parser.add_argument("--install-cmd", action="store_true", help="Install global 'deepx' command into Windows PATH")
    parser.add_argument("--uninstall-cmd", action="store_true", help="Remove global 'deepx' command from Windows PATH")
    parser.add_argument("--in-wt", action="store_true", help="Internal flag indicating Windows Terminal session")
    parser.add_argument("--no-relaunch", action="store_true", help="Do not hand off from classic console to Windows Terminal")
    parser.add_argument("--version", action="store_true", help="Show installed DEEPX CLI version and exit")
    parser.add_argument("--update", action="store_true", help="Check and install latest update from GitHub")
    args = parser.parse_args(raw_argv)

    setup_windows_terminal()

    if args.version:
        console.print(f"[bold #536DFE]DEEPX CLI[/bold #536DFE] v{get_local_version()}")
        return

    if args.install_cmd:
        ok, message = install_system_command(_PROJECT_ROOT)
        console.print(message, style="bold #10B981" if ok else "bold red", markup=False, highlight=False)
        sys.exit(0 if ok else 1)

    if args.uninstall_cmd:
        ok, message = uninstall_system_command()
        console.print(message, style="bold #FBBF24" if ok else "bold red", markup=False, highlight=False)
        sys.exit(0 if ok else 1)

    if args.update:
        from deepx.core.updater import perform_self_update

        ok, message = perform_self_update()
        style = "bold #10B981" if ok else "bold red"
        console.print(message, style=style, markup=False, highlight=False)
        sys.exit(0 if ok else 1)

    target_cwd = os.path.abspath(args.cwd) if args.cwd and os.path.isdir(args.cwd) else os.getcwd()

    if not args.in_wt and not args.no_relaunch and should_relaunch_in_windows_terminal(raw_argv):
        forward = [
            sys.executable,
            "-u",
            str(Path(__file__).resolve()),
            "--in-wt",
            "--cwd",
            target_cwd,
        ]
        if args.headful:
            forward.append("--headful")
        if args.launcher:
            forward.append("--launcher")
        if args.state != default_state:
            forward.extend(["--state", args.state])

        title = "DEEPX LAUNCHER" if args.launcher else "DEEPX AGENT"
        if relaunch_in_windows_terminal(
            launch_args=forward,
            cwd=target_cwd,
            title=title,
            close_parent=True,
        ):
            os._exit(0)

    os.chdir(target_cwd)
    disable_quick_edit_mode()

    if args.launcher:
        from deepx.launcher import run_launcher

        sys.exit(run_launcher(_PROJECT_ROOT))

    if sys.platform == "win32":
        try:
            ctypes.windll.kernel32.SetConsoleTitleW("DEEPX AGENT")
        except Exception:
            pass

    from deepx.agent.runner import DeepCLIApp

    app = DeepCLIApp(state_file=args.state, headless=not args.headful)
    try:
        asyncio.run(app.run())
    finally:
        if "pytest" not in sys.modules:
            shutdown_child_processes()


if __name__ == "__main__":
    main()
