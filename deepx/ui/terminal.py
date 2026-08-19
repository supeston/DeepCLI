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

__all__ = [
    "console",
    "setup_windows_terminal",
    "_begin_windows_ctrl_c_key_mode",
    "_restore_windows_console_mode",
    "_wait_for_windows_control_key",
]

def _begin_windows_ctrl_c_key_mode():
    if sys.platform != "win32":
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
        ctypes.windll.kernel32.SetConsoleMode(state[0], state[1])

async def _wait_for_windows_control_key():
    import msvcrt

    while True:
        if msvcrt.kbhit():
            char = msvcrt.getwch()
            if char == "\x03":
                return "exit"
            if char == "\x18":
                return "stop"
            if char in ("\x00", "\xe0") and msvcrt.kbhit():
                msvcrt.getwch()
        await asyncio.sleep(0.02)

def setup_windows_terminal(cols: int = 140, lines: int = 40, buffer_lines: int = 9999):
                                                                                              
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

    if sys.platform == "win32":
        try:
            kernel32 = ctypes.windll.kernel32
            hOut = kernel32.GetStdHandle(-11)                     
            hIn = kernel32.GetStdHandle(-10)                     
            if hOut != -1 and hOut != 0:
                mode = ctypes.c_ulong()
                if kernel32.GetConsoleMode(hOut, ctypes.byref(mode)):
                    mode.value |= 0x0004                                      
                    kernel32.SetConsoleMode(hOut, mode)

                if hIn != -1 and hIn != 0:
                    in_mode = ctypes.c_ulong()
                    if kernel32.GetConsoleMode(hIn, ctypes.byref(in_mode)):
                        in_mode.value |= 0x0010                      
                        kernel32.SetConsoleMode(hIn, in_mode)

                if not os.environ.get("WT_SESSION"):
                    class COORD(ctypes.Structure):
                        _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]
                    class SMALL_RECT(ctypes.Structure):
                        _fields_ = [("Left", ctypes.c_short), ("Top", ctypes.c_short), ("Right", ctypes.c_short), ("Bottom", ctypes.c_short)]

                    coord = COORD(cols, buffer_lines)
                    kernel32.SetConsoleScreenBufferSize(hOut, coord)
                    rect = SMALL_RECT(0, 0, cols - 1, lines - 1)
                    kernel32.SetConsoleWindowInfo(hOut, True, ctypes.byref(rect))

                                                                        
                                                                                         
            kernel32.GetCurrentProcess.restype = ctypes.c_void_p
            kernel32.TerminateProcess.argtypes = [ctypes.c_void_p, ctypes.c_uint]
            kernel32.TerminateProcess.restype = ctypes.c_bool
            PHANDLER_ROUTINE = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_ulong)
            def on_console_close(ctrl_type):
                if ctrl_type in (2, 5, 6):                                                            
                    process = kernel32.GetCurrentProcess()
                    kernel32.TerminateProcess(process, 0)
                    return True
                return False

            global _console_ctrl_handler
            _console_ctrl_handler = PHANDLER_ROUTINE(on_console_close)
            kernel32.SetConsoleCtrlHandler(_console_ctrl_handler, True)

        except Exception:
            try:
                if not os.environ.get("WT_SESSION"):
                    os.system(f"mode con: cols={cols}")
            except Exception:
                pass

console = Console()
