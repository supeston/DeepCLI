import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Optional

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def _ensure_bootstrapped_environment(project_root: Path) -> None:
    """Ensure .venv and Rich exist before importing TUI dependencies."""
    venv_py = (
        project_root
        / ".venv"
        / ("Scripts" if sys.platform == "win32" else "bin")
        / ("python.exe" if sys.platform == "win32" else "python")
    )
    in_venv = os.path.normcase(os.path.realpath(sys.executable)) == os.path.normcase(
        os.path.realpath(str(venv_py))
    )

    if venv_py.is_file() and not in_venv and "pytest" not in sys.modules:
        res = subprocess.run([str(venv_py), "-u", str(__file__), *sys.argv[1:]], check=False)
        sys.exit(res.returncode)

    try:
        import rich  # noqa: F401
        return
    except ImportError:
        pass

    print("DEEPX Launcher: initializing environment via deepx/install.py...")
    res = subprocess.run([sys.executable, str(project_root / "deepx" / "install.py")], check=False)
    if res.returncode != 0:
        sys.exit(res.returncode)

    if venv_py.is_file() and not in_venv and "pytest" not in sys.modules:
        res2 = subprocess.run([str(venv_py), "-u", str(__file__), *sys.argv[1:]], check=False)
        sys.exit(res2.returncode)


_ensure_bootstrapped_environment(_PROJECT_ROOT)

from rich import box
from rich.align import Align
from rich.console import Group
from rich.markup import escape as rich_escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from deepx.core.updater import check_for_updates, get_cached_update_info, perform_self_update
from deepx.core.version import UpdateInfo, get_local_version, get_project_root
from deepx.core.windows_launch import (
    find_windows_terminal,
    install_system_command,
    is_system_command_installed,
    relaunch_in_windows_terminal,
    should_relaunch_in_windows_terminal,
    uninstall_system_command,
)
from deepx.ui.banner import BANNER_WIDTH, _format_workspace_path, _padded_ascii_block
from deepx.ui.terminal import (
    console,
    disable_quick_edit_mode,
    is_windows_terminal_session,
    read_single_key_confirm,
    setup_windows_terminal,
    shutdown_child_processes,
)


@dataclass
class LauncherSnapshot:
    local_version: str
    update_info: Optional[UpdateInfo]
    venv_ready: bool
    cmd_installed: bool
    terminal_label: str
    wt_available: bool
    app_root: Path
    status_note: str = ""
    status_style: str = "#94A3B8"


def collect_launcher_snapshot(
    project_root: Optional[Path] = None,
    use_cached_update: bool = True,
) -> LauncherSnapshot:
    root = Path(project_root).resolve() if project_root else get_project_root()
    venv_py = (
        root
        / ".venv"
        / ("Scripts" if sys.platform == "win32" else "bin")
        / ("python.exe" if sys.platform == "win32" else "python")
    )
    wt_path = find_windows_terminal()
    if is_windows_terminal_session():
        term_label = "Windows Terminal (TrueColor)"
    elif sys.platform == "win32":
        term_label = "Classic Console (conhost)"
    else:
        term_label = "POSIX Terminal"

    update_info = get_cached_update_info(root) if use_cached_update else None
    return LauncherSnapshot(
        local_version=get_local_version(root),
        update_info=update_info,
        venv_ready=venv_py.is_file(),
        cmd_installed=is_system_command_installed(root),
        terminal_label=term_label,
        wt_available=wt_path is not None,
        app_root=root,
    )


def get_menu_items(snapshot: LauncherSnapshot) -> list[tuple[str, str, str]]:
    cmd_label = (
        "Remove 'deepx' Command"
        if snapshot.cmd_installed
        else "Install 'deepx' Command"
    )
    cmd_desc = (
        "Remove global alias from Windows PATH"
        if snapshot.cmd_installed
        else "Register global 'deepx' in PATH"
    )
    return [
        ("launch", "Launch DEEPX Agent", "Start autonomous engineering session"),
        ("update", "Check & Install Updates", "Fetch latest release from GitHub"),
        ("deps", "Verify Dependencies", "Check packages, Chromium & repair"),
        ("cmd", cmd_label, cmd_desc),
        ("exit", "Exit Launcher", "Close DEEPX Control Hub"),
    ]


def build_launcher_renderable(
    snapshot: LauncherSnapshot,
    selected_index: int = 0,
    term_width: Optional[int] = None,
):
    width = int(term_width or getattr(console, "width", 100) or 100)
    wide_mode = width >= 66
    panel_width = min(BANNER_WIDTH, max(66, width - 8)) if wide_mode else max(38, width - 2)
    rule_width = max(24, min(58, panel_width - 16))

    header_grid = Table.grid(expand=True)
    header_grid.add_column(justify="center")

    if wide_mode:
        title = Align.center(Text(_padded_ascii_block(), style="bold #536DFE", end=""))
    else:
        title = Text("DEEPX LAUNCHER", style="bold #536DFE", end="")

    tag_line = (
        f"[bold #F8FAFC]CONTROL HUB[/bold #F8FAFC]"
        f"  [dim #475569]·[/dim #475569]  "
        f"[#CBD5E1]v{rich_escape(snapshot.local_version)}[/#CBD5E1]"
        f"  [dim #475569]·[/dim #475569]  "
        f"[#38BDF8]{rich_escape(snapshot.terminal_label)}[/#38BDF8]"
    )

    divider = Text("─" * rule_width, style="#334155")

    if snapshot.update_info is not None and snapshot.update_info.has_update:
        latest = rich_escape(str(snapshot.update_info.latest_version).lstrip("vV"))
        ver_status = f"[bold #FBBF24]update {latest}[/bold #FBBF24]"
    elif snapshot.update_info is not None and not snapshot.update_info.error:
        ver_status = "[#10B981]up to date[/#10B981]"
    elif snapshot.update_info is not None and snapshot.update_info.error:
        ver_status = "[#F59E0B]offline[/#F59E0B]"
    else:
        ver_status = "[#94A3B8]ready[/#94A3B8]"

    venv_status = "[#10B981].venv ok[/#10B981]" if snapshot.venv_ready else "[#FBBF24].venv missing[/#FBBF24]"
    cmd_status = "[#10B981]PATH[/#10B981]" if snapshot.cmd_installed else "[#64748B]unset[/#64748B]"
    sep = "  [dim #475569]·[/dim #475569]  "
    diag_line = (
        f"[#94A3B8]Updates:[/#94A3B8] {ver_status}"
        f"{sep}[#94A3B8]Env:[/#94A3B8] {venv_status}"
        f"{sep}[#94A3B8]deepx:[/#94A3B8] {cmd_status}"
    )

    path_str = _format_workspace_path(str(snapshot.app_root), max_len=max(24, panel_width - 22))
    path_line = f"[#64748B]Root:[/#64748B] [#94A3B8]{rich_escape(path_str)}[/#94A3B8]"

    header_grid.add_row(title)
    header_grid.add_row(Text(""))
    header_grid.add_row(Text.from_markup(tag_line))
    header_grid.add_row(divider)
    header_grid.add_row(Text.from_markup(diag_line))
    header_grid.add_row(Text.from_markup(path_line))

    banner_panel = Panel(
        header_grid,
        border_style="#536DFE",
        box=box.ROUNDED,
        padding=(1, 3) if wide_mode else (0, 2),
        width=panel_width,
        expand=True,
        subtitle="[dim #64748B] LAUNCHER EDITION [/dim #64748B]",
        subtitle_align="center",
    )

    items = get_menu_items(snapshot)
    clamped_idx = max(0, min(selected_index, len(items) - 1))
    menu_table = Table(
        show_header=False,
        box=None,
        padding=(0, 1),
        expand=True,
    )
    menu_table.add_column("Pointer", width=2, no_wrap=True)
    menu_table.add_column("Key", width=4, no_wrap=True)
    menu_table.add_column("Action", width=26, no_wrap=True)
    if wide_mode:
        menu_table.add_column("Details", no_wrap=True, overflow="ellipsis")

    for idx, (_key, label, desc) in enumerate(items):
        is_sel = idx == clamped_idx
        pointer = "[bold #38BDF8]▸[/bold #38BDF8]" if is_sel else " "
        num_badge = f"[bold #536DFE][{idx + 1}][/bold #536DFE]" if is_sel else f"[#64748B][{idx + 1}][/#64748B]"
        title_cell = (
            f"[bold #F8FAFC on #1E293B] {rich_escape(label)} [/bold #F8FAFC on #1E293B]"
            if is_sel
            else f"[#CBD5E1] {rich_escape(label)} [/#CBD5E1]"
        )
        if wide_mode:
            desc_cell = f"[#94A3B8]{rich_escape(desc)}[/#94A3B8]" if is_sel else f"[#64748B]{rich_escape(desc)}[/#64748B]"
            menu_table.add_row(pointer, num_badge, title_cell, desc_cell)
        else:
            menu_table.add_row(pointer, num_badge, title_cell)

    menu_panel = Panel(
        menu_table,
        title="[bold #CBD5E1] Actions [/bold #CBD5E1]",
        title_align="left",
        border_style="#334155",
        box=box.ROUNDED,
        padding=(1, 2) if wide_mode else (0, 1),
        width=panel_width,
        expand=True,
        subtitle="[dim #64748B] ↑/↓ select  ·  Enter execute  ·  1-5 hotkey  ·  Esc exit [/dim #64748B]",
        subtitle_align="center",
    )

    rows: list[object] = [Text(""), Align.center(banner_panel), Text(""), Align.center(menu_panel)]
    if snapshot.status_note:
        note_panel = Panel(
            Text(snapshot.status_note, style=snapshot.status_style),
            border_style="#334155",
            box=box.ROUNDED,
            padding=(0, 2),
            width=panel_width,
            expand=True,
        )
        rows.extend([Text(""), Align.center(note_panel)])
    return Group(*rows)


def _read_menu_key() -> str:
    """Read navigation keypress cross-platform, handling Win32 extended arrow codes cleanly."""
    if sys.platform == "win32":
        import msvcrt

        while True:
            ch = msvcrt.getwch()
            if ch in ("\x00", "\xe0"):
                ext = msvcrt.getwch()
                return {
                    "H": "UP",
                    "P": "DOWN",
                    "K": "LEFT",
                    "M": "RIGHT",
                }.get(ext, "")
            if ch in ("\r", "\n"):
                return "ENTER"
            if ch == "\x1b":
                return "ESC"
            if ch == "\x03":
                return "CTRL_C"
            low = ch.lower()
            if low == "w":
                return "UP"
            if low == "s":
                return "DOWN"
            if low == "q":
                return "ESC"
            if low in ("1", "2", "3", "4", "5"):
                return f"NUM_{low}"
            return ""
    else:
        raw = sys.stdin.read(1)
        if raw == "\x1b":
            return "ESC"
        if raw in ("\r", "\n"):
            return "ENTER"
        if raw in ("1", "2", "3", "4", "5"):
            return f"NUM_{raw}"
        return ""


def _pause_for_return() -> None:
    console.print("\n[dim #64748B]Press any key to return to Launcher...[/dim #64748B]")
    if sys.platform == "win32":
        import msvcrt

        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            msvcrt.getwch()
    else:
        input()


def _action_launch_agent(snapshot: LauncherSnapshot) -> int:
    from deepx.main import main as agent_main

    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleTitleW("DEEPX AGENT")
        except Exception:
            pass
    console.clear()
    exit_code = 0
    try:
        agent_main(["--in-wt", "--no-relaunch", "--cwd", str(snapshot.app_root)])
    except SystemExit as exc:
        exit_code = int(exc.code) if isinstance(exc.code, int) else 0
    return exit_code


def _action_check_updates(snapshot: LauncherSnapshot) -> None:
    console.print("\n[bold #536DFE][>][/bold #536DFE] Checking GitHub releases for DEEPX updates...")
    info = check_for_updates(force_refresh=True, project_root=snapshot.app_root)
    snapshot.update_info = info
    if info.error:
        snapshot.status_note = f"Update check failed: {info.error}"
        snapshot.status_style = "#F59E0B"
        console.print(f"[#F59E0B]{rich_escape(snapshot.status_note)}[/#F59E0B]")
        _pause_for_return()
        return

    if not info.has_update:
        snapshot.status_note = f"DEEPX v{info.current_version} is already up to date."
        snapshot.status_style = "#10B981"
        console.print(f"[bold #10B981][+][/bold #10B981] {rich_escape(snapshot.status_note)}")
        time.sleep(0.9)
        return

    console.print(
        f"[bold #FBBF24][!][/bold #FBBF24] New version available: v{rich_escape(info.current_version)} -> v{rich_escape(info.latest_version)}"
    )
    confirm = read_single_key_confirm("Install update now? [y/N]: ")
    if confirm != "y":
        snapshot.status_note = f"Update v{info.latest_version} skipped."
        snapshot.status_style = "#FBBF24"
        return

    console.print("[bold #536DFE][>][/bold #536DFE] Downloading and applying update...")
    ok, msg = perform_self_update(project_root=snapshot.app_root)
    snapshot.local_version = get_local_version(snapshot.app_root)
    if ok:
        snapshot.update_info = UpdateInfo(
            current_version=snapshot.local_version,
            latest_version=snapshot.local_version,
            has_update=False,
            source="updated",
        )
        snapshot.status_note = msg
        snapshot.status_style = "#10B981"
        console.print(f"[bold #10B981][+][/bold #10B981] {rich_escape(msg)}")
    else:
        snapshot.status_note = msg
        snapshot.status_style = "bold red"
        console.print(msg, style="bold red", markup=False)
    _pause_for_return()


def _action_verify_dependencies(snapshot: LauncherSnapshot) -> None:
    console.print("\n[bold #536DFE][>][/bold #536DFE] Running full dependency & browser diagnostics...")
    install_script = snapshot.app_root / "deepx" / "install.py"
    check_res = subprocess.run([sys.executable, str(install_script), "--check-only"], check=False)
    if check_res.returncode == 0:
        snapshot.status_note = "All Python modules and Playwright Chromium passed verification."
        snapshot.status_style = "#10B981"
        console.print(f"\n[bold #10B981][+][/bold #10B981] {snapshot.status_note}")
        _pause_for_return()
        return

    console.print("\n[bold #FBBF24][!][/bold #FBBF24] Some dependencies or Chromium need setup/repair.")
    if read_single_key_confirm("Run automatic repair (deepx/install.py)? [y/N]: ") == "y":
        repair_res = subprocess.run([sys.executable, str(install_script)], check=False)
        if repair_res.returncode == 0:
            snapshot.status_note = "Environment repaired successfully."
            snapshot.status_style = "#10B981"
        else:
            snapshot.status_note = f"Installer exited with code {repair_res.returncode}."
            snapshot.status_style = "bold red"
        _pause_for_return()
    else:
        snapshot.status_note = "Diagnostics found incomplete dependencies (repair skipped)."
        snapshot.status_style = "#FBBF24"


def _action_toggle_global_command(snapshot: LauncherSnapshot) -> None:
    if snapshot.cmd_installed:
        ok, msg = uninstall_system_command()
        snapshot.status_note = msg
        snapshot.status_style = "#FBBF24" if ok else "bold red"
    else:
        ok, msg = install_system_command(snapshot.app_root)
        snapshot.status_note = msg
        snapshot.status_style = "#10B981" if ok else "bold red"
    snapshot.cmd_installed = is_system_command_installed(snapshot.app_root)


def run_launcher(project_root: Optional[Path] = None) -> int:
    root = Path(project_root).resolve() if project_root else get_project_root()
    setup_windows_terminal()
    disable_quick_edit_mode()

    snapshot = collect_launcher_snapshot(root, use_cached_update=True)
    selected = 0

    try:
        while True:
            snapshot.cmd_installed = is_system_command_installed(root)
            disable_quick_edit_mode()
            console.clear()
            console.print(build_launcher_renderable(snapshot, selected_index=selected))

            key = _read_menu_key()
            items = get_menu_items(snapshot)
            if key == "UP":
                selected = (selected - 1) % len(items)
                continue
            if key == "DOWN":
                selected = (selected + 1) % len(items)
                continue
            if key in ("ESC", "CTRL_C"):
                console.clear()
                return 0
            if key.startswith("NUM_"):
                idx = int(key.split("_", 1)[1]) - 1
                if 0 <= idx < len(items):
                    selected = idx
                else:
                    continue
            elif key != "ENTER":
                continue

            action_id = items[selected][0]
            if action_id == "launch":
                return _action_launch_agent(snapshot)
            if action_id == "update":
                _action_check_updates(snapshot)
            elif action_id == "deps":
                _action_verify_dependencies(snapshot)
            elif action_id == "cmd":
                _action_toggle_global_command(snapshot)
            elif action_id == "exit":
                console.clear()
                return 0
    finally:
        shutdown_child_processes()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="DEEPX AGENT Launcher & Control Hub")
    parser.add_argument("--in-wt", action="store_true", help="Already inside Windows Terminal")
    parser.add_argument("--no-relaunch", action="store_true", help="Stay in current console")
    args = parser.parse_args(argv)

    if not args.in_wt and not args.no_relaunch and should_relaunch_in_windows_terminal(argv):
        launched = relaunch_in_windows_terminal(
            launch_args=[sys.executable, "-u", str(Path(__file__).resolve()), "--in-wt"],
            cwd=str(_PROJECT_ROOT),
            title="DEEPX LAUNCHER",
            close_parent=True,
        )
        if launched:
            os._exit(0)

    return run_launcher(_PROJECT_ROOT)


if __name__ == "__main__":
    sys.exit(main())
