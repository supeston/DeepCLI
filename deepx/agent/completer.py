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

                                                                                
                    
                                                                                

from deepx.core.config import COMMANDS_DICT

class SlashCommandCompleter(Completer):
                                                                     
    def __init__(self, commands: dict):
        self.commands = commands

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text.startswith("/"):
            query = text[1:].lower()
            for cmd, desc in self.commands.items():
                if cmd.lower().startswith(query):
                    yield Completion(
                        f"/{cmd}",
                        start_position=-len(text),
                        display=f"/{cmd}",
                        display_meta=desc
                    )
