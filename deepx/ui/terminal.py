import asyncio
import concurrent.futures
import ctypes
import difflib
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version as package_version
import json
import os
import py_compile
import re
import shutil
import signal
import subprocess
import sys
import textwrap
import threading
import unicodedata
from pathlib import Path

import pyperclip
from prompt_toolkit import PromptSession
from prompt_toolkit.document import Document
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.styles import Style as PTStyle

from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from deepx.api.deep_api import DeepAPI
from deepx.tools.dadata_osint import DadataOSINTTool
from deepx.tools.funstat_osint import FunstatOSINTTool

                                                                                
                    
                                                                                

_console_ctrl_handler = None

from typing import Optional

__all__ = [
    "console",
    "setup_windows_terminal",
    "disable_quick_edit_mode",
    "shutdown_child_processes",
    "is_windows_terminal_session",
    "register_cleanup_callback",
    "read_single_key_confirm",
    "_begin_windows_ctrl_c_key_mode",
    "_restore_windows_console_mode",
    "_wait_for_windows_control_key",
]

_cleanup_callbacks = []
_confirm_active = False


def register_cleanup_callback(fn):
    if callable(fn) and fn not in _cleanup_callbacks:
        _cleanup_callbacks.append(fn)


def _begin_windows_ctrl_c_key_mode():
    if sys.platform != "win32":
        return None
    try:
        if not sys.stdin.isatty():
            return None
    except Exception:
        return None
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-10)
    if handle in (-1, 0):
        return None
    mode = ctypes.c_ulong()
    if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        return None
    if not kernel32.SetConsoleMode(handle, mode.value & ~0x0001):
        return None
    return handle, mode.value


def _restore_windows_console_mode(state):
    if state and sys.platform == "win32":
        try:
            ctypes.windll.kernel32.SetConsoleMode(state[0], state[1])
        except Exception:
            pass


def _peek_and_consume_windows_control_key() -> Optional[str]:
    """Peek Windows console input queue without dropping normal user typing.

    Consumes ONLY Ctrl+C ('exit') or Ctrl+X ('stop'), preserving all other buffered key events.
    """
    if sys.platform != "win32":
        return None
    kernel32 = ctypes.windll.kernel32
    h_in = kernel32.GetStdHandle(-10)
    if h_in in (-1, 0):
        return None

    class KEY_EVENT_RECORD(ctypes.Structure):
        class _Char(ctypes.Union):
            _fields_ = [("UnicodeChar", ctypes.c_wchar), ("AsciiChar", ctypes.c_char)]

        _fields_ = [
            ("bKeyDown", ctypes.c_int),
            ("wRepeatCount", ctypes.c_ushort),
            ("wVirtualKeyCode", ctypes.c_ushort),
            ("wVirtualScanCode", ctypes.c_ushort),
            ("uChar", _Char),
            ("dwControlKeyState", ctypes.c_uint32),
        ]

    class _EventUnion(ctypes.Union):
        _fields_ = [("KeyEvent", KEY_EVENT_RECORD), ("_pad", ctypes.c_byte * 16)]

    class INPUT_RECORD(ctypes.Structure):
        _fields_ = [("EventType", ctypes.c_ushort), ("_pad", ctypes.c_ushort), ("Event", _EventUnion)]

    num_events = ctypes.c_uint32(0)
    if not kernel32.GetNumberOfConsoleInputEvents(h_in, ctypes.byref(num_events)) or num_events.value == 0:
        return None

    count = min(int(num_events.value), 256)
    buf = (INPUT_RECORD * count)()
    peeked = ctypes.c_uint32(0)
    if not kernel32.PeekConsoleInputW(h_in, buf, count, ctypes.byref(peeked)) or peeked.value == 0:
        return None

    action = None
    match_idx = -1
    for idx in range(peeked.value):
        rec = buf[idx]
        if rec.EventType != 0x0001:  # KEY_EVENT
            continue
        ke = rec.Event.KeyEvent
        if not ke.bKeyDown:
            continue
        ch = ke.uChar.UnicodeChar
        ctrl_pressed = bool(ke.dwControlKeyState & 0x000C) and not (ke.dwControlKeyState & 0x0003)
        if ch == "\x03" or (ctrl_pressed and ke.wVirtualKeyCode == 0x43):
            action = "exit"
            match_idx = idx
            break
        if ch == "\x18" or (ctrl_pressed and ke.wVirtualKeyCode == 0x58):
            action = "stop"
            match_idx = idx
            break

    if action is None:
        return None

    # Drain up through match_idx and re-inject non-matching events so normal typing isn't lost
    drain_count = match_idx + 1
    drained = (INPUT_RECORD * drain_count)()
    actually_read = ctypes.c_uint32(0)
    if kernel32.ReadConsoleInputW(h_in, drained, drain_count, ctypes.byref(actually_read)):
        preserved = []
        for idx in range(actually_read.value):
            if idx == match_idx:
                continue
            rec = drained[idx]
            if rec.EventType == 0x0001 and rec.Event.KeyEvent.bKeyDown:
                k_ev = rec.Event.KeyEvent
                ch = k_ev.uChar.UnicodeChar
                ctrl_p = bool(k_ev.dwControlKeyState & 0x000C) and not (k_ev.dwControlKeyState & 0x0003)
                if ch in ("\x03", "\x18") or (ctrl_p and k_ev.wVirtualKeyCode in (0x43, 0x58)):
                    continue
                preserved.append(rec)
        if preserved:
            keep_arr = (INPUT_RECORD * len(preserved))(*preserved)
            written = ctypes.c_uint32(0)
            kernel32.WriteConsoleInputW(h_in, keep_arr, len(preserved), ctypes.byref(written))
    return action


async def _wait_for_windows_control_key():
    while True:
        if not _confirm_active:
            action = _peek_and_consume_windows_control_key()
            if action:
                return action
        await asyncio.sleep(0.03)


def read_single_key_confirm(prompt_text: str) -> bool:
    """Compact single-key confirmation: Enter confirms, Esc (or Ctrl+C) cancels."""
    global _confirm_active

    try:
        is_tty = sys.stdin.isatty()
    except Exception:
        is_tty = False

    sys.stdout.write(f"\r\x1b[2K[?] {prompt_text} [Enter: да / Esc: нет] ")
    sys.stdout.flush()

    if not is_tty:
        line = sys.stdin.readline()
        val = line.strip().lower()
        return val in ("", "y", "yes", "д", "да")

    _confirm_active = True
    try:
        if sys.platform == "win32":
            import msvcrt

            while msvcrt.kbhit():
                msvcrt.getwch()

            while True:
                ch = msvcrt.getwch()
                if ch in ("\r", "\n"):
                    sys.stdout.write("да\n")
                    sys.stdout.flush()
                    return True
                if ch in ("\x1b", "\x03"):
                    sys.stdout.write("отмена\n")
                    sys.stdout.flush()
                    return False
                if ch in ("\x00", "\xe0") and msvcrt.kbhit():
                    msvcrt.getwch()
        else:
            import termios
            import tty

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                termios.tcflush(fd, termios.TCIFLUSH)
                tty.setraw(fd)
                while True:
                    ch = sys.stdin.read(1)
                    if ch in ("\r", "\n"):
                        sys.stdout.write("да\r\n")
                        sys.stdout.flush()
                        return True
                    if ch in ("\x1b", "\x03"):
                        sys.stdout.write("отмена\r\n")
                        sys.stdout.flush()
                        return False
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    finally:
        _confirm_active = False


def is_windows_terminal_session() -> bool:
    return bool(os.environ.get("WT_SESSION"))


def disable_quick_edit_mode() -> bool:
    if sys.platform != "win32":
        return False
    try:
        kernel32 = ctypes.windll.kernel32
        h_in = kernel32.GetStdHandle(-10)
        if h_in in (-1, 0):
            return False
        in_mode = ctypes.c_ulong()
        if not kernel32.GetConsoleMode(h_in, ctypes.byref(in_mode)):
            return False
        # Clear ENABLE_QUICK_EDIT_MODE (0x0040) and ENABLE_MOUSE_INPUT (0x0010), keep ENABLE_EXTENDED_FLAGS (0x0080)
        desired = (in_mode.value & ~0x0040 & ~0x0010) | 0x0080
        if desired == in_mode.value:
            return True
        return bool(kernel32.SetConsoleMode(h_in, desired))
    except Exception:
        return False


def shutdown_child_processes(root_pid: Optional[int] = None) -> int:
    """Terminate all Windows descendant processes cleanly to avoid console-close hangs."""
    if sys.platform != "win32":
        return 0
    target_root = int(root_pid or os.getpid())
    try:
        kernel32 = ctypes.windll.kernel32

        class PROCESSENTRY32W(ctypes.Structure):
            _fields_ = [
                ("dwSize", ctypes.c_uint32),
                ("cntUsage", ctypes.c_uint32),
                ("th32ProcessID", ctypes.c_uint32),
                ("th32DefaultHeapID", ctypes.c_size_t),
                ("th32ModuleID", ctypes.c_uint32),
                ("cntThreads", ctypes.c_uint32),
                ("th32ParentProcessID", ctypes.c_uint32),
                ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", ctypes.c_uint32),
                ("szExeFile", ctypes.c_wchar * 260),
            ]

        snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
        if snapshot in (-1, 0):
            return 0
        children_by_parent: dict[int, list[int]] = {}
        try:
            entry = PROCESSENTRY32W()
            entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
            ok = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
            while ok:
                children_by_parent.setdefault(int(entry.th32ParentProcessID), []).append(int(entry.th32ProcessID))
                ok = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
        finally:
            kernel32.CloseHandle(snapshot)

        descendants: list[int] = []
        queue = list(children_by_parent.get(target_root, ()))
        seen = {target_root}
        while queue:
            pid = queue.pop(0)
            if pid in seen or pid <= 0:
                continue
            seen.add(pid)
            descendants.append(pid)
            queue.extend(children_by_parent.get(pid, ()))

        terminated = 0
        for pid in reversed(descendants):
            handle = kernel32.OpenProcess(0x0001, False, pid)
            if handle:
                try:
                    if kernel32.TerminateProcess(handle, 1):
                        terminated += 1
                finally:
                    kernel32.CloseHandle(handle)
        return terminated
    except Exception:
        return 0


def setup_windows_terminal(cols: int = 140, lines: int = 40, buffer_lines: int = 9999):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    if sys.platform == "win32":
        try:
            kernel32 = ctypes.windll.kernel32
            hOut = kernel32.GetStdHandle(-11)
            hErr = kernel32.GetStdHandle(-12)
            for h_stream in (hOut, hErr):
                if h_stream not in (-1, 0):
                    mode = ctypes.c_ulong()
                    if kernel32.GetConsoleMode(h_stream, ctypes.byref(mode)):
                        mode.value |= 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
                        kernel32.SetConsoleMode(h_stream, mode)

            disable_quick_edit_mode()

            if hOut not in (-1, 0) and sys.stdout.isatty() and not os.environ.get("WT_SESSION"):
                class COORD(ctypes.Structure):
                    _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

                class SMALL_RECT(ctypes.Structure):
                    _fields_ = [
                        ("Left", ctypes.c_short),
                        ("Top", ctypes.c_short),
                        ("Right", ctypes.c_short),
                        ("Bottom", ctypes.c_short),
                    ]

                kernel32.GetLargestConsoleWindowSize.restype = COORD
                largest = kernel32.GetLargestConsoleWindowSize(hOut)
                target_cols = max(80, min(int(cols), int(largest.X))) if largest.X > 0 else int(cols)
                target_lines = max(24, min(int(lines), int(largest.Y))) if largest.Y > 0 else int(lines)
                coord = COORD(target_cols, max(int(buffer_lines), target_lines))
                kernel32.SetConsoleScreenBufferSize(hOut, coord)
                rect = SMALL_RECT(0, 0, target_cols - 1, target_lines - 1)
                kernel32.SetConsoleWindowInfo(hOut, True, ctypes.byref(rect))

            try:
                kernel32.SetProcessShutdownParameters(0x3FF, 0)
            except Exception:
                pass

            PHANDLER_ROUTINE = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_ulong)

            def on_console_close(ctrl_type):
                if ctrl_type in (2, 5, 6):  # CTRL_CLOSE_EVENT, LOGOFF, SHUTDOWN
                    def _run_cleanups():
                        for fn in list(_cleanup_callbacks):
                            try:
                                fn()
                            except Exception:
                                pass

                    worker = threading.Thread(target=_run_cleanups, daemon=True)
                    worker.start()
                    worker.join(timeout=0.25)
                    shutdown_child_processes()
                    os._exit(0)
                    return 1
                return 0

            global _console_ctrl_handler
            _console_ctrl_handler = PHANDLER_ROUTINE(on_console_close)
            kernel32.SetConsoleCtrlHandler(_console_ctrl_handler, True)

        except Exception:
            pass


def _create_console() -> Console:
    if is_windows_terminal_session():
        return Console(color_system="truecolor", soft_wrap=False)
    return Console()


console = _create_console()
