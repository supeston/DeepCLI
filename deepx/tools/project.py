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

class ProjectToolsMixin:
    def _load_project_memory(self) -> dict:
                                                                           
        default = {
            "version": 1,
            "project": os.path.basename(self.cwd),
            "updated_at": None,
            "summary": "",
            "current_task": "",
            "completed": [],
            "next_steps": [],
            "important_files": [],
            "facts": [],
            "events": [],
        }
        if not os.path.exists(self.project_memory_file):
            return default
        try:
            with open(self.project_memory_file, "r", encoding="utf-8") as file:
                stored = json.load(file)
            if not isinstance(stored, dict):
                raise ValueError("memory root must be an object")
            for key, value in default.items():
                stored.setdefault(key, value)
            return stored
        except Exception as error:
            raise RuntimeError(f"Cannot read project memory: {error}") from error

    def _save_project_memory(self, memory: dict):
                                                                                          
        memory["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        temp_path = self.project_memory_file + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(memory, file, ensure_ascii=False, indent=2)
            file.write("\n")
        os.replace(temp_path, self.project_memory_file)

    @staticmethod
    def _memory_list(value, name: str) -> list:
        if value is None:
            return []
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list):
            raise ValueError(f"{name} must be a list")
        return [str(item).strip() for item in value if str(item).strip()]

    def project_memory(self, action: str, args: dict) -> str:
                                                                               
        action = (action or "get").strip().lower()
        try:
            memory = self._load_project_memory()
            if action in ("get", "view", "status"):
                return json.dumps(memory, ensure_ascii=False, indent=2)

            if action == "update":
                scalar_fields = ("summary", "current_task")
                list_fields = ("completed", "next_steps", "important_files", "facts")
                for field in scalar_fields:
                    if field in args:
                        memory[field] = str(args[field]).strip()
                for field in list_fields:
                    if field in args:
                        memory[field] = self._memory_list(args[field], field)
                self._save_project_memory(memory)
                return f"[Success: Project memory updated at '{self.project_memory_file}']"

            if action in ("append_event", "log"):
                event = {
                    "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "task": str(args.get("task", "")).strip(),
                    "result": str(args.get("result", "")).strip(),
                    "status": str(args.get("status", "completed")).strip() or "completed",
                    "files": self._memory_list(args.get("files", []), "files"),
                }
                if not event["task"] or not event["result"]:
                    return "[Error: append_event requires non-empty task and result]"
                memory["events"].append(event)
                memory["events"] = memory["events"][-50:]
                self._save_project_memory(memory)
                return f"[Success: Project event recorded ({len(memory['events'])} retained)]"

            return "[Error: project_memory action must be get, update, or append_event]"
        except Exception as error:
            return f"[Error in project_memory: {error}]"

