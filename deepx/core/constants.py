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

                                                                                
                    
                                                                                

MAX_READ_LINES = 1200
                                                                          
MAX_TOOL_FEEDBACK_CHARS = 60000
                                                                                         
TODO_NUDGE_AFTER_TOOLS = 4
                                                                                         
MAX_EMPTY_RESPONSE_RETRIES = 2
# The conversation already contains the original request. Repeat it only
# occasionally during unusually long autonomous runs to prevent goal drift.
TASK_GOAL_REMINDER_INTERVAL = 8

# Agent execution discipline. These rules are injected by the runner and do
# not modify the editable base prompts.
AGENT_EXECUTION_PROTOCOL = """
АГЕНТНЫЙ ЦИКЛ (ОБЯЗАТЕЛЬНО):
1. Перед каждым действием определи: что сейчас неизвестно, какое действие это
   проверит и какой наблюдаемый результат будет доказательством успеха.
2. После каждого результата инструмента сравни ожидание с фактическим выводом.
   Не считай предположение подтверждённым без наблюдаемого результата.
3. Код или файл, который только записан, ещё не готов. Перед завершением выполни
   релевантную проверку результата: тест, запуск, чтение, инспекцию или иную
   проверку, подходящую исходной задаче.
4. Две одинаковые неудачи подряд означают, что нужно изменить способ решения,
   а не повторять то же действие.
5. Финальный ответ разрешён только когда исходная цель выполнена и это
   подтверждается результатами инструментов. Если проверка невозможна, честно
   назови непроверенную часть вместо заявления об успехе.
6. МНОГОСТРОЧНЫЙ КОД: Для полей code, content, target, replacement ВСЕГДА 
   используй тройные кавычки \"\"\" вместо обычных \". Это позволяет писать код
   нормально, каждую строку с новой строки. ЗАПРЕЩЕНО писать код в одну строку 
   через \n! Пример: "content": \"\"\"\nprint('hello')\nprint('world')\n\"\"\"
7. ЗАПРЕТ ХОЛОСТЫХ ОБЕЩАНИЙ: Никогда не завершай сообщение словами «сейчас проверю»,
   «установлю», «проверю менеджеры» и т.п. без одновременного вызова ```tool_call.
   Если требуется действие — СРАЗУ вызывай нужный инструмент в этом же ответе.
Не пересказывай внутренний ход рассуждений. Показывай пользователю действия,
проверяемые результаты и выводы.
""".strip()

MUTATING_TOOLS_REQUIRING_VERIFICATION = {
    "write_file",
    "edit_file",
    "make_excel",
    "make_docx",
    "make_pptx",
    "zip_pack",
    "unzip_pack",
}

VERIFICATION_TOOLS = {
    "read_file",
    "file_info",
    "inspect_media",
    "run_cmd",
    "send_input",
    "run_python",
    "task_status",
    "task_log",
    "browser_action",
    "fetch_url",
    "vds_deploy",
}

# Calls in the same contiguous read-only batch can safely run concurrently.
# Mutating tools remain ordering barriers so a later read observes earlier writes.
PARALLEL_READ_ONLY_TOOLS = {
    "read_file",
    "file_info",
    "inspect_media",
    "read_clipboard",
    "get_clipboard_history",
    "get_clipboard_item",
    "web_search",
    "fetch_url",
    "dadata_osint",
    "list_dir",
}

MAX_BACKGROUND_LOG_CHARS = 1_000_000
FILE_PROGRESS_MIN_SECONDS = 0.32
FILE_PROGRESS_FRAME_SECONDS = 0.08
FILE_PROGRESS_FRAMES = ("|", "/", "-", "\\")
FILE_VISUAL_TOOL_NAMES = {
    "write_file",
    "edit_file",
    "make_excel",
    "make_docx",
    "make_pptx",
}

# Adaptive streaming: speed adjusts based on how far behind the console is
# relative to the model's output.  When buffer is small (we're caught up),
# use the slow "typewriter" delay for visual effect.  When buffer is large
# (model is ahead), ramp down to zero delay so we catch up quickly.
STREAM_CHAR_DELAY_MAX = 0.004       # per-char delay when fully caught up
STREAM_PUNCTUATION_DELAY = 0.008    # extra pause on sentence-ending chars
STREAM_ADAPTIVE_THRESHOLD = 60      # chars remaining below which we animate
STREAM_BULK_CHUNK = 120             # when far behind, write this many chars at once
SELF_PROTECTED_FILES = {
    "deep_cli.py",
    "deep_api.py",
    "dadata_osint.py",
    "funstat_osint.py",
    "run_cli.vbs",
}
                                                                                   
SELF_PROTECTED_PREFIXES = ("system_prompt", ".deepx", ".env", "state.json")
                                         
SELF_PROTECTED_DIRS = {"__pycache__"}
