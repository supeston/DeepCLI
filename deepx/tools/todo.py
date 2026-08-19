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
from deepx.parser.tool_parser import _as_int
from deepx.ui.markup import *
from deepx.ui.terminal import console

class TodoToolsMixin:
    TODO_STATUS_ALIASES = {
        "todo": "pending",
        "in_progress": "active",
        "doing": "active",
        "wip": "active",
        "finished": "done",
        "completed": "done",
        "canceled": "cancelled",
    }
    TODO_SYMBOLS = {
        "pending": ("○", "dim #94A3B8"),
        "active": ("●", "bold #FDE68A"),
        "done": ("✔", "bold #22C55E"),
        "cancelled": ("✖", "dim strike #EF4444"),
    }

    def _normalize_todo_status(self, status: str) -> str:
        value = str(status or "pending").strip().lower()
        value = self.TODO_STATUS_ALIASES.get(value, value)
        return value if value in self.TODO_SYMBOLS else "pending"

    def _mark_todo_changed(self) -> str:
                                                                                 
        self._todo_dirty = True
        return self._todo_text()

    def _todo_signature(self):
        return tuple((item["text"], item["status"]) for item in self.todos)

    def _todo_text(self) -> str:
                                                                      
        if not self.todos:
            return "[Task list is empty]"
        done_count = sum(1 for item in self.todos if item["status"] == "done")
        compact = "\n".join(
            f"{i}. [{item['status']}] {item['text']}"
            for i, item in enumerate(self.todos, 1)
        )
        return f"--- Task list ({done_count}/{len(self.todos)} done) ---\n{compact}"

    def flush_todos(self) -> bool:
                                                                                        

                                                                                   
                                                                  
           
        if not self._todo_dirty:
            return False
        self._todo_dirty = False
        signature = self._todo_signature()
        if signature == self._todo_rendered_signature:
            return False
        self._todo_rendered_signature = signature
        self._render_todos()
        return True

    def _render_todos(self) -> str:
                                                                                    
        if not self.todos:
            console.print("[dim #64748B]  Task list is empty.[/dim #64748B]")
            return "[Task list is empty]"

        done_count = sum(1 for item in self.todos if item["status"] == "done")
        total = len(self.todos)
        percent = int(round(done_count * 100 / total))

        lines = []
        for index, item in enumerate(self.todos, 1):
            symbol, color = self.TODO_SYMBOLS[item["status"]]
            number = f"[dim #475569]{index:>2}[/dim #475569]"
            if item["status"] == "done":
                text = f"[dim strike #94A3B8]{item['text']}[/dim strike #94A3B8]"
            elif item["status"] == "active":
                text = f"[bold #FDE68A]{item['text']}[/bold #FDE68A]"
            elif item["status"] == "cancelled":
                text = f"[dim strike #7F1D1D]{item['text']}[/dim strike #7F1D1D]"
            else:
                text = f"[#CBD5E1]{item['text']}[/#CBD5E1]"
            lines.append(f"{number}  [{color}]{symbol}[/{color}]  {text}")

        filled = int(round(percent / 5))
        bar = f"[#536DFE]{'━' * filled}[/#536DFE][#1E293B]{'━' * (20 - filled)}[/#1E293B]"

                                                                                      
                                                                                
        min_inner_width = 34
        widest = max(len(f"{i:>2}  {sym}  {item['text']}")
                     for i, (sym, item) in enumerate(
                         ((self.TODO_SYMBOLS[t["status"]][0], t) for t in self.todos), 1))
        if widest < min_inner_width:
            lines[0] += " " * (min_inner_width - widest)

        panel = Panel(
            "\n".join(lines),
            title=f"[bold #536DFE]TASKS[/bold #536DFE] [dim #64748B]{done_count}/{total}[/dim #64748B]",
            title_align="left",
            subtitle=f"{bar} [bold #536DFE]{percent}%[/bold #536DFE]",
            subtitle_align="right",
            border_style="#536DFE",
            box=box.ROUNDED,
            padding=(0, 2),
            expand=False,
        )
        console.print()
        console.print(panel)
        console.print()

        compact = "\n".join(
            f"{i}. [{item['status']}] {item['text']}"
            for i, item in enumerate(self.todos, 1)
        )
        return f"--- Task list ({done_count}/{total} done) ---\n{compact}"

    def todo(self, action: str = "list", args: dict = None) -> str:
                                                            
        args = args or {}
        action = str(action or "list").strip().lower()

        def _collect_items():
            raw = args.get("items", args.get("tasks", args.get("text", [])))
            if isinstance(raw, str):
                raw = [raw]
            if not isinstance(raw, list):
                return []
            collected = []
            for entry in raw:
                if isinstance(entry, dict):
                    text = str(entry.get("text", entry.get("task", ""))).strip()
                    status = self._normalize_todo_status(entry.get("status", "pending"))
                else:
                    text = str(entry).strip()
                    status = "pending"
                if text:
                    collected.append({"text": text, "status": status})
            return collected

        if action in ("set", "create", "plan", "replace"):
            items = _collect_items()
            if not items:
                return "[Error: todo 'set' requires a non-empty 'items' list]"
            self.todos = items
            return self._mark_todo_changed()

        if action in ("add", "append"):
            items = _collect_items()
            if not items:
                return "[Error: todo 'add' requires a non-empty 'items' list]"
            self.todos.extend(items)
            return self._mark_todo_changed()

        if action in ("update", "status", "complete", "done", "start"):
            if not self.todos:
                return "[Error: task list is empty, call todo 'set' first]"

            def _resolve(spec: dict):
                index = spec.get("index", spec.get("id", spec.get("number")))
                if index is not None:
                    position = _as_int(index, 0)
                    if not 1 <= position <= len(self.todos):
                        return None, f"[Error: task index {index} is out of range 1-{len(self.todos)}]"
                    return self.todos[position - 1], None
                needle = str(spec.get("text", spec.get("task", ""))).strip().lower()
                if not needle:
                    return None, "[Error: todo 'update' requires 'index' or 'text']"
                for item in self.todos:
                    if needle in item["text"].lower():
                        return item, None
                return None, f"[Error: no task matching '{needle}']"

            def _status_for(spec: dict) -> str:
                if action in ("complete", "done"):
                    return "done"
                if action == "start":
                    return "active"
                return self._normalize_todo_status(spec.get("status", "done"))

                                                                                    
                                                                      
            batch = args.get("updates", args.get("changes"))
            specs = batch if isinstance(batch, list) and batch else [args]

            errors = []
            for spec in specs:
                if not isinstance(spec, dict):
                    continue
                target, error = _resolve(spec)
                if error:
                    errors.append(error)
                    continue
                target["status"] = _status_for(spec)
                if spec.get("new_text"):
                    target["text"] = str(spec["new_text"]).strip()

            if errors and len(errors) == len(specs):
                return errors[0]
            summary = self._mark_todo_changed()
            return f"{summary}\n" + "\n".join(errors) if errors else summary

        if action in ("clear", "reset"):
            self.todos = []
            self._todo_dirty = False
            self._todo_rendered_signature = None
            console.print("[dim #64748B]  Task list cleared.[/dim #64748B]")
            return "[Task list cleared]"

        if action in ("list", "show", "get", ""):
                                                               
            self._todo_dirty = False
            self._todo_rendered_signature = self._todo_signature()
            return self._render_todos()

        return f"[Error: unknown todo action '{action}'. Use set, add, update, complete, start, list or clear]"

