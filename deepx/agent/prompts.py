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
from deepx.tools.manager import AgentTools

SYSTEM_PROMPT_FILE = Path(__file__).resolve().parent.parent / "core" / "system_prompt.txt"

SYSTEM_PROMPT_NOTHINK_FILE = Path(__file__).resolve().parent.parent / "core" / "system_prompt_nothink.txt"

def load_agent_system_prompt_base(think: bool = True) -> str:
                                                                                             
    prompt_file = SYSTEM_PROMPT_FILE if think else SYSTEM_PROMPT_NOTHINK_FILE
    if not think and not prompt_file.exists():
        prompt_file = SYSTEM_PROMPT_FILE
    try:
        prompt = prompt_file.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise RuntimeError(
            f"Cannot load editable system prompt '{prompt_file}': {error}"
        ) from error
    if not prompt:
        raise RuntimeError(f"Editable system prompt '{prompt_file}' is empty")
    return prompt

def normalize_style_name(value: str):
    name = (value or "").strip().lower()
    if name in STYLE_CONFIGS:
        return name
    return STYLE_ALIASES.get(name)

def build_agent_system_prompt(style: str, think: bool = True, workspace: str = None) -> str:
                                                                                    
    style = normalize_style_name(style) or "coder"
    config = STYLE_CONFIGS[style]
    workspace = workspace or default_workspace_dir()
    tool_lines = [
        TOOL_DESCRIPTIONS[name]
        for name in sorted(config["tools"])
        if name in TOOL_DESCRIPTIONS
    ]
    return (
        f"{load_agent_system_prompt_base(think)}\n\n"
        f"{AGENT_EXECUTION_PROTOCOL}\n\n"
        f"{config['instructions'].strip()}\n\n"
        "РАБОЧАЯ ДИРЕКТОРИЯ:\n"
        f"{workspace}\n"
        "Все относительные пути отсчитываются отсюда. Не предполагай другую папку и не выясняй её "
        "командами — если нужен файл, ищи от этого пути через list_dir.\n\n"
        "ПАМЯТЬ ПРОЕКТА:\n"
        "У тебя есть постоянная память только для текущей рабочей папки. Перед сложной, "
        "многошаговой задачей, продолжением прежней работы или если контекст неясен, сам вызови "
        "project_memory с action=get и опирайся на фактически сохранённые сведения. После важного "
        "завершённого этапа сохраняй короткий подтверждённый итог через append_event; когда меняются "
        "цель, текущая задача, факты или следующие шаги — обновляй сводку через update. Не записывай "
        "догадки, пароли, токены, полные сырые логи и личные данные без необходимости.\n\n"
        "ДОСТУПНЫЕ ИНСТРУМЕНТЫ "
        "(ВЫЗЫВАЙ ТОЛЬКО ЧЕРЕЗ ```tool_call):\n"
        + "\n".join(tool_lines)
    )

def _compact_task_text(value: str, limit: int = 1200) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[:limit] + f"... (+{len(text) - limit} chars)"

def _tool_result_failed(result: str) -> bool:
    lowered = str(result or "").lower()
    return any(marker in lowered for marker in (
        "[error",
        "[exit code:",
        "syntax check failed",
        "traceback (most recent call last)",
    ))

tool_result_failed = _tool_result_failed

def build_agent_task_state(
    goal: str,
    todos: list,
    pending_verification: bool = False,
    strategy_change_required: bool = False,
    include_goal: bool = False,
) -> str:
    active = [
        str(item.get("text", "")).strip()
        for item in todos
        if item.get("status") == "active" and str(item.get("text", "")).strip()
    ]
    pending = [
        str(item.get("text", "")).strip()
        for item in todos
        if item.get("status") == "pending" and str(item.get("text", "")).strip()
    ]
    lines = []
    if include_goal:
        lines.append(f"Напоминание цели: {_compact_task_text(goal, 1200)}")
    if active:
        lines.append(f"Активный шаг: {_compact_task_text(active[0], 400)}")
    elif pending:
        lines.append(f"Следующий шаг: {_compact_task_text(pending[0], 400)}")
    if pending_verification:
        lines.append(
            "После изменения артефакта обязательная проверка ещё не выполнена."
        )
    if strategy_change_required:
        lines.append(
            "Одинаковая ошибка повторилась: смени подход и не повторяй тот же вызов."
        )
    if not lines:
        return ""
    return "\n[КРАТКОЕ СОСТОЯНИЕ]\n" + "\n".join(lines) + "\n[КОНЕЦ СОСТОЯНИЯ]\n"
