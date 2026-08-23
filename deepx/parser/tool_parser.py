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

_CANONICAL_TOOLS = {
    "run_cmd": "run_cmd",
    "cmd": "run_cmd",
    "bash": "run_cmd",
    "shell": "run_cmd",
    "exec": "run_cmd",
    "command": "run_cmd",
    "execute_command": "run_cmd",
    "terminal": "run_cmd",
    
    "run_background_cmd": "run_background_cmd",
    "background_cmd": "run_background_cmd",
    "bg_cmd": "run_background_cmd",
    "run_bg": "run_background_cmd",
    
    "task_status": "task_status",
    "bg_status": "task_status",
    
    "task_log": "task_log",
    "bg_log": "task_log",
    
    "send_input": "send_input",
    "pty_input": "send_input",
    
    "kill_cmd": "kill_cmd",
    "pty_kill": "kill_cmd",
    
    "run_python": "run_python",
    "python": "run_python",
    "py": "run_python",
    "python3": "run_python",
    "run_code": "run_python",
    
    "read_file": "read_file",
    "read": "read_file",
    "view_file": "read_file",
    "cat": "read_file",
    "get_file": "read_file",
    
    "write_file": "write_file",
    "write": "write_file",
    "create_file": "write_file",
    "save_file": "write_file",
    "new_file": "write_file",
    
    "edit_file": "edit_file",
    "edit": "edit_file",
    "replace_file_content": "edit_file",
    "modify_file": "edit_file",
    "patch_file": "edit_file",
    
    "list_dir": "list_dir",
    "list_directory": "list_dir",
    "ls": "list_dir",
    "dir": "list_dir",
    "view_dir": "list_dir",
    
    "file_info": "file_info",
    "stat": "file_info",
    
    "web_search": "web_search",
    "search": "web_search",
    "duckduckgo": "web_search",
    "search_web": "web_search",
    "google": "web_search",
    "ddg": "web_search",
    
    "fetch_url": "fetch_url",
    "fetch": "fetch_url",
    "curl": "fetch_url",
    "get_url": "fetch_url",
    "read_url": "fetch_url",
    "read_webpage": "fetch_url",
    "scrape": "fetch_url",
    
    "browser_action": "browser_action",
    "browser": "browser_action",
    "playwright": "browser_action",
    "web_browser": "browser_action",
    "browse": "browser_action",
    
    "todo": "todo",
    "tasks": "todo",
    "todo_list": "todo",
    "plan_tasks": "todo",
    
    "project_memory": "project_memory",
    "memory": "project_memory",
    
    "sys_info": "sys_info",
    "system_info": "sys_info",
    
    "make_excel": "make_excel",
    "excel": "make_excel",
    
    "make_docx": "make_docx",
    "docx": "make_docx",
    "word": "make_docx",
    
    "make_pptx": "make_pptx",
    "pptx": "make_pptx",
    "powerpoint": "make_pptx",
    
    "zip_pack": "zip_pack",
    "zip": "zip_pack",
    
    "unzip_pack": "unzip_pack",
    "unzip": "unzip_pack",
    
    "inspect_media": "inspect_media",
    "media": "inspect_media",
    "inspect": "inspect_media",
    "ffprobe": "inspect_media",
    
    "read_clipboard": "read_clipboard",
    "get_clipboard": "read_clipboard",
    "clipboard": "read_clipboard",
    
    "write_clipboard": "write_clipboard",
    "set_clipboard": "set_clipboard",
    "get_clipboard_history": "get_clipboard_history",
    "get_clipboard_item": "get_clipboard_item",
    "delete_clipboard_item": "delete_clipboard_item",
    "clear_clipboard_history": "clear_clipboard_history",
    
    "vds_deploy": "vds_deploy",
    "vds": "vds_deploy",
    "vps": "vds_deploy",
    "ssh": "vds_deploy",
    "server": "vds_deploy",
    "dadata_osint": "dadata_osint",
    "funstat_osint": "funstat_osint",
    "render_plan": "render_plan",
}

def canonicalize_tool_name(name: str) -> str:
    if not name:
        return ""
    clean = str(name).strip().lower().replace("-", "_")
    return _CANONICAL_TOOLS.get(clean, clean)

def clean_and_fix_json_expressions(text: str) -> str:
    """
    Detects and safely evaluates JavaScript / Python-like expressions in JSON values:
    - String concatenation: "abc" + "def"
    - .repeat(N) methods: "a".repeat(1000)
    - Python multiplications: "a" * 1000
    - Math or variable-free expressions
    """
    if not text or not str(text).strip():
        return ""
    s = text.strip()

    # Preprocess .repeat(N)
    def repl_repeat(m):
        base_str = m.group(1)
        count = m.group(2)
        try:
            cnt = min(int(count), 50000)
            return f"({base_str} * {cnt})"
        except Exception:
            return m.group(0)

    s = re.sub(
        r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')\.repeat\s*\(\s*(\d+)\s*\)',
        repl_repeat,
        s
    )

    # Fix field values with concatenation `+` or `*`
    def fix_field_expr(match):
        prefix = match.group(1)
        raw_val = match.group(2)
        try:
            import ast
            tree = ast.parse(raw_val.strip(), mode='eval')
            for node in ast.walk(tree):
                if isinstance(node, (ast.Expression, ast.BinOp, ast.Add, ast.Mult, ast.Constant, ast.List, ast.Tuple, ast.Dict, ast.UnaryOp, ast.USub, ast.UAdd)):
                    continue
                raise ValueError("Unsafe node")
            val = eval(compile(tree, "<string>", "eval"), {"__builtins__": None}, {})
            return f"{prefix}{json.dumps(str(val), ensure_ascii=False)}"
        except Exception:
            pieces = []
            for sm in re.finditer(r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')', raw_val):
                try:
                    import ast
                    pieces.append(ast.literal_eval(sm.group(1)))
                except Exception:
                    pieces.append(sm.group(1)[1:-1])
            if pieces:
                combined = "".join(pieces)
                return f"{prefix}{json.dumps(combined, ensure_ascii=False)}"
            return match.group(0)

    pattern = r'((?:["\'][\w\-]+["\']|\b[\w\-]+\b)\s*:\s*)((?:["\'][^"\']*?["\']|\([^\)]*?\))\s*(?:\+|\*)[^\n,}\]]*)'
    s = re.sub(pattern, fix_field_expr, s)
    return s

def extract_json_objects(text: str) -> list:
    """Find all top-level JSON objects or arrays in text by tracking balanced braces/brackets."""
    results = []
    i = 0
    n = len(text)
    while i < n:
        char = text[i]
        if char in ('{', '['):
            start = i
            open_char = char
            close_char = '}' if char == '{' else ']'
            depth = 0
            in_string = False
            escape = False
            quote_char = None
            j = i
            while j < n:
                c = text[j]
                if escape:
                    escape = False
                elif c == '\\' and in_string:
                    escape = True
                elif in_string:
                    if c == quote_char:
                        if j + 2 < n and text[j:j+3] == quote_char * 3:
                            j += 2
                        in_string = False
                        quote_char = None
                else:
                    if c in ('"', "'"):
                        if j + 2 < n and text[j:j+3] == c * 3:
                            in_string = True
                            quote_char = c
                            j += 2
                        else:
                            in_string = True
                            quote_char = c
                    elif c == open_char:
                        depth += 1
                    elif c == close_char:
                        depth -= 1
                        if depth == 0:
                            results.append(text[start:j+1])
                            i = j
                            break
                j += 1
        i += 1
    return results

def parse_json_lenient(json_str: str):
    """
    Robust, fault-tolerant JSON parser for tool calls. Supports:
    - Standard JSON
    - String concatenation, .repeat(), arithmetic expressions inside JSON values
    - Unescaped newlines and tabs inside multiline strings (strict=False)
    - Triple quoted strings inside JSON
    - Missing 'tool': key (e.g. {"run_cmd", "args": {...}} or {'run_cmd', 'args': ...})
    - Unquoted object keys ({tool: "...", args: {...}})
    - Unescaped Windows backslashes in paths (C:\\path or C:\\path\\telegram)
    - Trailing commas before closing braces/brackets
    - Single quoted strings and Python literals (True, False, None)
    - Python dict / AST evaluation fallback
    """
    if not json_str or not json_str.strip():
        return None

    s = clean_and_fix_json_expressions(json_str)

    def fix_windows_paths(text: str) -> str:
        def replace_path(m):
            key = m.group(1)
            val = m.group(2)
            val_fixed = re.sub(r'\\([a-zA-Z0-9_\-\.])', r'/\1', val)
            return f'{key}"{val_fixed}"'
        return re.sub(r'("path"\s*:\s*)"([^"]+)"', replace_path, text)

    s = fix_windows_paths(s)

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

    # Fix unquoted keys ({tool: "...", args: {action: "..."}})
    s = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_\-]*)\s*:', r'\1"\2":', s)

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

    # Try AST literal eval
    try:
        import ast
        ast_str = re.sub(r'\btrue\b', 'True', s_no_trailing)
        ast_str = re.sub(r'\bfalse\b', 'False', ast_str)
        ast_str = re.sub(r'\bnull\b', 'None', ast_str)
        val = ast.literal_eval(ast_str)
        if isinstance(val, (dict, list)):
            return val
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
            return val.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")

        repaired = re.sub(r'"([^"\\]*(\\.[^"\\]*)*)"', replace_newlines_in_strings, s_no_trailing, flags=re.DOTALL)
        repaired = re.sub(r'\\(?![\\"/bfnrtu])', r'\\\\', repaired)
        return json.loads(repaired, strict=False)
    except Exception:
        pass

    try:
        single_to_double = re.sub(r"'([^'\\]*(?:\\.[^'\\]*)*)'", r'"\1"', s_no_trailing)
        return json.loads(single_to_double, strict=False)
    except Exception:
        pass

    return None


def _dict_to_tool_call(data: dict):
    if not isinstance(data, dict):
        return None

    # Check for direct 'tool' or aliases
    for tool_key in ("tool", "name", "function", "action", "tool_name", "type"):
        if tool_key in data and isinstance(data[tool_key], str):
            tool_name = canonicalize_tool_name(data[tool_key].strip())
            if not tool_name:
                continue
            args = None
            for args_key in ("args", "arguments", "parameters", "params", "kwargs", "action_input", "input"):
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
        canon = canonicalize_tool_name(k)
        if canon in _CANONICAL_TOOLS.values():
            if isinstance(v, dict):
                return {"tool": canon, "args": v}
            elif isinstance(v, str) and canon not in ("error", "message", "status", "response"):
                return {"tool": canon, "args": {"command" if "cmd" in canon else "path" if "file" in canon else "input": v}}

    return None


def extract_tool_calls(text: str):
    """
    Extracts all tool calls from model output using multiple cascaded extraction strategies:
    1. Native XML invoke format: <invoke name="...">...</invoke>
    2. XML tags: <tool_call>...</tool_call>, <function_call>...</function_call>
    3. Markdown code blocks (```tool_call, ```tool_calls, ```json, etc.) — both closed and unclosed
    4. Multi-object balanced JSON scanners for multiple tool calls in a single block
    5. Raw unfenced JSON objects in text
    6. Function call syntax: tool_name(param1="...", param2="...")
    """
    if not text or not str(text).strip():
        return []

    calls = []

    def add_call(tc):
        if tc and isinstance(tc, dict) and tc.get("tool"):
            tc["tool"] = canonicalize_tool_name(tc["tool"])
            tc["args"] = normalize_tool_args(tc.get("args") or {})
            if tc not in calls:
                calls.append(tc)

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
        add_call({"tool": html.unescape(tool_name.strip()), "args": args})

    # 2. XML <tool_call>...</tool_call> or <function_call>...</function_call>
    xml_matches = re.findall(r"<(?:tool_call|function_call|tool)>\s*(.*?)\s*</(?:tool_call|function_call|tool)>", text, re.DOTALL | re.IGNORECASE)
    for match in xml_matches:
        cleaned = re.sub(r"^```(?:\w+)?\s*", "", match.strip())
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()
        
        objs = extract_json_objects(cleaned)
        if objs:
            for obj_str in objs:
                data = parse_json_lenient(obj_str)
                if isinstance(data, dict):
                    add_call(_dict_to_tool_call(data))
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            add_call(_dict_to_tool_call(item))
        else:
            data = parse_json_lenient(cleaned)
            if isinstance(data, dict):
                add_call(_dict_to_tool_call(data))
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        add_call(_dict_to_tool_call(item))

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
            add_call({"tool": tool_name, "args": args})

    # 3. Markdown code blocks: ```tool_call, ```tool_calls, ```tool, ```json, etc. (closed or unclosed)
    code_block_matches = re.findall(r"```(?:tool_call|tool_calls|tools|tool|json|javascript|js|python|py|bash|sh)?\s*\n?(.*?)(?:```|$)", text, re.DOTALL)
    for match in code_block_matches:
        match_str = match.strip()
        if not match_str:
            continue
        cleaned = re.sub(r"^<(?:tool_call|function_call)>\s*", "", match_str, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*</(?:tool_call|function_call)>$", "", cleaned, flags=re.IGNORECASE).strip()

        objs = extract_json_objects(cleaned)
        if objs:
            for obj_str in objs:
                data = parse_json_lenient(obj_str)
                if isinstance(data, dict):
                    add_call(_dict_to_tool_call(data))
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            add_call(_dict_to_tool_call(item))
        else:
            data = parse_json_lenient(cleaned)
            if isinstance(data, dict):
                add_call(_dict_to_tool_call(data))
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        add_call(_dict_to_tool_call(item))

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
            add_call({"tool": tool_name, "args": args})

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
            add_call({"tool": tool_name, "args": args})

    # 4. Raw JSON objects in text (if no code block tool call was found)
    if not calls:
        raw_objs = extract_json_objects(text)
        for obj_str in raw_objs:
            data = parse_json_lenient(obj_str)
            if isinstance(data, dict):
                add_call(_dict_to_tool_call(data))
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        add_call(_dict_to_tool_call(item))

    # 5. Raw function calls in text: `browser_action(action="navigate", url="...")`
    if not calls:
        for fn_match in re.finditer(r'\b([a-zA-Z0-9_]+)\s*\(([^()]*?)\)', text):
            tool_name = canonicalize_tool_name(fn_match.group(1))
            if tool_name in _CANONICAL_TOOLS.values():
                raw_params = fn_match.group(2)
                args = {}
                for param in re.finditer(r'([a-zA-Z0-9_]+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^,)]+))', raw_params):
                    k = param.group(1)
                    v = param.group(2) if param.group(2) is not None else param.group(3) if param.group(3) is not None else param.group(4).strip()
                    args[k] = v
                add_call({"tool": tool_name, "args": args})

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

    for code_key in ("code", "content", "command", "target", "replacement", "script"):
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
        tool_name = canonicalize_tool_name(call.get("tool"))
        normalized.append({
            "tool": tool_name,
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

