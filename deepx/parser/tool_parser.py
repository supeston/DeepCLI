import asyncio
import concurrent.futures
import ctypes
import difflib
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version as package_version
import json
import html
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

def parse_json_lenient(json_str: str):
    """
    Robust JSON parser for tool calls. Supports:
    - Standard JSON
    - Unescaped newlines and tabs inside multiline strings (strict=False)
    - Triple quoted strings inside JSON
    - Unescaped Windows backslashes in paths (C:\\path or C:\\path\\telegram)
    - Trailing commas before closing braces/brackets
    """
    if not json_str or not json_str.strip():
        return None

    def fix_windows_paths(text: str) -> str:
        def replace_path(m):
            key = m.group(1)
            val = m.group(2)
            val_fixed = re.sub(r'\\([a-zA-Z0-9_\-\.])', r'/\1', val)
            return f'{key}"{val_fixed}"'
        return re.sub(r'("path"\s*:\s*)"([^"]+)"', replace_path, text)

    s = fix_windows_paths(json_str)

    def replace_triple_quotes(match):
        prefix = match.group(1)
        val_content = match.group(2)
        val_escaped = val_content.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        return f'{prefix}"{val_escaped}"'

    s = re.sub(r'("[\w_]+"\s*:\s*)"""(.*?)"""', replace_triple_quotes, s, flags=re.DOTALL)
    s = re.sub(r"('[\w_]+'\s*:\s*)'''(.*?)'''", replace_triple_quotes, s, flags=re.DOTALL)
    s_no_trailing = re.sub(r',\s*([\}])', r'\1', s)

    try:
        return json.loads(s_no_trailing, strict=False)
    except Exception:
        pass

    try:
        fixed = re.sub(r'\\(?![\\"/bfnrtu])', r'\\\\', s_no_trailing)
        return json.loads(fixed, strict=False)
    except Exception:
        pass

    try:
        def replace_newlines_in_strings(match):
            val = match.group(0)
            val_escaped = val.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
            return val_escaped

        repaired = re.sub(r'"([^"\\]*(\\.[^"\\]*)*)"', replace_newlines_in_strings, s_no_trailing, flags=re.DOTALL)
        repaired = re.sub(r'\\(?![\\"/bfnrtu])', r'\\\\', repaired)
        return json.loads(repaired, strict=False)
    except Exception:
        return None

def extract_tool_calls(text: str):
                                                                                                 
    calls = []

    # DeepSeek Expert sometimes emits the native function-call XML used by
    # other clients instead of DEEPX's documented JSON envelope:
    # <tool_calls><invoke name="read_file"><parameter name="path">...</parameter>
    # </invoke></tool_calls>.  Accept it so the call is executed rather than
    # leaked to the terminal as ordinary assistant text.
    invoke_matches = re.findall(
        r"<invoke\b[^>]*\bname\s*=\s*(['\"])(.*?)\1[^>]*>(.*?)</invoke\s*>",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    for _, tool_name, invoke_body in invoke_matches:
        args = {}
        parameter_matches = re.findall(
            r"<parameter\b[^>]*\bname\s*=\s*(['\"])(.*?)\1[^>]*>(.*?)</parameter\s*>",
            invoke_body,
            re.DOTALL | re.IGNORECASE,
        )
        for _, parameter_name, raw_value in parameter_matches:
            value = raw_value.strip()
            cdata = re.fullmatch(r"<!\[CDATA\[(.*)\]\]>", value, re.DOTALL)
            if cdata:
                value = cdata.group(1)
            args[html.unescape(parameter_name.strip())] = html.unescape(value)
        call_obj = {
            "tool": html.unescape(tool_name.strip()),
            "args": args,
        }
        if call_obj["tool"] and call_obj not in calls:
            calls.append(call_obj)
    
                                            
    xml_matches = re.findall(r"<tool_call>\s*(.*?)\s*</tool_call>", text, re.DOTALL)
    for match in xml_matches:
        match_str = match.strip()
        cleaned = re.sub(r"^```(?:\w+)?\s*", "", match_str)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()
        data = parse_json_lenient(cleaned)
        if isinstance(data, dict) and "tool" in data:
            if data not in calls:
                calls.append(data)
            continue

        tool_m = re.search(r"^tool:\s*(\w+)", cleaned, re.MULTILINE)
        if tool_m:
            tool_name = tool_m.group(1).strip()
            path_m = re.search(r"^path:\s*(.+)$", cleaned, re.MULTILINE)
            cmd_m = re.search(r"^command:\s*(.+)$", cleaned, re.MULTILINE)

            code_block_m = re.search(r"```(?:\w+)?\s*\n(.*)\n```", cleaned, re.DOTALL)

            args = {}
            if path_m:
                args["path"] = path_m.group(1).strip()
            if cmd_m:
                args["command"] = cmd_m.group(1).strip()

            if code_block_m:
                args["content"] = code_block_m.group(1)
            elif "content:" in cleaned:
                cont_parts = cleaned.split("content:", 1)
                raw_cont = cont_parts[1].lstrip("\n\r")
                raw_cont = re.sub(r"```(?:\w+)?\s*\n(.*)\n```$", r"\1", raw_cont, flags=re.DOTALL).strip()
                if raw_cont.startswith("```"):
                    raw_cont = re.sub(r"^```(?:\w+)?\n?(.*?)\n?```$", r"\1", raw_cont, flags=re.DOTALL)
                args["content"] = raw_cont

            call_obj = {"tool": tool_name, "args": args}
            if call_obj not in calls:
                calls.append(call_obj)

                                                      
    md_matches = re.findall(r"```tool_call\s*\n?(.*?)\n?```", text, re.DOTALL)
    for match in md_matches:
        match_str = match.strip()
        cleaned = re.sub(r"^<tool_call>\s*", "", match_str)
        cleaned = re.sub(r"\s*</tool_call>$", "", cleaned).strip()
        data = parse_json_lenient(cleaned)
        if isinstance(data, dict) and "tool" in data and data not in calls:
            calls.append(data)

                                    
    json_matches = re.findall(r"```json\s*\n?(.*?)\n?```", text, re.DOTALL)
    for match in json_matches:
        match_str = match.strip()
        cleaned = re.sub(r"^<tool_call>\s*", "", match_str)
        cleaned = re.sub(r"\s*</tool_call>$", "", cleaned).strip()
        data = parse_json_lenient(cleaned)
        if isinstance(data, dict) and "tool" in data and data not in calls:
            calls.append(data)

    return normalize_tool_calls(calls)

_ARG_ALIASES = {
    "file_path": "path",
    "filepath": "path",
    "filename": "path",
    "file": "path",
    "dir": "path",
    "directory": "path",
    "offset": "start_line",
    "start": "start_line",
    "from_line": "start_line",
    "limit": "end_line",
    "end": "end_line",
    "to_line": "end_line",
    "cmd": "command",
    "shell": "command",
    "q": "query",
    "search_query": "query",
    "link": "url",
    "text": "content",
    "data": "content",
    "script": "code",
    "python_code": "code",
    "py_code": "code",
    "source": "code",
}

def normalize_tool_args(args: dict) -> dict:
    if not isinstance(args, dict):
        return {}
    fixed = {}
    for key, value in args.items():
        canonical = _ARG_ALIASES.get(key, key)
        if canonical in fixed and canonical != key:
            continue
        fixed[canonical] = value

    for code_key in ("code", "content", "command"):
        if code_key in fixed and isinstance(fixed[code_key], str):
            val = fixed[code_key]
            if "\\n" in val and "\n" not in val.strip():
                fixed[code_key] = val.replace("\\n", "\n").replace("\\t", "    ")

    return fixed

def _as_int(value, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback

def normalize_tool_calls(calls: list) -> list:
                                                                                       

                                                                                     
                                                                                      
                                                                                     
       
    normalized = []
    for call in calls:
        if not isinstance(call, dict) or "tool" not in call:
            continue
        raw_args = call.get("args")
        if not isinstance(raw_args, dict):
            raw_args = call.get("arguments")
        if not isinstance(raw_args, dict):
            raw_args = call.get("kwargs")
        if not isinstance(raw_args, dict):
            raw_args = {}
        normalized.append({
            "tool": call.get("tool"),
            "args": normalize_tool_args(raw_args),
        })

    merged = []
    read_index = {}
    for call in normalized:
        if call["tool"] != "read_file" or not call["args"].get("path"):
            if call not in merged:
                merged.append(call)
            continue

        args = call["args"]
        path = args["path"]
        start = max(1, _as_int(args.get("start_line", 1), 1))
        end = _as_int(args.get("end_line", start + MAX_READ_LINES - 1), start + MAX_READ_LINES - 1)
        if end < start:
            start, end = end, start

        if path in read_index:
            target = merged[read_index[path]]["args"]
            target["start_line"] = min(target["start_line"], start)
            target["end_line"] = max(target["end_line"], end)
        else:
            read_index[path] = len(merged)
            merged.append({
                "tool": "read_file",
                "args": {"path": path, "start_line": start, "end_line": end},
            })

    return merged

def count_tokens(text: str) -> int:
                                                                              
    if not text:
        return 0
    tokens = re.findall(r'\w+|\S', text)
    return len(tokens)
