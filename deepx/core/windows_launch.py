import ctypes
import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from deepx.core.version import get_project_root


_IDE_OR_CONPTY_ENV_VARS = (
    "VSCODE_PID",
    "VSCODE_INJECTION",
    "JETBRAINS_IDE",
    "TERMINAL_EMULATOR",
    "ConEmuPID",
    "CI",
    "GITHUB_ACTIONS",
)

_SKIP_RELAUNCH_FLAGS = {
    "--in-wt",
    "--no-relaunch",
    "--version",
    "-V",
    "--update",
    "--install-cmd",
    "--uninstall-cmd",
    "--help",
    "-h",
}


def get_bin_dir(base_dir: Optional[Path] = None) -> Path:
    if base_dir is not None:
        return Path(base_dir)
    local_app_data = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(local_app_data) / "DeepX" / "bin"


def get_windows_build() -> tuple[int, int]:
    if sys.platform != "win32":
        return 0, 0
    try:
        ver = sys.getwindowsversion()
        return int(ver.major), int(ver.build)
    except Exception:
        return 0, 0


def is_windows_11() -> bool:
    major, build = get_windows_build()
    return major > 10 or (major == 10 and build >= 22000)


def find_windows_terminal() -> Optional[str]:
    """Return path to Windows Terminal (wt.exe) if installed, else None."""
    if sys.platform != "win32":
        return None

    candidates: list[str] = []
    for name in ("wt.exe", "wt"):
        found = shutil.which(name)
        if found:
            candidates.append(found)

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(str(Path(local_app_data) / "Microsoft" / "WindowsApps" / "wt.exe"))
        candidates.append(
            str(
                Path(local_app_data)
                / "Microsoft"
                / "WindowsApps"
                / "Microsoft.WindowsTerminal_8wekyb3d8bbwe"
                / "wt.exe"
            )
        )

    program_files = os.environ.get("ProgramFiles") or os.environ.get("PROGRAMFILES")
    if program_files:
        pattern = str(Path(program_files) / "WindowsApps" / "Microsoft.WindowsTerminal_*" / "wt.exe")
        for match in sorted(glob.glob(pattern), reverse=True):
            candidates.append(match)

    for candidate in candidates:
        try:
            if os.path.exists(candidate) or os.path.lexists(candidate):
                return candidate
        except OSError:
            continue
    return None


def is_standalone_classic_console() -> bool:
    """Return True only when running directly inside a visible classic conhost window."""
    if sys.platform != "win32":
        return False
    if os.environ.get("WT_SESSION"):
        return False
    if "pytest" in sys.modules or os.environ.get("PYTEST_CURRENT_TEST"):
        return False
    if any(os.environ.get(var) for var in _IDE_OR_CONPTY_ENV_VARS):
        return False
    term_program = (os.environ.get("TERM_PROGRAM") or "").strip().lower()
    if term_program:
        return False
    try:
        if not (sys.stdin.isatty() and sys.stdout.isatty()):
            return False
    except Exception:
        return False

    try:
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        hwnd = kernel32.GetConsoleWindow()
        if not hwnd:
            return False
        if not user32.IsWindowVisible(hwnd):
            return False
        class_buf = ctypes.create_unicode_buffer(64)
        length = user32.GetClassNameW(hwnd, class_buf, 64)
        if length <= 0:
            return False
        return class_buf.value == "ConsoleWindowClass"
    except Exception:
        return False


def should_relaunch_in_windows_terminal(argv: Optional[list[str]] = None) -> bool:
    """Decide whether current standalone classic console process should hand off to Windows Terminal."""
    if os.environ.get("DEEPX_NO_WT_RELAUNCH") == "1":
        return False
    args = list(sys.argv[1:] if argv is None else argv)
    for token in args:
        if token in _SKIP_RELAUNCH_FLAGS:
            return False
    if not is_standalone_classic_console():
        return False
    return find_windows_terminal() is not None or is_windows_11()


def build_wt_command(
    launch_args: list[str],
    cwd: str,
    title: str = "DEEPX AGENT",
    cols: int = 116,
    lines: int = 34,
    wt_path: Optional[str] = None,
) -> list[str]:
    wt_exe = wt_path or find_windows_terminal() or "wt.exe"
    clean_args = [str(a) for a in launch_args]
    if "--in-wt" not in clean_args:
        clean_args.append("--in-wt")
    return [
        wt_exe,
        "-w",
        "new",
        "--size",
        f"{int(cols)},{int(lines)}",
        "new-tab",
        "--title",
        title,
        "-d",
        str(cwd),
        *clean_args,
    ]


def close_classic_console_window() -> bool:
    """Request the visible standalone classic console window to close cleanly."""
    if not is_standalone_classic_console():
        return False
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            return bool(ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0))
    except Exception:
        pass
    return False


def relaunch_in_windows_terminal(
    launch_args: list[str],
    cwd: str,
    title: str = "DEEPX AGENT",
    close_parent: bool = True,
    wt_path: Optional[str] = None,
) -> bool:
    """Spawn a detached Windows Terminal session and optionally close the old classic console."""
    if sys.platform != "win32":
        return False

    target_wt = wt_path or find_windows_terminal()
    if not target_wt:
        if is_windows_11():
            target_wt = "wt.exe"
        else:
            return False

    target_cwd = str(cwd or os.getcwd())
    if not os.path.isdir(target_cwd):
        target_cwd = os.getcwd()

    cmd = build_wt_command(
        launch_args=launch_args,
        cwd=target_cwd,
        title=title,
        wt_path=target_wt,
    )
    creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(
        subprocess, "DETACHED_PROCESS", 0
    )
    try:
        subprocess.Popen(
            cmd,
            cwd=target_cwd,
            creationflags=creation_flags,
            close_fds=True,
        )
    except OSError:
        return False

    if close_parent:
        close_classic_console_window()
    return True


def _resolve_launcher_python(project_root: Path) -> Path:
    venv_py = project_root / ".venv" / ("Scripts" if sys.platform == "win32" else "bin") / (
        "python.exe" if sys.platform == "win32" else "python"
    )
    if venv_py.is_file():
        return venv_py
    return Path(sys.executable)


def _broadcast_environment_change() -> None:
    if sys.platform != "win32":
        return
    try:
        result = ctypes.c_ulong(0)
        ctypes.windll.user32.SendMessageTimeoutW(
            0xFFFF,
            0x001A,
            0,
            "Environment",
            0x0002,
            2000,
            ctypes.byref(result),
        )
    except Exception:
        pass


def _update_user_path_registry(bin_dir: Path, remove: bool = False) -> bool:
    if sys.platform != "win32":
        return False
    try:
        import winreg

        target = os.path.normcase(os.path.normpath(str(bin_dir)))
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            "Environment",
            0,
            winreg.KEY_READ | winreg.KEY_WRITE,
        ) as key:
            try:
                current_raw, reg_type = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                current_raw, reg_type = "", winreg.REG_EXPAND_SZ

            entries = [item for item in str(current_raw).split(";") if item.strip()]
            filtered: list[str] = []
            already_present = False
            for item in entries:
                norm = os.path.normcase(os.path.normpath(os.path.expandvars(item.strip())))
                if norm == target:
                    already_present = True
                    if remove:
                        continue
                filtered.append(item.strip())

            if not remove and not already_present:
                filtered.append(str(bin_dir))
            elif remove and not already_present:
                return False

            new_value = ";".join(filtered)
            write_type = reg_type if reg_type in (winreg.REG_SZ, winreg.REG_EXPAND_SZ) else winreg.REG_EXPAND_SZ
            winreg.SetValueEx(key, "Path", 0, write_type, new_value)
        _broadcast_environment_change()
        return True
    except Exception:
        return False


def is_system_command_installed(
    project_root: Optional[Path] = None,
    bin_dir: Optional[Path] = None,
) -> bool:
    target_bin = get_bin_dir(bin_dir)
    cmd_file = target_bin / "deepx.cmd"
    if not cmd_file.is_file():
        return False
    if project_root is not None:
        try:
            content = cmd_file.read_text(encoding="utf-8", errors="ignore")
            if str(Path(project_root).resolve()) not in content:
                return False
        except OSError:
            return False
    return True


def install_system_command(
    project_root: Optional[Path] = None,
    bin_dir: Optional[Path] = None,
    update_registry: bool = True,
) -> tuple[bool, str]:
    """Install global `deepx` command shims into %LOCALAPPDATA%\\DeepX\\bin and User PATH."""
    root = Path(project_root).resolve() if project_root else get_project_root()
    target_bin = get_bin_dir(bin_dir)
    target_bin.mkdir(parents=True, exist_ok=True)
    py_exec = _resolve_launcher_python(root)
    fallback_py = Path(sys.executable)

    cmd_path = target_bin / "deepx.cmd"
    ps1_path = target_bin / "deepx.ps1"

    cmd_content = (
        "@echo off\n"
        "setlocal\n"
        f'set "DEEPX_ROOT={root}"\n'
        f'set "DEEPX_PY={py_exec}"\n'
        f'if not exist "%DEEPX_PY%" set "DEEPX_PY={fallback_py}"\n'
        'if not exist "%DEEPX_PY%" set "DEEPX_PY=python"\n'
        'set "PYTHONPATH=%DEEPX_ROOT%;%PYTHONPATH%"\n'
        '"%DEEPX_PY%" -u -m deepx.main --cwd "%CD%" %*\n'
        "exit /b %ERRORLEVEL%\n"
    )
    ps1_content = (
        "$ErrorActionPreference = 'Stop'\n"
        f"$deepxRoot = '{str(root).replace(chr(39), chr(39) * 2)}'\n"
        f"$deepxPy = '{str(py_exec).replace(chr(39), chr(39) * 2)}'\n"
        "if (-not (Test-Path $deepxPy)) {\n"
        f"    $deepxPy = '{str(fallback_py).replace(chr(39), chr(39) * 2)}'\n"
        "}\n"
        "$env:PYTHONPATH = if ($env:PYTHONPATH) { \"$deepxRoot;$env:PYTHONPATH\" } else { $deepxRoot }\n"
        "& $deepxPy -u -m deepx.main --cwd (Get-Location).Path @args\n"
        "exit $LASTEXITCODE\n"
    )

    cmd_path.write_text(cmd_content, encoding="utf-8", newline="\r\n")
    ps1_path.write_text(ps1_content, encoding="utf-8", newline="\r\n")

    if update_registry:
        _update_user_path_registry(target_bin, remove=False)

    current_path = os.environ.get("PATH", "")
    norm_target = os.path.normcase(os.path.normpath(str(target_bin)))
    existing_parts = [
        os.path.normcase(os.path.normpath(p.strip()))
        for p in current_path.split(os.pathsep)
        if p.strip()
    ]
    if norm_target not in existing_parts:
        os.environ["PATH"] = f"{target_bin}{os.pathsep}{current_path}" if current_path else str(target_bin)

    return True, f"Global command 'deepx' installed ({cmd_path})"


def uninstall_system_command(
    bin_dir: Optional[Path] = None,
    update_registry: bool = True,
) -> tuple[bool, str]:
    target_bin = get_bin_dir(bin_dir)
    removed = False
    for name in ("deepx.cmd", "deepx.ps1"):
        shim = target_bin / name
        if shim.exists():
            shim.unlink()
            removed = True
    if update_registry:
        _update_user_path_registry(target_bin, remove=True)
    if removed:
        return True, f"Global command 'deepx' removed from {target_bin}"
    return True, "Global command 'deepx' was not installed"
