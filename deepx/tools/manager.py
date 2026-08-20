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
from deepx.parser.tool_parser import normalize_tool_args
from deepx.ui.markup import *
from deepx.ui.terminal import console
from .system import SystemToolsMixin
from .filesystem import FileSystemToolsMixin
from .browser import BrowserToolsMixin
from .documents import DocumentsToolsMixin
from .web import WebToolsMixin
from .todo import TodoToolsMixin
from .project import ProjectToolsMixin
from .media_inspector import MediaInspectorMixin
from .clipboard import ClipboardMixin

class AgentTools(
    SystemToolsMixin,
    FileSystemToolsMixin,
    BrowserToolsMixin,
    DocumentsToolsMixin,
    WebToolsMixin,
    TodoToolsMixin,
    ProjectToolsMixin,
    MediaInspectorMixin,
    ClipboardMixin,
):
    def __init__(
        self,
        cwd: str = None,
        browser_state_file: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core", ".deepx_browser_state.json"),
        browser_headless: bool = True
    ):
        self.cwd = os.path.abspath(cwd) if cwd else default_workspace_dir()
                                                                                      
                                                                                         
        self.browser_state_file = os.path.abspath(os.path.join(APP_DIR, browser_state_file))
        self.project_memory_file = os.path.abspath(
            os.path.join(APP_DIR, ".deepx_project_memory.json")
        )
        self.browser_headless = browser_headless
                                                                                           
        self.protect_self = False
        self.extra_protected = set()
        self.todos = []
        self._todo_dirty = False
        self._todo_rendered_signature = None
        self.playwright = None
        self.browser = None
        self.browser_context = None
        self.page = None
        self.browser_timeout = 15000
        self.browser_stealth_status = "not initialized"
        self.active_tasks = {}
        self._background_task_counter = 0
    def add_protected(self, path: str):
                                                                                          
        if path:
            self.extra_protected.add(os.path.realpath(os.path.abspath(os.path.join(APP_DIR, path))))
    def is_protected(self, path: str) -> bool:
                                                                                       

                                                                               
                                                                               
           
        if not path:
            return False
        try:
            real = os.path.realpath(os.path.abspath(os.path.join(self.cwd, str(path))))
        except Exception:
            return True                                               

        if not self.protect_self:
            return False

        if real in self.extra_protected:
            return True

        try:
            relative = os.path.relpath(real, APP_DIR)
        except ValueError:
            return False                                                  
                                                                                          
                                                                               
        return relative == os.curdir or not relative.startswith(os.pardir)
    def _deny(self, path: str) -> str:
        return (
            f"[Access denied: '{path}' belongs to the DEEPX application itself and is "
            "permanently blocked in this agent style. It does not exist for you. "
            "Do not attempt to reach it by another route.]"
        )
    def _command_touches_self(self, text: str) -> bool:
                                                                                          
        if not self.protect_self or not text:
            return False
        lowered = str(text).lower()
        needles = set(SELF_PROTECTED_FILES) | set(SELF_PROTECTED_DIRS)
        needles.update(SELF_PROTECTED_PREFIXES)
        needles.update(os.path.basename(p).lower() for p in self.extra_protected)
        return any(needle in lowered for needle in needles)
    def _process_kill_guard(self, text: str):
        """Reject process-kill commands that can terminate the DEEPX runner."""
        if not text:
            return None

        command = str(text)
        lowered = command.lower()
        agent_pid = os.getpid()

        taskkill_calls = re.findall(
            r"(?:^|[&|])\s*([^&|\r\n]*\btaskkill\b[^&|\r\n]*)",
            lowered,
        )
        for taskkill_call in taskkill_calls:
            if re.search(r"/(?:im|fi)\b", taskkill_call):
                return (
                    "taskkill by image name or filter is blocked because it can "
                    "terminate DEEPX. Use only `taskkill /PID <pid> /F`."
                )
            pid_values = {
                int(value)
                for value in re.findall(r"/pid\s+(\d+)", taskkill_call)
            }
            if not pid_values:
                return (
                    "mass taskkill is blocked because it can terminate DEEPX. "
                    "Find the exact target PID first, then use "
                    "`taskkill /PID <pid> /F`."
                )
            if agent_pid in pid_values:
                return (
                    f"PID {agent_pid} belongs to the active DEEPX process and "
                    "cannot be terminated."
                )

        if re.search(r"\b(?:wmic|pkill|killall)\b.*\b(?:delete|terminate|python)", lowered):
            return (
                "mass process termination is blocked. Find the exact target "
                "PID and terminate only that PID."
            )

        if "stop-process" in lowered:
            pid_values = {
                int(value)
                for value in re.findall(r"(?:-id\s+|stop-process\s+)(\d+)", lowered)
            }
            if not pid_values:
                return (
                    "Stop-Process without an explicit numeric PID is blocked "
                    "because it can terminate DEEPX."
                )
            if agent_pid in pid_values:
                return (
                    f"PID {agent_pid} belongs to the active DEEPX process and "
                    "cannot be terminated."
                )

        direct_kill = re.search(
            r"(?:^|[&|])\s*(?:kill|tskill)\s+(?:-[a-z0-9]+\s+)*(\d+)\b",
            lowered,
        )
        if direct_kill and int(direct_kill.group(1)) == agent_pid:
            return (
                f"PID {agent_pid} belongs to the active DEEPX process and "
                "cannot be terminated."
            )

        return None
    async def execute_tool(self, tool_name: str, args: dict, allowed_tools=None) -> str:
                                            
        args = normalize_tool_args(args or {})
        if allowed_tools is not None and tool_name not in allowed_tools:
            return f"[Error: Tool '{tool_name}' is unavailable in the active agent style]"
        if tool_name == "run_cmd":
            return await asyncio.to_thread(
                self.run_cmd, args.get("command", ""), args.get("inputs", None)
            )
        elif tool_name == "send_input":
            return await asyncio.to_thread(
                self.send_input,
                args.get("session_id", args.get("id", "")),
                args.get("text", args.get("input", "")),
            )
        elif tool_name == "kill_cmd":
            return await asyncio.to_thread(
                self.kill_cmd, args.get("session_id", args.get("id", ""))
            )
        elif tool_name == "run_python":
            return await asyncio.to_thread(self.run_python, args.get("code", ""))
        elif tool_name == "run_background_cmd":
            return await self.run_background_cmd(
                args.get("command", ""), args.get("inputs", None)
            )
        elif tool_name == "task_status":
            return await self.task_status(args.get("id", args.get("task_id", "")))
        elif tool_name == "task_log":
            return await self.task_log(
                args.get("id", args.get("task_id", "")),
                args.get("tail_lines", 200),
            )
        elif tool_name == "todo":
            return self.todo(args.get("action", "list"), args)
        elif tool_name == "web_search":
            return await asyncio.to_thread(
                self.web_search,
                args.get("query", ""),
                args.get("max_results", 10),
                args.get("site", ""),
                args.get("region", "wt-wt"),
            )
        elif tool_name == "funstat_osint":
            return await FunstatOSINTTool().run(
                args.get("action", "free_scan"),
                args.get("telegram_id"),
                args.get("username"),
            )
        elif tool_name == "dadata_osint":
            return await DadataOSINTTool().run(
                action=args.get("action", ""),
                query=args.get("query"),
                lat=args.get("lat"),
                lon=args.get("lon"),
                count=args.get("count", 10),
                options=args.get("options", {}),
            )
        elif tool_name == "fetch_url":
            return await asyncio.to_thread(
                self.fetch_url, args.get("url", ""), args.get("max_chars", 6000)
            )
        elif tool_name == "read_file":
            return await asyncio.to_thread(
                self.read_file,
                args.get("path", ""),
                args.get("start_line", 1),
                args.get("end_line", 500),
            )
        elif tool_name == "write_file":
            return await asyncio.to_thread(
                self.write_file, args.get("path", ""), args.get("content", "")
            )
        elif tool_name == "edit_file":
            return await asyncio.to_thread(
                self.edit_file,
                args.get("path", ""),
                args.get("target", ""),
                args.get("replacement", ""),
                args.get("start_line"),
                args.get("end_line"),
            )
        elif tool_name == "list_dir":
            return await asyncio.to_thread(self.list_dir, args.get("path", "."))
        elif tool_name == "file_info":
            return self.file_info(args.get("path", ""))
        elif tool_name == "project_memory":
            return self.project_memory(args.get("action", "get"), args)
        elif tool_name == "sys_info":
            return self.sys_info()
        elif tool_name == "browser_action":
            return await self.browser_action(args.get("action", ""), args)
        elif tool_name == "render_plan":
            return self.render_plan(args.get("title", "План выполнения задачи"), args.get("steps", []))
        elif tool_name == "make_excel":
            return self.make_excel(args.get("path", ""), args.get("sheets", {}))
        elif tool_name == "make_docx":
            return self.make_docx(args.get("path", ""), args.get("title", "Document"), args.get("paragraphs", []))
        elif tool_name == "make_pptx":
            return self.make_pptx(args.get("path", ""), args.get("title", "Presentation"), args.get("slides", []))
        elif tool_name == "zip_pack":
            return self.zip_pack(args.get("zip_path", ""), args.get("files", []))
        elif tool_name == "unzip_pack":
            return self.unzip_pack(args.get("zip_path", ""), args.get("extract_to", "."))
        elif tool_name == "inspect_media":
            return await asyncio.to_thread(
                self.inspect_media,
                args.get("path", ""),
                args.get("detailed", True),
            )
        elif tool_name == "read_clipboard":
            return await asyncio.to_thread(self.read_clipboard)
        elif tool_name == "write_clipboard":
            return await asyncio.to_thread(
                self.write_clipboard,
                args.get("content", args.get("text", "")),
            )
        elif tool_name == "get_clipboard_history":
            return await self.get_clipboard_history(args.get("limit", 10))
        elif tool_name == "get_clipboard_item":
            return await self.get_clipboard_item(
                index=args.get("index"), item_id=args.get("item_id", args.get("id"))
            )
        elif tool_name == "set_clipboard":
            return await self.set_clipboard(args.get("content", args.get("text", "")))
        elif tool_name == "delete_clipboard_item":
            return await self.delete_clipboard_item(
                index=args.get("index"), item_id=args.get("item_id", args.get("id"))
            )
        elif tool_name == "clear_clipboard_history":
            return await asyncio.to_thread(self.clear_clipboard_history)

        else:
            return f"[Error: Unknown tool '{tool_name}']"
