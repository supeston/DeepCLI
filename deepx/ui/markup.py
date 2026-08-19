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

                                                                                
                    
                                                                                

from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import Terminal256Formatter

BORDER_STYLE = "\033[38;5;240m"
LANG_STYLE = "\033[1;38;5;75m"
_LEXER_CACHE = {}
_CODE_FORMATTER = Terminal256Formatter(style="monokai")

def _get_lexer(lang: str):
    lang_key = (lang or "").strip().lower()
    if lang_key in _LEXER_CACHE:
        return _LEXER_CACHE[lang_key]
    if not lang_key:
        l = TextLexer()
    else:
        try:
            l = get_lexer_by_name(lang_key, stripall=False)
        except Exception:
            l = TextLexer()
    _LEXER_CACHE[lang_key] = l
    return l

def _highlight_code_line(line: str, lang: str = "") -> str:
    if not line:
        return ""
    lexer = _get_lexer(lang)
    res = highlight(line, lexer, _CODE_FORMATTER)
    if res.endswith("\n"):
        res = res[:-1]
    return res

from deepx.core.constants import *
from deepx.core.config import *
from deepx.ui.terminal import console

ANSI_ESCAPE_RE = re.compile(
    r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\)|[@-_])"
)

def sanitize_tool_result(text: str) -> str:
                                                                                          
    text = ANSI_ESCAPE_RE.sub("", str(text))
    return "".join(
        char for char in text
        if char in "\n\r\t" or ord(char) >= 32
    )

def get_clean_text(text: str) -> str:
    text = re.sub(
        r"Чтение ссылок недоступно в Экспертном режиме\.?\s*"
        r"(?:Используйте|Переключитесь на)\s+Быстрый режим\.?",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"(?:Reading|Opening) links? (?:is|are) "
        r"(?:unavailable|not available) in Expert mode\.?\s*"
        r"(?:Use|Switch to) (?:Fast|Instant) mode\.?",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"^Глубокое размышление\s*", "", text, flags=re.IGNORECASE)
                                                                                   
                              
    text = re.sub(r"\s*<tool_call>.*?(?:</tool_call>|$)", "", text, flags=re.DOTALL)
    text = re.sub(r"\s*<tool_calls>.*?(?:</tool_calls>|$)", "", text, flags=re.DOTALL)
    text = re.sub(r"\s*<invoke\b.*?(?:</invoke\s*>|$)", "", text, flags=re.DOTALL)
    
                                                                                 
    text = re.sub(r"\s*```tool_call\s*\n.*?(?:\n```(?=\n|$)|\Z)", "", text, flags=re.DOTALL)
    
                                                             
    text = re.sub(r"\s*```json\s*\n.*?(?:\"tool\"|\"args\").*?(?:\n```(?=\n|$)|\Z)", "", text, flags=re.DOTALL)

    # While streaming, the opening marker arrives character by character
    # (for example "`", "```to", "```tool_call"). Do not print those
    # temporary fragments or their leading blank lines before the complete
    # tool block can be recognized and removed by the expressions above.
    trimmed = text.rstrip()
    for marker in ("```tool_call", "<tool_call>", "<tool_calls>", "<invoke"):
        for prefix_length in range(len(marker), 0, -1):
            prefix = marker[:prefix_length]
            if trimmed.endswith(prefix):
                text = trimmed[:-prefix_length].rstrip()
                break
        else:
            continue
        break

    return text

class StableStreamText:
    """Confirm DOM text across two snapshots without waiting for a newline.

    DeepSeek occasionally rebuilds the tail of its Markdown DOM while a token
    is arriving.  Printing the whole newest snapshot can therefore duplicate
    a rewritten tail, while buffering the last *line* makes long paragraphs
    appear frozen.  The common prefix of two consecutive snapshots is both
    append-safe and normally only one polling interval behind the browser.
    """

    def __init__(self):
        self._previous = ""
        self._committed = ""

    def update(self, text: str) -> str:
        current = str(text or "")
        common_len = 0
        for old_char, new_char in zip(self._previous, current):
            if old_char != new_char:
                break
            common_len += 1
        candidate = current[:common_len]
        if candidate.startswith(self._committed):
            self._committed = candidate
        self._previous = current
        return self._committed


def get_stable_stream_text(text: str) -> str:
    """Legacy line-based helper retained for external callers."""
    if not text:
        return ""
    last_newline = text.rfind("\n")
    return text[:last_newline + 1] if last_newline >= 0 else ""

def render_terminal_markup(text: str, final: bool = False) -> str:
                                                                               
                                                                                             
                                                                                       
    inline_code_style = "\033[38;5;222m"
    styles = {
        "***": "\033[1;3m",
        "**": "\033[1m",
        "~~": "\033[9m",
        "*": "\033[3m",
        "_": "\033[4m",
        "``": inline_code_style,
        "`": inline_code_style,
    }
    reset = "\033[0m"

    def valid_underline_open(source: str, pos: int) -> bool:
        before = source[pos - 1] if pos > 0 else ""
        after = source[pos + 1] if pos + 1 < len(source) else ""
        return (not before.isalnum()) and bool(after) and not after.isspace()

    def find_close(source: str, delimiter: str, start: int) -> int:
        pos = source.find(delimiter, start)
        while pos >= 0:
            if delimiter != "_":
                return pos
            after = source[pos + 1] if pos + 1 < len(source) else ""
            if not after.isalnum():
                return pos
            pos = source.find(delimiter, pos + 1)
        return -1

    def split_table_row(line: str) -> list:
        stripped = line.strip()
        if stripped.startswith("|"):
            stripped = stripped[1:]
        if stripped.endswith("|") and not stripped.endswith("\\|"):
            stripped = stripped[:-1]
        cells = re.split(r"(?<!\\)\|", stripped)
        return [cell.strip().replace("\\|", "|") for cell in cells]

    def table_from(source: str, start: int):
        first_end = source.find("\n", start)
        if first_end < 0:
            return None
        second_start = first_end + 1
        second_end = source.find("\n", second_start)
        if second_end < 0:
            second_end = len(source)
        header = split_table_row(source[start:first_end])
        separators = split_table_row(source[second_start:second_end])
        if (
            len(header) < 2
            or len(separators) != len(header)
            or not all(re.fullmatch(r":?-{3,}:?", cell) for cell in separators)
        ):
            return None

        rows = [header]
        cursor = second_end + (1 if second_end < len(source) else 0)
        while cursor < len(source):
            row_end = source.find("\n", cursor)
            if row_end < 0:
                row_end = len(source)
            line = source[cursor:row_end]
            if not line.strip() or "|" not in line:
                break
            cells = split_table_row(line)
            if len(cells) != len(header):
                break
            rows.append(cells)
            cursor = row_end + (1 if row_end < len(source) else 0)
        return rows, cursor

    def render_markdown_table(rows: list) -> str:
        column_count = len(rows[0])
        cleaned_rows = []
        for row in rows:
            cleaned_rows.append([
                re.sub(r"(\*\*|__|~~|`)", "", cell).replace("\n", " ").strip()
                for cell in row
            ])

        def display_width(value: str) -> int:
            return sum(
                0 if unicodedata.combining(char)
                else 2 if unicodedata.east_asian_width(char) in ("W", "F")
                else 1
                for char in value
            )

        def pad_cell(value: str, width: int) -> str:
            return value + " " * max(0, width - display_width(value))

        terminal_width = max(40, min(getattr(console, "width", 112), 140))
        available = max(column_count * 4, terminal_width - (column_count * 3 + 1))
        natural = [
            max(4, max(display_width(row[index]) for row in cleaned_rows))
            for index in range(column_count)
        ]
        if sum(natural) <= available:
            widths = natural
        else:
            base, extra = divmod(available, column_count)
            widths = [max(4, base + (1 if index < extra else 0)) for index in range(column_count)]

        border_style = "\033[38;5;240m"
        header_style = "\033[1;38;5;255m"
        cell_style = "\033[38;5;252m"
        horizontal = lambda left, middle, right: (
            left + middle.join("─" * (width + 2) for width in widths) + right
        )
        rendered = [border_style, horizontal("┌", "┬", "┐"), reset, "\n"]

        for row_index, row in enumerate(cleaned_rows):
            wrapped = [
                textwrap.wrap(
                    cell,
                    width=widths[index],
                    break_long_words=True,
                    break_on_hyphens=False,
                    replace_whitespace=True,
                ) or [""]
                for index, cell in enumerate(row)
            ]
            height = max(len(lines) for lines in wrapped)
            for line_index in range(height):
                rendered.extend([border_style, "│", reset])
                for column_index, lines in enumerate(wrapped):
                    value = lines[line_index] if line_index < len(lines) else ""
                    style = header_style if row_index == 0 else cell_style
                    rendered.extend([
                        " ",
                        style,
                        pad_cell(value, widths[column_index]),
                        reset,
                        " ",
                        border_style,
                        "│",
                        reset,
                    ])
                rendered.append("\n")
            if row_index == 0:
                rendered.extend([
                    border_style,
                    horizontal("├", "┼", "┤"),
                    reset,
                    "\n",
                ])

        rendered.extend([border_style, horizontal("└", "┴", "┘"), reset])
        return "".join(rendered)

    def parse(source: str, active_styles=()) -> str:
        output = []
        i = 0
        while i < len(source):
            line_start = i == 0 or source[i - 1] == "\n"

            # Tables stay in compact Markdown form.  Building a bordered table
            # changes every previous row whenever a wider cell arrives, which
            # cannot be represented correctly on an append-only terminal and
            # used to freeze the stream until the whole table was complete.

            if line_start and source[i] == "#":
                heading = re.match(r"^(#{1,6})[ \t]+", source[i:])
                if heading:
                    line_end = source.find("\n", i)
                    if line_end < 0 and not final:
                        break
                    if line_end < 0:
                        line_end = len(source)
                    content_start = i + heading.end()
                    heading_style = "\033[1;38;5;255m"
                    output.append(heading_style)
                    output.append(parse(
                        source[content_start:line_end],
                        active_styles + (heading_style,)
                    ))
                    output.append(reset)
                    output.extend(active_styles)
                    if line_end < len(source):
                        output.append("\n")
                    i = line_end + (1 if line_end < len(source) else 0)
                    continue
                if not final and source[i:].strip("#") == "":
                    break

            if line_start and source[i] in "-+":
                if i + 1 >= len(source) and not final:
                    break
                if i + 1 < len(source) and source[i + 1] in " \t":
                    output.append("• ")
                    i += 2
                    while i < len(source) and source[i] in " \t":
                        i += 1
                    continue

            if source[i] == "\\" and i + 1 < len(source) and source[i + 1] in "*_~`\\":
                output.append(source[i + 1])
                i += 2
                continue

            if line_start and source.startswith("```", i):
                fence_m = re.match(r"^```([a-zA-Z0-9_\-\.\+\#]*)[ \t]*(\n|$)", source[i:])
                if fence_m:
                    lang = fence_m.group(1).strip()
                    has_newline = bool(fence_m.group(2))
                    if not has_newline and not final:
                        break
                    
                    code_start = i + fence_m.end()
                    lang_label = lang if lang else "code"
                    border_width = 48
                    bar_len = max(4, border_width - len(lang_label) - 6)
                    output.append(f"{BORDER_STYLE}┌── {LANG_STYLE}{lang_label}{reset} {BORDER_STYLE}{'─' * bar_len}{reset}\n")
                    
                    curr = code_start
                    while curr < len(source):
                        at_line_start = curr == 0 or source[curr - 1] == "\n"
                        if at_line_start and source.startswith("```", curr):
                            closing_m = re.match(r"^```[ \t]*(\n|$)", source[curr:])
                            if closing_m:
                                curr += closing_m.end()
                                output.append(f"{BORDER_STYLE}└──{'─' * (border_width - 3)}{reset}\n")
                                break
                            elif not final:
                                curr = len(source)
                                break
                        
                        next_nl = source.find("\n", curr)
                        if next_nl >= 0:
                            line_content = source[curr:next_nl]
                            if line_content:
                                styled = _highlight_code_line(line_content, lang)
                                output.append(f"{BORDER_STYLE}│{reset} {styled}\n")
                            else:
                                output.append(f"{BORDER_STYLE}│{reset}\n")
                            curr = next_nl + 1
                        else:
                            line_content = source[curr:]
                            if final:
                                if line_content:
                                    styled = _highlight_code_line(line_content, lang)
                                    output.append(f"{BORDER_STYLE}│{reset} {styled}\n")
                                output.append(f"{BORDER_STYLE}└──{'─' * (border_width - 3)}{reset}\n")
                            curr = len(source)
                            break
                    
                    i = curr
                    continue

            delimiter = None
            for candidate in ("***", "**", "~~", "``", "*", "_", "`"):
                if source.startswith(candidate, i):
                    if candidate == "_" and not valid_underline_open(source, i):
                        continue
                    delimiter = candidate
                    break

            if delimiter:
                end = find_close(source, delimiter, i + len(delimiter))
                if end < 0:
                    if final:
                        output.append(source[i + len(delimiter):])
                    break
                content = source[i + len(delimiter):end]
                start_code = styles[delimiter]
                output.append(start_code)
                if delimiter in ("``", "`"):
                                                                                           
                    output.append(content)
                else:
                    output.append(parse(content, active_styles + (start_code,)))
                output.append(reset)
                output.extend(active_styles)
                i = end + len(delimiter)
                continue

            output.append(source[i])
            i += 1
        return "".join(output)

    return parse(text)
