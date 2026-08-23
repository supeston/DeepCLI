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
from deepx.ui.markup import *
from deepx.ui.terminal import console

class AdaptiveStreamWriter:
    """Adaptive-speed streaming writer.

    Text is pushed via *push()* and consumed by *drain()*.  When the internal
    buffer is large (model is generating faster than we print), characters are
    flushed in bulk.  When we're nearly caught up, a smooth typewriter effect
    is used.

    Usage::

        writer = AdaptiveStreamWriter()
        drain_task = asyncio.create_task(writer.drain())
        ...
        writer.push(new_chars)
        ...
        await writer.finish()   # signals no more data, waits for drain
    """

    def __init__(self):
        self._buf: list[str] = []
        self._buf_len: int = 0
        self._event = asyncio.Event()
        self._drained = asyncio.Event()
        self._done = False

    def push(self, text: str) -> None:
        """Enqueue text for adaptive output."""
        if text:
            self._buf.append(text)
            self._buf_len += len(text)
            self._event.set()

    async def finish(self) -> None:
        """Signal that no more text will arrive and wait until buffer is fully drained."""
        self._done = True
        self._event.set()
        # _buf_len becomes zero as soon as drain() takes ownership of a chunk,
        # not when that chunk has actually reached stdout.  Waiting on it used
        # to let callers cancel drain() halfway through a word.
        await self._drained.wait()

    async def drain(self) -> None:
        """Continuously consume buffered text until finish() is called and buffer is empty."""
        while True:
            # Wait for data or finish signal
            if not self._event.is_set() and not self._done:
                await self._event.wait()
            self._event.clear()

            # Grab all accumulated text at once
            if self._buf:
                text = "".join(self._buf)
                self._buf.clear()
                self._buf_len = 0
                remainder = await self._emit(text)
                if remainder:
                    self._buf.insert(0, remainder)
                    self._buf_len += len(remainder)
            elif self._done:
                self._drained.set()
                break

    async def _emit(self, text: str) -> str:
        """Output *text* with adaptive speed based on how much is left in the buffer.
        Returns any leftover unparsed incomplete ANSI escape sequence.
        """
        total = len(text)
        index = 0

        while index < total:
            # --- ANSI escape: always emit whole sequence, no delay ---
            if text[index] == "\x1b":
                match = ANSI_ESCAPE_RE.match(text, index)
                if match:
                    sys.stdout.write(match.group(0))
                    sys.stdout.flush()
                    index = match.end()
                    continue
                elif not self._done:
                    # Incomplete ANSI sequence at end of string: save remainder for next chunk
                    return text[index:]

            chars_in_text = total - index
            chars_in_queue = self._buf_len
            chars_left = chars_in_text + chars_in_queue

            # When significantly behind, stream in small fast batches (4-6 chars) with micro-delay
            if chars_left > 100:
                chunk_size = min(6, total - index)
                end = index + chunk_size
                while end < total and text[end] == "\x1b":
                    m = ANSI_ESCAPE_RE.match(text, end)
                    if m:
                        end = m.end()
                    else:
                        break
                sys.stdout.write(text[index:end])
                sys.stdout.flush()
                index = end
                await asyncio.sleep(0.001)
                continue

            if chars_left > 25:
                chunk_size = min(2, total - index)
                end = index + chunk_size
                while end < total and text[end] == "\x1b":
                    m = ANSI_ESCAPE_RE.match(text, end)
                    if m:
                        end = m.end()
                    else:
                        break
                sys.stdout.write(text[index:end])
                sys.stdout.flush()
                index = end
                await asyncio.sleep(STREAM_CHAR_DELAY_MAX / 2)
                continue

            # Smooth typewriter mode: we're caught up
            char = text[index]
            sys.stdout.write(char)
            sys.stdout.flush()
            index += 1

            delay = STREAM_CHAR_DELAY_MAX
            if char in ".!?,;:":
                delay += STREAM_PUNCTUATION_DELAY
            elif char == "\n":
                delay += STREAM_PUNCTUATION_DELAY / 2
            await asyncio.sleep(delay)

        return ""

async def write_streaming_chars(text: str, remaining: int = 0):
    """Outputs text adaptively with smooth progressive pacing."""
    total = len(text)
    index = 0

    while index < len(text):
        if text[index] == "\x1b":
            match = ANSI_ESCAPE_RE.match(text, index)
            if match:
                sys.stdout.write(match.group(0))
                sys.stdout.flush()
                index = match.end()
                continue

        chars_left = total - index + remaining
        if chars_left > 100:
            chunk_size = min(6, total - index)
            end = index + chunk_size
            while end < total and text[end] == "\x1b":
                m = ANSI_ESCAPE_RE.match(text, end)
                if m:
                    end = m.end()
                else:
                    break
            sys.stdout.write(text[index:end])
            sys.stdout.flush()
            index = end
            await asyncio.sleep(0.001)
            continue

        if chars_left > 25:
            chunk_size = min(2, total - index)
            end = index + chunk_size
            while end < total and text[end] == "\x1b":
                m = ANSI_ESCAPE_RE.match(text, end)
                if m:
                    end = m.end()
                else:
                    break
            sys.stdout.write(text[index:end])
            sys.stdout.flush()
            index = end
            await asyncio.sleep(STREAM_CHAR_DELAY_MAX / 2)
            continue

        char = text[index]
        sys.stdout.write(char)
        sys.stdout.flush()
        index += 1

        delay = STREAM_CHAR_DELAY_MAX
        if char in ".!?,;:":
            delay += STREAM_PUNCTUATION_DELAY
        elif char == "\n":
            delay += STREAM_PUNCTUATION_DELAY / 2
        await asyncio.sleep(delay)

