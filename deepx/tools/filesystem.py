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
        suffix = Path(abs_path).suffix.lower()
        try:
            if suffix == ".py":
                py_compile.compile(abs_path, doraise=True)
            elif suffix == ".json":
                json.loads(content)
            elif suffix in {".js", ".mjs", ".cjs"}:
                node = shutil.which("node")
                if node is None:
                    return "\n[Syntax Check Skipped: Node.js executable was not found]"
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
                    detail = (result.stderr or result.stdout).strip()
                    detail = re.sub(r"\s+", " ", detail)
                    return f"\n[Success: File saved, BUT Syntax Check Failed: {detail}]"
            else:
                return ""
        except py_compile.PyCompileError as error:
            detail = re.sub(r"\s+", " ", str(error))
            return f"\n[Success: File saved, BUT Syntax Check Failed: {detail}]"
        except json.JSONDecodeError as error:
            return (
                "\n[Success: File saved, BUT Syntax Check Failed: "
                f"line {error.lineno}, column {error.colno}: {error.msg}]"
            )
        except subprocess.TimeoutExpired:
            return "\n[Syntax Check Skipped: Node.js syntax check timed out]"
        except Exception as error:
            return f"\n[Syntax Check Skipped: {type(error).__name__}: {error}]"
        return "\n[Syntax Check: OK]"

    def write_file(self, path: str, content: str) -> str:
                                                                                    
        abs_path = os.path.abspath(os.path.join(self.cwd, path))
        if self.is_protected(path):
            return self._deny(path)
        filename = os.path.basename(path)
        existed = os.path.exists(abs_path)
        old_line_count = 0

        if existed:
            try:
                with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                    old_line_count = len(f.readlines())
            except Exception:
                pass

        try:
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            if filename.endswith(".py") or "**" in content:
                content = re.sub(r'\*\*([a-zA-Z0-9_]+)\*\*', r'__\1__', content)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)

            new_line_count = len(content.splitlines())
            syntax_result = self._syntax_check_file(abs_path, content)

            if not existed:
                return (
                    f"[Success: File '{path}' created "
                    f"({new_line_count} lines, {len(content)} bytes)]{syntax_result}"
                )
            else:
                added = max(0, new_line_count - old_line_count)
                removed = max(0, old_line_count - new_line_count)
                stats = []
                if added > 0 or (added == 0 and removed == 0):
                    stats.append(f"[bold #10B981]+{added}[/bold #10B981]")
                if removed > 0:
                    stats.append(f"[bold #EF4444]-{removed}[/bold #EF4444]")
                stat_str = " ".join(stats)
                return (
                    f"[Success: File '{path}' updated "
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
        if self.is_protected(path):
            return self._deny(path)
        filename = os.path.basename(path)
        if not os.path.exists(abs_path):
            return f"[Error: File '{path}' does not exist]"
        try:
            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            match_method = "exact match"
            matched_target = target
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
            elif target and target in content:
                new_content = content.replace(target, replacement, 1)
            else:
                if not target:
                    return (
                        f"[Error: edit_file requires either a non-empty target or "
                        f"start_line/end_line for '{path}']"
                    )
                target_lines_normalized = [
                    line.rstrip() for line in target.splitlines()
                ]
                source_lines = content.splitlines(keepends=True)
                source_lines_normalized = [
                    line.rstrip("\r\n").rstrip() for line in source_lines
                ]
                width = len(target_lines_normalized)
                matches = [
                    index
                    for index in range(len(source_lines_normalized) - width + 1)
                    if source_lines_normalized[index:index + width]
                    == target_lines_normalized
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

            target_lines = len(matched_target.splitlines())
            replacement_lines = len(replacement.splitlines())
            diff = replacement_lines - target_lines
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            syntax_result = self._syntax_check_file(abs_path, new_content)

            added = max(0, diff)
            removed = max(0, -diff)
            stats = []
            if added > 0 or (added == 0 and removed == 0):
                stats.append(f"[bold #10B981]+{added}[/bold #10B981]")
            if removed > 0:
                stats.append(f"[bold #EF4444]-{removed}[/bold #EF4444]")
            stat_str = " ".join(stats)

            return (
                f"[Success: File '{path}' updated successfully using {match_method}]"
                f"{syntax_result}"
            )
        except Exception as e:
            return f"[Error editing file '{path}': {e}]"

    def list_dir(self, path: str = ".") -> str:
                                                    
        abs_path = os.path.abspath(os.path.join(self.cwd, path))
        if self.is_protected(path):
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
        if self.is_protected(path):
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

    def zip_pack(self, zip_path: str, files: list) -> str:
                                              
        abs_zip = os.path.abspath(os.path.join(self.cwd, zip_path))
        import zipfile
        try:
            os.makedirs(os.path.dirname(abs_zip), exist_ok=True)
            if self.is_protected(zip_path):
                return self._deny(zip_path)
            packed = 0
            skipped = 0
            with zipfile.ZipFile(abs_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for f in files:
                    abs_f = os.path.abspath(os.path.join(self.cwd, f))
                    if self.is_protected(f):
                        skipped += 1
                        continue
                    if os.path.exists(abs_f):
                        zipf.write(abs_f, arcname=os.path.basename(f))
                        packed += 1
                    else:
                        skipped += 1
            note = f", {skipped} skipped (missing or protected)" if skipped else ""
            return f"[Success: ZIP archive '{zip_path}' created with {packed} file(s){note}]"
        except Exception as e:
            return f"[Error creating ZIP archive: {e}]"

    def unzip_pack(self, zip_path: str, extract_to: str = ".") -> str:
                                  
        abs_zip = os.path.abspath(os.path.join(self.cwd, zip_path))
        abs_dest = os.path.abspath(os.path.join(self.cwd, extract_to))
        import zipfile
        if self.is_protected(zip_path) or self.is_protected(extract_to):
            return self._deny(zip_path if self.is_protected(zip_path) else extract_to)
        try:
            with zipfile.ZipFile(abs_zip, 'r') as zipf:
                zipf.extractall(abs_dest)
            return f"[Success: ZIP archive '{zip_path}' extracted to '{extract_to}']"
        except Exception as e:
            return f"[Error extracting ZIP archive: {e}]"

