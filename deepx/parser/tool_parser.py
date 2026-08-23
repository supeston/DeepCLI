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
    - Missing 'tool': key (e.g. {"run_cmd", "args": {...}} or {'run_cmd', 'args': ...})
    - Unescaped Windows backslashes in paths (C:\\path or C:\\path\\telegram)
    - Trailing commas before closing braces/brackets
    - Single quoted strings and Python literals
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

    s = fix_windows_paths(json_str.strip())

    # Fix malformed missing "tool": key (e.g. {"run_cmd", "args": {...}} or {'run_cmd', 'args': ...})
    s = re.sub(
        r'\{\s*(["\'])([a-zA-Z0-9_\-]+)\1\s*,\s*(["\'])(args|arguments|parameters|params|kwargs|action_input|command|path|code|content)\3\s*:',
        r'{"tool": "\2", "\4":',
        s,
    )
    # Fix standalone tool name as first key-less entry: {"run_cmd", ...}
    s = re.sub(
        r'\{\s*(["\'])([a-zA-Z0-9_\-]+)\1\s*,\s*',
        r'{"tool": "\2", ',
        s,
    )

    def replace_triple_quotes(match):
        prefix = match.group(1)
        val_content = match.group(2)
        val_escaped = val_content.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        return f'{prefix}"{val_escaped}"'

    s = re.sub(r'("[\w_]+"\s*:\s*)"""(.*?)"""', replace_triple_quotes, s, flags=re.DOTALL)
    s = re.sub(r"('[\w_]+'\s*:\s*)'''(.*?)'''", replace_triple_quotes, s, flags=re.DOTALL)
    s_no_trailing = re.sub(r',\s*([\}\]])', r'\1', s)

    # Replace Python True/False/None if unquoted
    s_no_trailing = re.sub(r'\bTrue\b', 'true', s_no_trailing)
    s_no_trailing = re.sub(r'\bFalse\b', 'false', s_no_trailing)
    s_no_trailing = re.sub(r'\bNone\b', 'null', s_no_trailing)

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
        pass

    try:
        single_to_double = re.sub(r"'([^'\\]*(?:\\.[^'\\]*)*)'", r'"\1"', s_no_trailing)
        return json.loads(single_to_double, strict=False)
    except Exception:
        return None


def _dict_to_tool_call(data: dict):
    if not isinstance(data, dict):
        return None

    # Check for direct 'tool' or aliases
    for tool_key in ("tool", "name", "function", "action", "tool_name"):
        if tool_key in data and isinstance(data[tool_key], str):
            tool_name = data[tool_key].strip()
            args = None
            for args_key in ("args", "arguments", "parameters", "params", "kwargs", "action_input"):
                if args_key in data:
                    args = data[args_key]
                    break
            if args is None:
                # Flat args
                args = {k: v for k, v in data.items() if k not in (tool_key, "thought", "reasoning", "type", "id")}
            elif isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {"input": args}
            elif not isinstance(args, dict):
                args = {"input": args}
            return {"tool": tool_name, "args": args}

    # Single key dict where key is the tool name (e.g. {"run_cmd": {"command": "..."}})
    if len(data) == 1:
        k, v = next(iter(data.items()))
        if isinstance(v, dict):
            return {"tool": k.strip(), "args": v}
        elif isinstance(v, str) and k not in ("error", "message", "status", "response"):
            return {"tool": k.strip(), "args": {"command" if "cmd" in k else "path" if "file" in k else "input": v}}

    return None


def extract_tool_calls(text: str):
    if not text or not str(text).strip():
        return []

    calls = []

    # 1. Native XML function-call format:
    # <invoke name="read_file"><parameter name="path">...</parameter></invoke>
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

    # 2. XML <tool_call>...</tool_call> or <function_call>...</function_call>
    xml_matches = re.findall(r"<(?:tool_call|function_call)>\s*(.*?)\s*</(?:tool_call|function_call)>", text, re.DOTALL | re.IGNORECASE)
    for match in xml_matches:
        cleaned = re.sub(r"^```(?:\w+)?\s*", "", match.strip())
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()
        data = parse_json_lenient(cleaned)
        if isinstance(data, dict):
            tc = _dict_to_tool_call(data)
            if tc and tc not in calls:
                calls.append(tc)
                continue

        # Check key-value format inside XML
        tool_m = re.search(r"^(?:tool|name|action):\s*(\w+)", cleaned, re.MULTILINE | re.IGNORECASE)
        if tool_m:
            tool_name = tool_m.group(1).strip()
            path_m = re.search(r"^path:\s*(.+)$", cleaned, re.MULTILINE | re.IGNORECASE)
            cmd_m = re.search(r"^command:\s*(.+)$", cleaned, re.MULTILINE | re.IGNORECASE)
            args = {}
            if path_m:
                args["path"] = path_m.group(1).strip()
            if cmd_m:
                args["command"] = cmd_m.group(1).strip()
            call_obj = {"tool": tool_name, "args": args}
            if call_obj not in calls:
                calls.append(call_obj)

    # 3. Markdown code blocks: ```tool_call, ```tool_calls, ```tool, ```json, ```
    code_block_matches = re.findall(r"```(?:tool_call|tool_calls|tools|tool|json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    for match in code_block_matches:
        match_str = match.strip()
        if not match_str:
            continue
        cleaned = re.sub(r"^<(?:tool_call|function_call)>\s*", "", match_str, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*</(?:tool_call|function_call)>$", "", cleaned, flags=re.IGNORECASE).strip()

        data = parse_json_lenient(cleaned)
        if isinstance(data, dict):
            tc = _dict_to_tool_call(data)
            if tc and tc not in calls:
                calls.append(tc)
                continue
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    tc = _dict_to_tool_call(item)
                    if tc and tc not in calls:
                        calls.append(tc)
            if calls:
                continue

        # Check key-value format inside markdown block
        tool_m = re.search(r"^(?:tool|name|action):\s*(\w+)", cleaned, re.MULTILINE | re.IGNORECASE)
        if tool_m:
            tool_name = tool_m.group(1).strip()
            path_m = re.search(r"^path:\s*(.+)$", cleaned, re.MULTILINE | re.IGNORECASE)
            cmd_m = re.search(r"^command:\s*(.+)$", cleaned, re.MULTILINE | re.IGNORECASE)
            code_block_m = re.search(r"```(?:\w+)?\s*\n(.*)\n```", cleaned, re.DOTALL)
            args = {}
            if path_m:
                args["path"] = path_m.group(1).strip()
            if cmd_m:
                args["command"] = cmd_m.group(1).strip()
            if code_block_m:
                args["content"] = code_block_m.group(1)
            call_obj = {"tool": tool_name, "args": args}
            if call_obj not in calls:
                calls.append(call_obj)
                continue

        # Function call style e.g. run_cmd(command="...")
        fn_match = re.match(r"^([a-zA-Z0-9_]+)\s*\((.*)\)\s*$", cleaned, re.DOTALL)
        if fn_match:
            tool_name = fn_match.group(1)
            raw_params = fn_match.group(2)
            args = {}
            for param in re.finditer(r'([a-zA-Z0-9_]+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^,)]+))', raw_params):
                k = param.group(1)
                v = param.group(2) if param.group(2) is not None else param.group(3) if param.group(3) is not None else param.group(4).strip()
                args[k] = v
            call_obj = {"tool": tool_name, "args": args}
            if call_obj not in calls:
                calls.append(call_obj)

    # 4. Raw JSON without code fences in case model didn't fence it
    if not calls:
        raw_json_matches = re.finditer(r'\{\s*(?:["\']tool["\']|["\']name["\']|["\']function["\']|["\']action["\']|["\'][a-zA-Z0-9_]+["\']\s*,\s*["\']args["\']).*?\}', text, re.DOTALL)
        for m in raw_json_matches:
            data = parse_json_lenient(m.group(0))
            if isinstance(data, dict):
                tc = _dict_to_tool_call(data)
                if tc and tc not in calls:
                    calls.append(tc)

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
