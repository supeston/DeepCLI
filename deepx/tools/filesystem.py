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

class FileSystemToolsMixin:
    def read_file(self, path: str, start_line: int = 1, end_line: int = 500) -> str:
                                          
        if not path:
            return "[Error: read_file requires a 'path' argument]"
        abs_path = os.path.abspath(os.path.join(self.cwd, path))
        if self.is_protected(path):
            return self._deny(path)
        if not os.path.exists(abs_path):
            return f"[Error: File '{path}' does not exist]"
        if os.path.isdir(abs_path):
            return f"[Error: Path '{path}' is a directory, not a file]"
        try:
            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            try:
                start = max(1, int(start_line)) - 1
            except (TypeError, ValueError):
                start = 0
            try:
                end = min(len(lines), int(end_line))
            except (TypeError, ValueError):
                end = min(len(lines), start + MAX_READ_LINES)

                                                                                              
                                                                           
            truncated = False
            if end - start > MAX_READ_LINES:
                end = start + MAX_READ_LINES
                truncated = True

            selected = lines[start:end]
            formatted = "".join(f"{i + start + 1:4d} | {line}" for i, line in enumerate(selected))
            header = f"--- Content of {path} (Lines {start+1}-{end} of {len(lines)}) ---"
            footer = ""
            if truncated or end < len(lines):
                footer = (
                    f"\n[Truncated: shown {end - start} of {len(lines)} lines. "
                    f"Continue with read_file path=\"{path}\" start_line={end + 1}]"
                )
            return f"{header}\n{formatted}{footer}"
        except Exception as e:
            return f"[Error reading file '{path}': {e}]"

    def _syntax_check_file(self, abs_path: str, content: str) -> str:
        ext = os.path.splitext(abs_path)[1].lower()
        if ext == ".py":
            try:
                import ast
                ast.parse(content, filename=abs_path)
            except SyntaxError as exc:
                line = exc.lineno or "?"
                col = exc.offset or "?"
                return f"\n[Success: File saved, BUT Syntax Check Failed: line {line}, column {col}: {exc.msg}]"
            except Exception as exc:
                return f"\n[Success: File saved, BUT Syntax Check Failed: {exc}]"
            return "\n[Syntax Check: OK]"
        if ext == ".json":
            try:
                json.loads(content)
            except json.JSONDecodeError as exc:
                return (
                    "\n[Success: File saved, BUT Syntax Check Failed: "
                    f"line {exc.lineno}, column {exc.colno}: {exc.msg}]"
                )
            return "\n[Syntax Check: OK]"
        if ext in {".js", ".mjs", ".cjs"}:
            node = shutil.which("node")
            if node is None:
                return "\n[Syntax Check Skipped: Node.js executable was not found]"
            try:
                result = subprocess.run(
                    [node, "--check", abs_path],
                    cwd=self.cwd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=15,
                )
                if result.returncode != 0:
                    detail = re.sub(r"\s+", " ", (result.stderr or result.stdout).strip())
                    return f"\n[Success: File saved, BUT Syntax Check Failed: {detail}]"
                return "\n[Syntax Check: OK]"
            except subprocess.TimeoutExpired:
                return "\n[Syntax Check Skipped: Node.js syntax check timed out]"
            except Exception as exc:
                return f"\n[Syntax Check Skipped: {type(exc).__name__}: {exc}]"
        return ""

    def grep_search(
        self,
        query: str,
        path: str = ".",
        include: str = "",
        case_sensitive: bool = False,
        regex: bool = False,
        max_results: int = 80,
    ) -> str:
        """Fast recursive text/regex search across project files (skips .git/.venv/node_modules)."""
        if not query or not str(query):
            return "[Error: grep_search requires a non-empty 'query' argument]"

        target_root = path if os.path.isabs(path) else os.path.join(self.cwd, path or ".")
        target_root = os.path.abspath(target_root)
        if self.is_protected(target_root):
            return self._deny(target_root)
        if not os.path.exists(target_root):
            return f"[Error: Path not found: {target_root}]"

        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(query if regex else re.escape(query), flags)
        except re.error as exc:
            return f"[Error: Invalid regex '{query}': {exc}]"

        from deepx.agent.repo_map import IGNORED_DIRS
        import fnmatch

        limit = max(1, min(int(max_results or 80), 300))
        matches = []
        searched_files = 0

        if os.path.isfile(target_root):
            files_to_scan = [target_root]
        else:
            files_to_scan = []
            for root_str, dirs, files in os.walk(target_root):
                dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS)
                for fname in sorted(files):
                    if include and not fnmatch.fnmatch(fname, include):
                        continue
                    full_p = os.path.join(root_str, fname)
                    if not self.is_protected(full_p):
                        files_to_scan.append(full_p)

        for file_path in files_to_scan:
            if len(matches) >= limit:
                break
            try:
                if os.path.getsize(file_path) > 1_500_000:
                    continue
                with open(file_path, "rb") as fb:
                    sample = fb.read(2048)
                if b"\x00" in sample:
                    continue
                with open(file_path, "r", encoding="utf-8-sig", errors="replace") as f:
                    searched_files += 1
                    try:
                        rel_path = os.path.relpath(file_path, self.cwd).replace("\\", "/")
                    except Exception:
                        rel_path = file_path
                    for lineno, line_text in enumerate(f, 1):
                        if pattern.search(line_text):
                            snippet = line_text.rstrip("\r\n")
                            if len(snippet) > 220:
                                snippet = snippet[:217] + "..."
                            matches.append(f"{rel_path}:{lineno}: {snippet}")
                            if len(matches) >= limit:
                                break
            except Exception:
                continue

        if not matches:
            return f"[No matches for '{query}' across {searched_files} files in '{path}']"
        suffix = f"\n[Showing first {limit} matches]" if len(matches) >= limit else ""
        return "\n".join(matches) + suffix

    def write_file(self, path: str, content: str) -> str:
        abs_path = os.path.abspath(os.path.join(self.cwd, path))
        if self.is_protected(path) or self.is_protected(abs_path):
            return self._deny(path)
        existed = os.path.exists(abs_path)

        try:
            os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)
            if getattr(self, "checkpoints", None) is not None:
                self.checkpoints.record_before_modify(abs_path, "write_file")
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)

            new_line_count = len(content.splitlines())
            syntax_result = self._syntax_check_file(abs_path, content)

            action_word = "updated" if existed else "created"
            return (
                f"[Success: File '{path}' {action_word} "
                f"({new_line_count} lines, {len(content)} bytes)]{syntax_result}"
            )
        except Exception as e:
            return f"[Error writing file '{path}': {e}]"

    def edit_file(
        self,
        path: str,
        target: str = "",
        replacement: str = "",
        start_line=None,
        end_line=None,
    ) -> str:
        abs_path = os.path.abspath(os.path.join(self.cwd, path))
        if self.is_protected(path) or self.is_protected(abs_path):
            return self._deny(path)
        if not os.path.exists(abs_path):
            return f"[Error: File '{path}' does not exist]"
        try:
            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            match_method = "exact match"
            if start_line is not None or end_line is not None:
                try:
                    start = int(start_line if start_line is not None else end_line)
                    end = int(end_line if end_line is not None else start_line)
                except (TypeError, ValueError):
                    return f"[Error: start_line and end_line must be integers for '{path}']"
                if start < 1 or end < start:
                    return f"[Error: Invalid line range {start}-{end} for '{path}']"
                source_lines = content.splitlines(keepends=True)
                if start > len(source_lines) or end > len(source_lines):
                    return (
                        f"[Error: Line range {start}-{end} is outside '{path}' "
                        f"(1-{len(source_lines)})]"
                    )
                matched_target = "".join(source_lines[start - 1:end])
                line_ending = "\r\n" if "\r\n" in matched_target else "\n"
                range_replacement = replacement
                if (
                    range_replacement
                    and matched_target.endswith(("\n", "\r"))
                    and not range_replacement.endswith(("\n", "\r"))
                    and end < len(source_lines)
                ):
                    range_replacement += line_ending
                prefix = "".join(source_lines[:start - 1])
                suffix = "".join(source_lines[end:])
                new_content = prefix + range_replacement + suffix
                match_method = f"line range {start}-{end}"
            else:
                if not target or not str(target).strip():
                    return (
                        f"[Error: edit_file requires a non-empty, non-whitespace target "
                        f"or start_line/end_line for '{path}']"
                    )
                if target in content:
                    occ = content.count(target)
                    if occ > 1:
                        line_nums = []
                        pos = 0
                        for _ in range(min(occ, 10)):
                            idx = content.find(target, pos)
                            if idx == -1:
                                break
                            line_nums.append(str(content[:idx].count("\n") + 1))
                            pos = idx + len(target)
                        return (
                            f"[Error: Target string is ambiguous in '{path}' "
                            f"({occ} occurrences at lines {', '.join(line_nums)}); "
                            f"provide more context or use start_line/end_line]"
                        )
                    new_content = content.replace(target, replacement, 1)
                else:
                    target_lines_normalized = [line.rstrip() for line in target.splitlines()]
                    if not target_lines_normalized or all(not ln.strip() for ln in target_lines_normalized):
                        return f"[Error: Target string not found cleanly in '{path}']"
                    source_lines = content.splitlines(keepends=True)
                    source_lines_normalized = [
                        line.rstrip("\r\n").rstrip() for line in source_lines
                    ]
                    width = len(target_lines_normalized)
                    matches = [
                        index
                        for index in range(len(source_lines_normalized) - width + 1)
                        if source_lines_normalized[index:index + width] == target_lines_normalized
                    ]
                    if not matches:
                        return f"[Error: Target string not found in '{path}', including normalized matching]"
                    if len(matches) > 1:
                        lines = ", ".join(str(index + 1) for index in matches[:10])
                        return (
                            f"[Error: Normalized target is ambiguous in '{path}' "
                            f"(matches start at lines {lines}); use start_line/end_line]"
                        )
                    index = matches[0]
                    matched_target = "".join(source_lines[index:index + width])
                    line_ending = "\r\n" if "\r\n" in matched_target else "\n"
                    fuzzy_replacement = replacement
                    if (
                        fuzzy_replacement
                        and matched_target.endswith(("\n", "\r"))
                        and not fuzzy_replacement.endswith(("\n", "\r"))
                        and index + width < len(source_lines)
                    ):
                        fuzzy_replacement += line_ending
                    new_content = (
                        "".join(source_lines[:index])
                        + fuzzy_replacement
                        + "".join(source_lines[index + width:])
                    )
                    match_method = f"normalized whitespace match at line {index + 1}"

            if getattr(self, "checkpoints", None) is not None:
                self.checkpoints.record_before_modify(abs_path, "edit_file")
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            syntax_result = self._syntax_check_file(abs_path, new_content)

            return (
                f"[Success: File '{path}' updated successfully using {match_method}]"
                f"{syntax_result}"
            )
        except Exception as e:
            return f"[Error editing file '{path}': {e}]"

    def list_dir(self, path: str = ".") -> str:
        abs_path = os.path.abspath(os.path.join(self.cwd, path))
        if self.is_protected(path) or self.is_protected(abs_path):
            return self._deny(path)
        if not os.path.exists(abs_path):
            return f"[Error: Path '{path}' does not exist]"
        try:
            entries = sorted(os.listdir(abs_path))
            dirs = []
            files = []
            for entry in entries:
                full = os.path.join(abs_path, entry)
                if self.is_protected(full):
                    continue
                if os.path.isdir(full):
                    dirs.append(f"[DIR]  {entry}/")
                else:
                    size = os.path.getsize(full)
                    files.append(f"[FILE] {entry} ({size:,} bytes)")
            out = dirs + files
            return f"--- Contents of {path} ({len(out)} items) ---\n" + ("\n".join(out) if out else "[Empty Directory]")
        except Exception as e:
            return f"[Error listing directory '{path}': {e}]"

    def file_info(self, path: str) -> str:
        abs_path = os.path.abspath(os.path.join(self.cwd, path))
        if self.is_protected(path) or self.is_protected(abs_path):
            return self._deny(path)
        if not os.path.exists(abs_path):
            return f"[Error: File '{path}' does not exist]"
        try:
            stat = os.stat(abs_path)
            return (
                f"Path: {path}\n"
                f"Absolute: {abs_path}\n"
                f"Type: {'Directory' if os.path.isdir(abs_path) else 'File'}\n"
                f"Size: {stat.st_size:,} bytes\n"
                f"Modified: {stat.st_mtime}"
            )
        except Exception as e:
            return f"[Error retrieving info for '{path}': {e}]"

    def zip_pack(self, zip_path: str, files) -> str:
        import zipfile

        abs_zip = os.path.abspath(os.path.join(self.cwd, zip_path))
        if self.is_protected(zip_path) or self.is_protected(abs_zip):
            return self._deny(zip_path)

        if isinstance(files, str):
            file_items = [files]
        elif isinstance(files, (list, tuple)):
            file_items = list(files)
        else:
            return "[Error: zip_pack 'files' must be a path or list of paths]"

        for item in file_items:
            raw_item = str(item or "").strip()
            if not raw_item:
                continue
            abs_f = os.path.abspath(os.path.join(self.cwd, raw_item))
            if self.is_protected(raw_item) or self.is_protected(abs_f):
                return self._deny(raw_item)

        try:
            zip_dir = os.path.dirname(abs_zip)
            if zip_dir:
                os.makedirs(zip_dir, exist_ok=True)
            packed = 0
            skipped = 0
            cwd_real = os.path.realpath(self.cwd)
            zip_real = os.path.realpath(abs_zip)

            with zipfile.ZipFile(abs_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
                for item in file_items:
                    raw_item = str(item or "").strip()
                    if not raw_item:
                        skipped += 1
                        continue
                    abs_f = os.path.abspath(os.path.join(self.cwd, raw_item))
                    if self.is_protected(raw_item) or self.is_protected(abs_f):
                        return self._deny(raw_item)
                    if not os.path.exists(abs_f):
                        skipped += 1
                        continue

                    if os.path.isdir(abs_f):
                        base_parent = os.path.dirname(os.path.abspath(abs_f))
                        for root_dir, dirs, dir_files in os.walk(abs_f):
                            dirs[:] = [
                                d for d in sorted(dirs)
                                if not self.is_protected(os.path.join(root_dir, d))
                            ]
                            for fname in sorted(dir_files):
                                full_child = os.path.join(root_dir, fname)
                                if os.path.realpath(full_child) == zip_real:
                                    continue
                                if self.is_protected(full_child):
                                    skipped += 1
                                    continue
                                try:
                                    arc = os.path.relpath(full_child, cwd_real)
                                    if arc.startswith(".."):
                                        arc = os.path.relpath(full_child, base_parent)
                                except Exception:
                                    arc = os.path.relpath(full_child, base_parent)
                                zipf.write(full_child, arcname=arc.replace("\\", "/"))
                                packed += 1
                    else:
                        if os.path.realpath(abs_f) == zip_real:
                            continue
                        try:
                            arc = os.path.relpath(abs_f, cwd_real)
                            if arc.startswith(".."):
                                arc = os.path.basename(abs_f)
                        except Exception:
                            arc = os.path.basename(abs_f)
                        zipf.write(abs_f, arcname=arc.replace("\\", "/"))
                        packed += 1

            note = f", {skipped} skipped (missing or protected)" if skipped else ""
            return f"[Success: ZIP archive '{zip_path}' created with {packed} file(s){note}]"
        except Exception as e:
            return f"[Error creating ZIP archive: {e}]"

    def unzip_pack(self, zip_path: str, extract_to: str = ".") -> str:
        import zipfile

        abs_zip = os.path.abspath(os.path.join(self.cwd, zip_path))
        abs_dest = os.path.abspath(os.path.join(self.cwd, extract_to))
        if self.is_protected(zip_path) or self.is_protected(abs_zip):
            return self._deny(zip_path)
        if self.is_protected(extract_to) or self.is_protected(abs_dest):
            return self._deny(extract_to)
        try:
            dest_real = os.path.realpath(abs_dest)
            os.makedirs(abs_dest, exist_ok=True)
            with zipfile.ZipFile(abs_zip, "r") as zipf:
                for info in zipf.infolist():
                    target_member = os.path.realpath(os.path.join(dest_real, info.filename))
                    if not (target_member == dest_real or target_member.startswith(dest_real + os.sep)):
                        return f"[Security Blocked: Unsafe path in archive '{info.filename}']"
                    if self.is_protected(target_member):
                        return self._deny(info.filename)
                zipf.extractall(abs_dest)
            return f"[Success: ZIP archive '{zip_path}' extracted to '{extract_to}']"
        except Exception as e:
            return f"[Error extracting ZIP archive: {e}]"

