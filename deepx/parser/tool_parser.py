import ast
import html
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from deepx.core.constants import MAX_READ_LINES

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
    "kill_background_cmd": "kill_background_cmd",
    "kill_bg": "kill_background_cmd",
    "kill_task": "kill_background_cmd",
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
    "grep_search": "grep_search",
    "grep": "grep_search",
    "ripgrep": "grep_search",
    "rg": "grep_search",
    "search_code": "grep_search",
    "search_files": "grep_search",
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

_KNOWN_TOOL_NAMES = set(_CANONICAL_TOOLS.values())

_TOOL_FENCE_LANGS = {"tool_call", "tool_calls", "tools", "tool"}
_JSON_OR_PLAIN_FENCE_LANGS = {"", "json", "json5"} | _TOOL_FENCE_LANGS


def _has_unclosed_json_prefix(text: str) -> bool:
    """Return True if `text` starts a JSON/dict payload whose string or braces are still open."""
    s = text.lstrip()
    if not s or s[0] not in "{[":
        return False
    n = len(s)
    i = 0
    depth = 0
    saw_bracket = False
    while i < n:
        ch = s[i]
        if ch in ('"', "'"):
            end_idx, is_triple = _scan_string_end(s, i)
            quote_len = 3 if is_triple else 1
            if end_idx >= n and (n - i < 2 * quote_len or not s.endswith(ch * quote_len)):
                return True
            i = end_idx
            continue
        if ch in ("{", "["):
            depth += 1
            saw_bracket = True
        elif ch in ("}", "]"):
            depth -= 1
            if saw_bracket and depth <= 0:
                rest = s[i + 1 :].lstrip()
                if not rest or rest[0] not in "{[":
                    return False
                depth = 0
                saw_bracket = False
        i += 1
    return depth > 0


def _iter_fenced_blocks(text: str) -> List[Tuple[str, str, int, int]]:
    """Extract markdown fenced code blocks `(lang, body, start_pos, end_pos)`.

    Handles nested ``` markdown fences inside JSON/tool string literals when tracking braces.
    """
    blocks: List[Tuple[str, str, int, int]] = []
    lines = text.splitlines(keepends=True)
    n_lines = len(lines)
    offsets: List[int] = []
    pos = 0
    for line in lines:
        offsets.append(pos)
        pos += len(line)

    i = 0
    while i < n_lines:
        stripped = lines[i].lstrip()
        m_open = re.match(r"^(`{3,})([a-zA-Z0-9_+-]*)[ \t]*\r?\n?$", stripped)
        if not m_open:
            i += 1
            continue

        fence = m_open.group(1)
        lang = m_open.group(2).strip().lower()
        start_pos = offsets[i]
        body_lines: List[str] = []
        j = i + 1
        end_pos = len(text)
        closed = False

        while j < n_lines:
            candidate = lines[j].strip()
            if candidate == fence or (len(candidate) >= len(fence) and set(candidate) == {"`"}):
                # If inside an unclosed JSON/tool fence with unbalanced braces/strings, check if a later closing fence closes it cleanly
                if lang in _JSON_OR_PLAIN_FENCE_LANGS:
                    so_far = "".join(body_lines)
                    if _has_unclosed_json_prefix(so_far):
                        has_later_fence = any(
                            lines[k].strip() == fence or (len(lines[k].strip()) >= len(fence) and set(lines[k].strip()) == {"`"})
                            for k in range(j + 1, n_lines)
                        )
                        if has_later_fence:
                            body_lines.append(lines[j])
                            j += 1
                            continue
                end_pos = offsets[j] + len(lines[j])
                closed = True
                break
            body_lines.append(lines[j])
            j += 1

        blocks.append((lang, "".join(body_lines), start_pos, end_pos))
        i = (j + 1) if closed else n_lines
    return blocks


def canonicalize_tool_name(name: str) -> str:
    if not name:
        return ""
    clean = str(name).strip().lower().replace("-", "_")
    return _CANONICAL_TOOLS.get(clean, clean)


def _scan_string_end(text: str, start: int) -> Tuple[int, bool]:
    """Return (end_index_exclusive, is_triple) for a string starting at `start`."""
    n = len(text)
    quote_char = text[start]
    if start + 2 < n and text[start : start + 3] == quote_char * 3:
        i = start + 3
        while i < n:
            c = text[i]
            if c == "\\":
                i += 2
                continue
            if c == quote_char and i + 2 < n and text[i : i + 3] == quote_char * 3:
                return i + 3, True
            i += 1
        return n, True

    i = start + 1
    while i < n:
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == quote_char:
            return i + 1, False
        i += 1
    return n, False


def _decode_string_token(raw_token: str, is_triple: bool) -> str:
    """Decode a quoted string token safely into raw string contents."""
    if is_triple:
        quote_char = raw_token[0]
        if len(raw_token) >= 6 and raw_token.endswith(quote_char * 3):
            return raw_token[3:-3]
        return raw_token[3:]

    try:
        val = ast.literal_eval(raw_token)
        if isinstance(val, str):
            return val
    except Exception:
        pass

    quote_char = raw_token[0]
    inner = raw_token[1:-1] if len(raw_token) >= 2 and raw_token.endswith(quote_char) else raw_token[1:]
    try:
        return json.loads('"' + inner.replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t") + '"', strict=False)
    except Exception:
        return inner


def _tokenize_segments(text: str) -> List[Tuple[bool, bool, str]]:
    """Split text into [(is_string, is_triple, chunk_text), ...]."""
    segments: List[Tuple[bool, bool, str]] = []
    n = len(text)
    i = 0
    buf_start = 0
    while i < n:
        if text[i] in ('"', "'"):
            if i > buf_start:
                segments.append((False, False, text[buf_start:i]))
            end_idx, is_triple = _scan_string_end(text, i)
            segments.append((True, is_triple, text[i:end_idx]))
            i = end_idx
            buf_start = i
        else:
            i += 1
    if buf_start < n:
        segments.append((False, False, text[buf_start:]))
    return segments


def _safe_eval_expr(expr: str) -> Optional[str]:
    """Safely evaluate simple constant concatenation/repeat expressions outside strings."""
    candidate = re.sub(
        r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')\.repeat\s*\(\s*(\d+)\s*\)',
        lambda m: f"({m.group(1)} * {min(int(m.group(2)), 50000)})",
        expr.strip(),
    )
    try:
        tree = ast.parse(candidate, mode="eval")
        for node in ast.walk(tree):
            if isinstance(
                node,
                (ast.Expression, ast.BinOp, ast.Add, ast.Mult, ast.Constant, ast.UnaryOp, ast.USub, ast.UAdd),
            ):
                continue
            return None
        val = eval(compile(tree, "<string>", "eval"), {"__builtins__": None}, {})
        if isinstance(val, (str, int, float)):
            return json.dumps(str(val), ensure_ascii=False)
    except Exception:
        pass
    return None


def clean_and_fix_json_expressions(text: str) -> str:
    """Safely evaluate `.repeat(N)`, `"a" + "b"`, `"a" * N` ONLY in expression slots outside string contents."""
    if not text or not str(text).strip():
        return ""

    segments = _tokenize_segments(text.strip())
    out: List[str] = []
    idx = 0
    total = len(segments)

    while idx < total:
        is_str, is_triple, chunk = segments[idx]
        if is_str and not is_triple:
            # Check for immediate .repeat(N) or + / * expression chain following this string token
            expr_parts = [chunk]
            j = idx + 1
            matched_expr = False
            while j < total:
                n_str, n_tri, n_chunk = segments[j]
                if not n_str:
                    if not matched_expr and re.match(r"^\s*\.repeat\s*\(\s*\d+\s*\)", n_chunk):
                        m = re.match(r"^(\s*\.repeat\s*\(\s*\d+\s*\))(.*)$", n_chunk, re.DOTALL)
                        if m:
                            evaluated = _safe_eval_expr(chunk + m.group(1))
                            if evaluated is not None:
                                out.append(evaluated + m.group(2))
                                idx = j + 1
                                matched_expr = True
                                break
                    op_match = re.match(r"^\s*([+*])\s*(.*)$", n_chunk, re.DOTALL)
                    if op_match and j + 1 < total and segments[j + 1][0]:
                        expr_parts.append(n_chunk)
                        expr_parts.append(segments[j + 1][2])
                        j += 2
                        continue
                    mul_num = re.match(r"^(\s*\*\s*\d+)(.*)$", n_chunk, re.DOTALL)
                    if mul_num:
                        expr_parts.append(mul_num.group(1))
                        evaluated = _safe_eval_expr("".join(expr_parts))
                        if evaluated is not None:
                            out.append(evaluated + mul_num.group(2))
                            idx = j + 1
                            matched_expr = True
                        break
                    break
                else:
                    break
            if matched_expr:
                continue
            if len(expr_parts) > 1:
                evaluated = _safe_eval_expr("".join(expr_parts))
                if evaluated is not None:
                    out.append(evaluated)
                    idx = j
                    continue

        out.append(chunk)
        idx += 1

    return "".join(out)


def extract_json_objects(text: str) -> List[str]:
    """Find top-level JSON/dict objects or arrays while properly respecting single and triple-quoted strings."""
    results: List[str] = []
    i = 0
    n = len(text)
    while i < n:
        char = text[i]
        if char in ("{", "["):
            start = i
            open_char = char
            close_char = "}" if char == "{" else "]"
            depth = 0
            j = i
            found = False
            while j < n:
                c = text[j]
                if c in ('"', "'"):
                    j, _ = _scan_string_end(text, j)
                    continue
                if c == open_char:
                    depth += 1
                elif c == close_char:
                    depth -= 1
                    if depth == 0:
                        results.append(text[start : j + 1])
                        i = j
                        found = True
                        break
                j += 1
            if not found:
                pass
        i += 1
    return results


def _repair_code_segments_outside_strings(text: str, *, for_ast: bool = False) -> str:
    """Apply structural JSON repairs ONLY outside string literals."""
    segments = _tokenize_segments(text)
    repaired_parts: List[str] = []

    for is_str, is_triple, chunk in segments:
        if is_str:
            if is_triple:
                decoded = _decode_string_token(chunk, True)
                repaired_parts.append(json.dumps(decoded, ensure_ascii=False) if not for_ast else repr(decoded))
            elif chunk.startswith("'") and not for_ast:
                decoded = _decode_string_token(chunk, False)
                repaired_parts.append(json.dumps(decoded, ensure_ascii=False))
            else:
                repaired_parts.append(chunk)
            continue

        code = chunk
        # Normalize missing "tool": key in pattern like {"run_cmd", "args": ...}
        code = re.sub(
            r'([{\[,]\s*)([a-zA-Z_][a-zA-Z0-9_\-]*)\s*:',
            lambda m: f'{m.group(1)}"{m.group(2)}":' if not for_ast else f'{m.group(1)}r"{m.group(2)}":',
            code,
        )
        # Trailing commas
        code = re.sub(r",\s*([\}\]])", r"\1", code)

        if for_ast:
            code = re.sub(r"\btrue\b", "True", code)
            code = re.sub(r"\bfalse\b", "False", code)
            code = re.sub(r"\bnull\b", "None", code)
        else:
            code = re.sub(r"\bTrue\b", "true", code)
            code = re.sub(r"\bFalse\b", "false", code)
            code = re.sub(r"\bNone\b", "null", code)

        repaired_parts.append(code)

    return "".join(repaired_parts)


def _fix_invalid_escapes_in_strings(text: str) -> str:
    """Fix raw control chars and invalid backslash escapes (e.g. unescaped Windows paths) inside double-quoted JSON strings."""
    segments = _tokenize_segments(text)
    out: List[str] = []
    for is_str, is_triple, chunk in segments:
        if not is_str or is_triple:
            out.append(chunk)
            continue
        fixed = chunk.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        fixed = re.sub(r'\\(?![\\"/bfnrtu])', r"\\\\", fixed)
        out.append(fixed)
    return "".join(out)


def parse_json_lenient(json_str: str):
    """Fault-tolerant JSON/dict parser that strictly preserves Python code & literals inside strings."""
    if not json_str or not json_str.strip():
        return None

    raw = json_str.strip()
    try:
        return json.loads(raw, strict=False)
    except Exception:
        pass

    s = clean_and_fix_json_expressions(raw)

    # Fix missing "tool": key at object start: {"run_cmd", "args": {...}}
    s = re.sub(
        r'^\{\s*(["\'])([a-zA-Z0-9_\-]+)\1\s*,\s*',
        r'{"tool": "\2", ',
        s,
    )

    repaired = _repair_code_segments_outside_strings(s, for_ast=False)
    try:
        return json.loads(repaired, strict=False)
    except Exception:
        pass

    repaired_esc = _fix_invalid_escapes_in_strings(repaired)
    try:
        return json.loads(repaired_esc, strict=False)
    except Exception:
        pass

    try:
        ast_candidate = _repair_code_segments_outside_strings(s, for_ast=True)
        val = ast.literal_eval(ast_candidate)
        if isinstance(val, (dict, list)):
            return val
    except Exception:
        pass

    try:
        # Fallback for raw ast literal without key rewriting
        val = ast.literal_eval(s)
        if isinstance(val, (dict, list)):
            return val
    except Exception:
        pass

    return None


def _dict_to_tool_call(data: dict, require_known: bool = True) -> Optional[Dict[str, Any]]:
    """Convert a parsed dict into a normalized tool call descriptor."""
    if not isinstance(data, dict):
        return None

    for tool_key in ("tool", "tool_name", "function", "name", "action", "type"):
        if tool_key in data and isinstance(data[tool_key], str):
            raw_name = data[tool_key].strip()
            tool_name = canonicalize_tool_name(raw_name)
            if not tool_name:
                continue

            is_known = tool_name in _KNOWN_TOOL_NAMES
            has_explicit_args = any(
                k in data for k in ("args", "arguments", "parameters", "params", "kwargs", "action_input")
            )

            # Reject arbitrary JSON payloads like {"name": "my-app"} or {"type": "module"}
            if tool_key in ("name", "action", "type"):
                if not is_known:
                    continue
                if tool_key == "type" and not has_explicit_args:
                    continue
            elif require_known and not is_known:
                continue

            args = None
            for args_key in ("args", "arguments", "parameters", "params", "kwargs", "action_input", "input"):
                if args_key in data:
                    args = data[args_key]
                    break
            if args is None:
                args = {
                    k: v
                    for k, v in data.items()
                    if k not in (tool_key, "thought", "reasoning", "type", "id")
                }
            elif isinstance(args, str):
                try:
                    parsed_args = json.loads(args)
                    args = parsed_args if isinstance(parsed_args, dict) else {"input": args}
                except Exception:
                    args = {"input": args}
            elif not isinstance(args, dict):
                args = {"input": args}
            return {"tool": tool_name, "args": args}

    if len(data) == 1:
        k, v = next(iter(data.items()))
        canon = canonicalize_tool_name(k)
        if canon in _KNOWN_TOOL_NAMES:
            if isinstance(v, dict):
                return {"tool": canon, "args": v}
            if isinstance(v, str):
                arg_key = "command" if "cmd" in canon else "path" if "file" in canon else "input"
                return {"tool": canon, "args": {arg_key: v}}

    return None


def _parse_kv_params(raw_params: str) -> Dict[str, Any]:
    """Parse `key="val", key2='val2'` arguments safely using Python AST when possible."""
    try:
        call_ast = ast.parse(f"_f({raw_params})", mode="eval")
        if isinstance(call_ast.body, ast.Call):
            args: Dict[str, Any] = {}
            for kw in call_ast.body.keywords:
                if kw.arg:
                    try:
                        args[kw.arg] = ast.literal_eval(kw.value)
                    except Exception:
                        pass
            if args or not raw_params.strip():
                return args
    except Exception:
        pass

    args = {}
    for param in re.finditer(r'([a-zA-Z0-9_]+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^,)]+))', raw_params):
        k = param.group(1)
        v = (
            param.group(2)
            if param.group(2) is not None
            else param.group(3)
            if param.group(3) is not None
            else param.group(4).strip()
        )
        args[k] = v
    return args


def _collect_from_json_text(text: str, add_call, *, require_known: bool = True) -> bool:
    added = False
    objs = extract_json_objects(text)
    candidates = objs if objs else [text]
    for obj_str in candidates:
        data = parse_json_lenient(obj_str)
        if isinstance(data, dict):
            tc = _dict_to_tool_call(data, require_known=require_known)
            if tc:
                add_call(tc)
                added = True
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    tc = _dict_to_tool_call(item, require_known=require_known)
                    if tc:
                        add_call(tc)
                        added = True
    return added


def extract_tool_calls(text: str) -> List[Dict[str, Any]]:
    """Extract validated tool calls without false positives on YAML/Python/code examples or prose."""
    if not text or not str(text).strip():
        return []

    calls: List[Dict[str, Any]] = []

    def add_call(tc):
        if tc and isinstance(tc, dict) and tc.get("tool"):
            canon = canonicalize_tool_name(tc["tool"])
            tc["tool"] = canon
            tc["args"] = normalize_tool_args(tc.get("args") or {}, tool_name=canon)
            if tc not in calls:
                calls.append(tc)

    # 1. Native XML function-call format: <invoke name="..."><parameter name="...">...</parameter></invoke>
    invoke_matches = re.findall(
        r"<invoke\b[^>]*\bname\s*=\s*(['\"])(.*?)\1[^>]*>(.*?)</invoke\s*>",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    for _, tool_name, invoke_body in invoke_matches:
        canon = canonicalize_tool_name(html.unescape(tool_name.strip()))
        if canon not in _KNOWN_TOOL_NAMES:
            continue
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
        add_call({"tool": canon, "args": args})

    # 2. Explicit XML <tool_call>...</tool_call> or <function_call>...</function_call>
    xml_matches = re.findall(
        r"<(?:tool_call|function_call)>\s*(.*?)\s*</(?:tool_call|function_call)>",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    for match in xml_matches:
        cleaned = re.sub(r"^```(?:\w+)?\s*", "", match.strip())
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()
        if _collect_from_json_text(cleaned, add_call, require_known=False):
            continue

        tool_m = re.search(r"^(?:tool|name|action):\s*(\w+)", cleaned, re.MULTILINE | re.IGNORECASE)
        if tool_m:
            tool_name = canonicalize_tool_name(tool_m.group(1).strip())
            if tool_name in _KNOWN_TOOL_NAMES:
                path_m = re.search(r"^path:\s*(.+)$", cleaned, re.MULTILINE | re.IGNORECASE)
                cmd_m = re.search(r"^command:\s*(.+)$", cleaned, re.MULTILINE | re.IGNORECASE)
                args = {}
                if path_m:
                    args["path"] = path_m.group(1).strip()
                if cmd_m:
                    args["command"] = cmd_m.group(1).strip()
                add_call({"tool": tool_name, "args": args})

    # 3. Fenced markdown blocks — ignore yaml, python, bash, html, etc. to prevent false positives
    fenced_blocks = _iter_fenced_blocks(text)
    for lang_norm, body, _, _ in fenced_blocks:
        if lang_norm not in _JSON_OR_PLAIN_FENCE_LANGS:
            continue

        match_str = body.strip()
        if not match_str:
            continue

        cleaned = re.sub(r"^<(?:tool_call|function_call)>\s*", "", match_str, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*</(?:tool_call|function_call)>$", "", cleaned, flags=re.IGNORECASE).strip()
        explicit_tool_fence = lang_norm in _TOOL_FENCE_LANGS or match_str != cleaned

        if _collect_from_json_text(cleaned, add_call, require_known=not explicit_tool_fence):
            continue

        # Key-value or function-call fallback ONLY inside explicit tool_call blocks
        if explicit_tool_fence:
            tool_m = re.search(r"^(?:tool|tool_name):\s*([a-zA-Z0-9_\-]+)", cleaned, re.MULTILINE | re.IGNORECASE)
            if tool_m:
                tool_name = canonicalize_tool_name(tool_m.group(1).strip())
                if tool_name in _KNOWN_TOOL_NAMES:
                    path_m = re.search(r"^path:\s*(.+)$", cleaned, re.MULTILINE | re.IGNORECASE)
                    cmd_m = re.search(r"^command:\s*(.+)$", cleaned, re.MULTILINE | re.IGNORECASE)
                    args = {}
                    if path_m:
                        args["path"] = path_m.group(1).strip()
                    if cmd_m:
                        args["command"] = cmd_m.group(1).strip()
                    add_call({"tool": tool_name, "args": args})
                    continue

            fn_match = re.match(r"^([a-zA-Z0-9_]+)\s*\((.*)\)\s*$", cleaned, re.DOTALL)
            if fn_match:
                tool_name = canonicalize_tool_name(fn_match.group(1))
                if tool_name in _KNOWN_TOOL_NAMES:
                    add_call({"tool": tool_name, "args": _parse_kv_params(fn_match.group(2))})

    # 4. Raw unfenced JSON tool objects in text outside fenced code blocks (only when nothing found yet)
    if not calls:
        if fenced_blocks:
            parts = []
            cursor = 0
            for _, _, s_pos, e_pos in fenced_blocks:
                parts.append(text[cursor:s_pos])
                cursor = e_pos
            parts.append(text[cursor:])
            text_no_fences = "\n".join(parts)
        else:
            text_no_fences = text
        raw_objs = extract_json_objects(text_no_fences)
        for obj_str in raw_objs:
            data = parse_json_lenient(obj_str)
            if isinstance(data, dict):
                tc = _dict_to_tool_call(data, require_known=True)
                if tc:
                    add_call(tc)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        tc = _dict_to_tool_call(item, require_known=True)
                        if tc:
                            add_call(tc)

    return normalize_tool_calls(calls)


_ARG_ALIASES = {
    "file_path": "path",
    "filepath": "path",
    "filename": "path",
    "file": "path",
    "dir": "path",
    "directory": "path",
    "start": "start_line",
    "from_line": "start_line",
    "end": "end_line",
    "to_line": "end_line",
    "cmd": "command",
    "shell": "command",
    "q": "query",
    "search_query": "query",
    "link": "url",
    "python_code": "code",
    "py_code": "code",
}

_READ_FILE_ONLY_ALIASES = {
    "offset": "start_line",
    "limit": "end_line",
}


def normalize_tool_args(args: dict, tool_name: str = "") -> dict:
    if not isinstance(args, dict):
        return {}
    canon_tool = canonicalize_tool_name(tool_name) if tool_name else ""
    fixed: Dict[str, Any] = {}
    for key, value in args.items():
        if canon_tool == "read_file" and key in _READ_FILE_ONLY_ALIASES:
            canonical = _READ_FILE_ONLY_ALIASES[key]
        elif canon_tool in ("", "run_python") and key == "source":
            canonical = "code"
        else:
            canonical = _ARG_ALIASES.get(key, key)
        if canonical in fixed and canonical != key:
            continue
        fixed[canonical] = value
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
            "args": normalize_tool_args(raw_args, tool_name=tool_name),
        })

    # Merge ONLY overlapping or directly contiguous read_file ranges on the same path
    merged: List[Dict[str, Any]] = []
    read_entries_by_path: Dict[str, List[int]] = {}
    for call in normalized:
        if call["tool"] != "read_file" or not call["args"].get("path"):
            if call not in merged:
                merged.append(call)
            continue

        args = call["args"]
        path = str(args["path"])
        path_key = path.lower().replace("\\", "/")
        start = max(1, _as_int(args.get("start_line", 1), 1))
        end = _as_int(args.get("end_line", start + MAX_READ_LINES - 1), start + MAX_READ_LINES - 1)
        if end < start:
            start, end = end, start

        indices = read_entries_by_path.get(path_key, [])
        merged_into_existing = False
        for idx in indices:
            target = merged[idx]["args"]
            t_start = target["start_line"]
            t_end = target["end_line"]
            # Merge only if ranges overlap or touch (gap <= 1 line)
            if start <= t_end + 1 and end >= t_start - 1:
                target["start_line"] = min(t_start, start)
                target["end_line"] = max(t_end, end)
                merged_into_existing = True
                break

        if not merged_into_existing:
            read_entries_by_path.setdefault(path_key, []).append(len(merged))
            merged.append({
                "tool": "read_file",
                "args": {"path": path, "start_line": start, "end_line": end},
            })

    return merged


def count_tokens(text: str) -> int:
    if not text:
        return 0
    tokens = re.findall(r"\w+|\S", text)
    return len(tokens)
