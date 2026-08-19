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

                                                                                
                    
                                                                                

from deepx.core.constants import *
from deepx.core.config import *
from deepx.ui.terminal import console

DEEPX_ASCII_ART = """\
██████╗ ███████╗███████╗██████╗ ██╗  ██╗
██╔══██╗██╔════╝██╔════╝██╔══██╗╚██╗██╔╝
██║  ██║█████╗  █████╗  ██████╔╝ ╚███╔╝
██║  ██║██╔══╝  ██╔══╝  ██╔═══╝  ██╔██╗
██████╔╝███████╗███████╗██║     ██╔╝ ██╗
╚═════╝ ╚══════╝╚══════╝╚═╝     ╚═╝  ╚═╝"""

BANNER_WIDTH = 100

def render_banner(
    mode: str,
    style: str,
    think: bool,
    search: bool,
    status_message: str | None = None,
):
                                                                                 
    grid = Table.grid(expand=True)
    grid.add_column(justify="center")

    title = Text(DEEPX_ASCII_ART, style="bold #536DFE", end="")

    if status_message:
        status_line = f"[bold #F8FAFC]{status_message}[/bold #F8FAFC]"
    else:
        mode_val = f"[bold #38BDF8]{mode.upper()}[/bold #38BDF8]"
        style_label = STYLE_CONFIGS.get(style, STYLE_CONFIGS["coder"])["label"]
        style_val = f"[bold #A78BFA]{style_label}[/bold #A78BFA]"
        think_val = "[bold #38BDF8]ON[/bold #38BDF8]" if think else "[dim #64748B]OFF[/dim #64748B]"
        if mode == "expert":
            status_line = f"Mode: {mode_val}  |  Style: {style_val}  |  DeepThink: {think_val}"
        else:
            search_val = "[bold #38BDF8]ON[/bold #38BDF8]" if search else "[dim #64748B]OFF[/dim #64748B]"
            status_line = f"Mode: {mode_val}  |  Style: {style_val}  |  DeepThink: {think_val}  |  Search: {search_val}"

    grid.add_row(title)
    grid.add_row(Text(""))
    grid.add_row(Text.from_markup(status_line))

    panel = Panel(
        grid,
        border_style="#536DFE",
        padding=(1, 4),
        width=BANNER_WIDTH,
        expand=True,
        box=box.ROUNDED,
    )
    console.print(Align.center(panel))

def print_help():
                                                       
    table = Table(title="DEEPX COMMANDS", border_style="#536DFE", header_style="bold #536DFE")
    table.add_column("Command", style="bold #536DFE", width=28)
    table.add_column("Description", style="white")

    for cmd, desc in COMMANDS_DICT.items():
        table.add_row(f"/{cmd}", desc)

    console.print(table)
    console.print(
        "[bold #EF4444]Правый Ctrl (удерживать 0,5 секунды)[/bold #EF4444] — "
        "локальная запись речи; отпусти Ctrl, затем нажми Enter для отправки."
    )

def print_status(mode: str, style: str, think: bool, search: bool, cwd: str, state_file: str):
                                        
    grid = Table.grid(expand=True)
    grid.add_column(style="bold #536DFE", width=22)
    grid.add_column(style="white")

    grid.add_row("Model Mode:", mode.upper())
    grid.add_row("Agent Style:", STYLE_CONFIGS.get(style, STYLE_CONFIGS["coder"])["label"])
    grid.add_row("DeepThink Engine:", "Enabled" if think else "Disabled")
    if mode != "expert":
        grid.add_row("Smart Web Search:", "Enabled" if search else "Disabled")
    grid.add_row("Working Directory:", cwd)
    grid.add_row("Session State:", state_file)

    console.print(Panel(grid, title="SESSION STATUS", border_style="#536DFE"))
