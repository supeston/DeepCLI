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

class SystemToolsMixin:
    def _is_direct_executable_launch(self, command: str) -> bool:
        """Detect a foreground launch of an executable in the last cmd segment."""
        if sys.platform != "win32":
            return False
        tail = re.split(r"&&|\|\||[&|]", str(command or ""))[-1].strip()
        if not tail:
            return False
        # Exclude commands that merely inspect or manipulate an .exe path.
        first = tail.split(None, 1)[0].strip('"').lower()
        cmd_builtins = {
            "dir", "where", "type", "copy", "move", "del", "erase",
            "if", "for", "start", "tasklist", "taskkill",
        }
        return first not in cmd_builtins and bool(
            re.match(r'^(?:"[^"]+\.exe"|\S+\.exe)(?:\s|$)', tail, re.IGNORECASE)
        )

    def run_cmd(self, command: str, inputs: str = None) -> str:
                                                         
        if self._command_touches_self(command) or self._command_touches_self(inputs):
            return self._deny("command referencing DEEPX application files")
        kill_guard = self._process_kill_guard(command)
        if kill_guard:
            return f"[Error: {kill_guard}]"
        try:
            executable_launch = self._is_direct_executable_launch(command)
            timeout_seconds = 10 if executable_launch else 60
            command_to_run = command
            if sys.platform == "win32":
                command_to_run = f"chcp 65001 >nul & {command}"
            child_env = os.environ.copy()
            child_env.pop("FUNSTAT_API_TOKEN", None)
            child_env["PYTHONIOENCODING"] = "utf-8"
            child_env["PYTHONUTF8"] = "1"
            res = subprocess.run(
                command_to_run,
                shell=True,
                cwd=self.cwd,
                input=inputs,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=child_env,
                timeout=timeout_seconds
            )
            out = res.stdout
            if res.stderr:
                out += ("\n" if out else "") + "[STDERR]\n" + res.stderr
            if res.returncode != 0:
                out += f"\n[Exit Code: {res.returncode}]"
            return out.strip() if out.strip() else "[OK]"
        except subprocess.TimeoutExpired:
            if executable_launch:
                return (
                    "[Launch check complete: the executable stayed running for "
                    f"{timeout_seconds} seconds and produced no exit result. "
                    "It is likely an interactive or long-running application. "
                    "Do not wait or retry with run_cmd; report that it launched, "
                    "or use run_background_cmd when continued monitoring is needed.]"
                )
            return (
                f"[Error: Command execution timed out after {timeout_seconds} seconds]"
            )
        except Exception as e:
            return f"[Error executing command: {e}]"

    def run_python(self, code: str) -> str:
                                                                      
        import tempfile
        import os

        if self._command_touches_self(code):
            return self._deny("Python code referencing DEEPX application files")
        kill_guard = self._process_kill_guard(code)
        if kill_guard:
            return f"[Error: {kill_guard}]"
        if re.search(
            r"\bos\.(?:kill|killpg)\s*\(\s*os\.getppid\s*\(",
            code,
        ) or re.search(
            r"\bpsutil\.Process\s*\(\s*os\.getppid\s*\(\s*\)\s*\)"
            r"\s*\.\s*(?:kill|terminate)\s*\(",
            code,
        ):
            return (
                "[Error: Python code may not terminate its parent DEEPX process. "
                "Use a concrete external PID instead.]"
            )

        fd, temp_path = tempfile.mkstemp(suffix=".py", dir=self.cwd)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(code)
            
        try:
            child_env = os.environ.copy()
            child_env.pop("FUNSTAT_API_TOKEN", None)
            child_env["PYTHONIOENCODING"] = "utf-8"
            child_env["PYTHONUTF8"] = "1"
            res = subprocess.run(
                [sys.executable, "-X", "utf8", temp_path],
                cwd=self.cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=child_env,
                timeout=60
            )
            out = res.stdout
            if res.stderr:
                out += ("\n" if out else "") + "[STDERR]\n" + res.stderr
            if res.returncode != 0:
                out += f"\n[Exit Code: {res.returncode}]"
            return out.strip() if out.strip() else "[OK]"
        except subprocess.TimeoutExpired:
            return "[Error: Python script execution timed out after 60 seconds]"
        except Exception as e:
            return f"[Error executing Python script: {e}]"
        finally:
            try:
                os.remove(temp_path)
            except Exception:
                pass

    def _assign_windows_kill_job(self, process):
        if sys.platform != "win32":
            return None

        class JobObjectBasicLimitInformation(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_longlong),
                ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", ctypes.c_uint32),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", ctypes.c_uint32),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", ctypes.c_uint32),
                ("SchedulingClass", ctypes.c_uint32),
            ]

        class IoCounters(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_uint64),
                ("WriteOperationCount", ctypes.c_uint64),
                ("OtherOperationCount", ctypes.c_uint64),
                ("ReadTransferCount", ctypes.c_uint64),
                ("WriteTransferCount", ctypes.c_uint64),
                ("OtherTransferCount", ctypes.c_uint64),
            ]

        class JobObjectExtendedLimitInformation(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", JobObjectBasicLimitInformation),
                ("IoInfo", IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        kernel32 = ctypes.windll.kernel32
        kernel32.CreateJobObjectW.restype = ctypes.c_void_p
        job_handle = kernel32.CreateJobObjectW(None, None)
        if not job_handle:
            return None

        information = JobObjectExtendedLimitInformation()
        information.BasicLimitInformation.LimitFlags = 0x00002000
        configured = kernel32.SetInformationJobObject(
            ctypes.c_void_p(job_handle),
            9,
            ctypes.byref(information),
            ctypes.sizeof(information),
        )
        transport = getattr(process, "_transport", None)
        popen = (
            transport.get_extra_info("subprocess")
            if transport is not None
            else None
        )
        process_handle = getattr(popen, "_handle", None)
        assigned = bool(
            configured
            and process_handle
            and kernel32.AssignProcessToJobObject(
                ctypes.c_void_p(job_handle),
                ctypes.c_void_p(int(process_handle)),
            )
        )
        if assigned:
            return int(job_handle)
        kernel32.CloseHandle(ctypes.c_void_p(job_handle))
        return None

    def _close_windows_kill_job(self, task: dict):
        job_handle = task.get("job_handle")
        if not job_handle:
            return
        task["job_handle"] = None
        ctypes.windll.kernel32.CloseHandle(ctypes.c_void_p(job_handle))

    def _background_process_args(self, command: str):
        if sys.platform != "win32":
            return ["/bin/sh", "-lc", command], None

        import tempfile

        fd, launcher_path = tempfile.mkstemp(
            prefix=".deepx-task-",
            suffix=".cmd",
            dir=tempfile.gettempdir(),
        )
        with os.fdopen(fd, "w", encoding="utf-8", newline="\r\n") as launcher:
            launcher.write("@chcp 65001 >nul\n")
            launcher.write(f"@{command}\n")
        return [
            os.environ.get("COMSPEC", "cmd.exe"),
            "/d",
            "/s",
            "/c",
            launcher_path,
        ], launcher_path

    async def _capture_background_stream(self, task_id: str, stream, label: str):
        while True:
            chunk = await stream.read(4096)
            if not chunk:
                break
            text = chunk.decode("utf-8", errors="replace")
            if label:
                text = f"[{label}]\n{text}"
            task = self.active_tasks.get(task_id)
            if task is None:
                return
            task["log"] += text
            if len(task["log"]) > MAX_BACKGROUND_LOG_CHARS:
                removed = len(task["log"]) - MAX_BACKGROUND_LOG_CHARS
                task["log"] = (
                    f"[Log truncated: removed {removed} oldest characters]\n"
                    + task["log"][-MAX_BACKGROUND_LOG_CHARS:]
                )

    async def _watch_background_task(self, task_id: str):
        task = self.active_tasks[task_id]
        try:
            returncode = await task["process"].wait()
            await asyncio.gather(*task["reader_tasks"], return_exceptions=True)
            task["returncode"] = returncode
            task["ended_at"] = datetime.now(timezone.utc).isoformat()
        finally:
            self._close_windows_kill_job(task)
            launcher_path = task.get("launcher_path")
            if launcher_path:
                try:
                    os.remove(launcher_path)
                except OSError:
                    pass

    async def run_background_cmd(self, command: str, inputs: str = None) -> str:
        if not command:
            return "[Error: run_background_cmd requires a 'command' argument]"
        if self._command_touches_self(command) or self._command_touches_self(inputs):
            return self._deny("background command referencing DEEPX application files")
        kill_guard = self._process_kill_guard(command)
        if kill_guard:
            return f"[Error: {kill_guard}]"

        child_env = os.environ.copy()
        child_env.pop("FUNSTAT_API_TOKEN", None)
        child_env["PYTHONIOENCODING"] = "utf-8"
        child_env["PYTHONUTF8"] = "1"
        launcher_path = None

        try:
            process_args, launcher_path = self._background_process_args(command)
            process_options = {}
            if sys.platform == "win32":
                process_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                process_options["start_new_session"] = True
            process = await asyncio.create_subprocess_exec(
                *process_args,
                cwd=self.cwd,
                env=child_env,
                stdin=asyncio.subprocess.PIPE if inputs is not None else asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                **process_options,
            )
            job_handle = self._assign_windows_kill_job(process)
            self._background_task_counter += 1
            task_id = f"task-{self._background_task_counter:04d}"
            task = {
                "id": task_id,
                "command": command,
                "process": process,
                "pid": process.pid,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "ended_at": None,
                "returncode": None,
                "log": "",
                "launcher_path": launcher_path,
                "job_handle": job_handle,
            }
            self.active_tasks[task_id] = task
            stdout_reader = asyncio.create_task(
                self._capture_background_stream(task_id, process.stdout, "")
            )
            stderr_reader = asyncio.create_task(
                self._capture_background_stream(task_id, process.stderr, "STDERR")
            )
            task["reader_tasks"] = (stdout_reader, stderr_reader)
            task["watcher"] = asyncio.create_task(self._watch_background_task(task_id))

            if inputs is not None and process.stdin is not None:
                process.stdin.write(str(inputs).encode("utf-8"))
                await process.stdin.drain()
                process.stdin.close()

            return (
                f"[Success: Background task '{task_id}' started "
                f"(PID {process.pid}). Use task_status/task_log with this id.]"
            )
        except Exception as e:
            if launcher_path:
                try:
                    os.remove(launcher_path)
                except OSError:
                    pass
            return f"[Error starting background command: {e}]"

    async def task_status(self, task_id: str) -> str:
        task = self.active_tasks.get(str(task_id))
        if task is None:
            return f"[Error: Background task '{task_id}' not found]"
        await asyncio.sleep(0)
        returncode = task["process"].returncode
        if returncode is None:
            status = "running"
        elif returncode == 0:
            status = "completed"
        else:
            status = "failed"
        return (
            f"[Background task '{task_id}': status={status}, PID={task['pid']}, "
            f"exit_code={returncode}, started_at={task['started_at']}, "
            f"ended_at={task.get('ended_at')}]"
        )

    async def task_log(self, task_id: str, tail_lines: int = 200) -> str:
        task = self.active_tasks.get(str(task_id))
        if task is None:
            return f"[Error: Background task '{task_id}' not found]"
        await asyncio.sleep(0)
        try:
            tail_lines = max(1, min(int(tail_lines), 5000))
        except (TypeError, ValueError):
            tail_lines = 200
        log = task["log"]
        if not log:
            state = "running" if task["process"].returncode is None else "finished"
            return f"[Background task '{task_id}' has no output yet; status={state}]"
        lines = log.splitlines()
        shown = "\n".join(lines[-tail_lines:])
        omitted = len(lines) - min(len(lines), tail_lines)
        prefix = f"[Background task '{task_id}' log"
        if omitted:
            prefix += f"; {omitted} earlier line(s) omitted"
        return f"{prefix}]\n{shown}"

    async def close_background_tasks(self):
        running = [
            task for task in self.active_tasks.values()
            if task["process"].returncode is None
        ]
        for task in running:
            try:
                if sys.platform == "win32" and task.get("job_handle"):
                    self._close_windows_kill_job(task)
                elif sys.platform == "win32":
                    task["process"].terminate()
                else:
                    os.killpg(os.getpgid(task["pid"]), signal.SIGTERM)
            except (ProcessLookupError, PermissionError, OSError):
                pass
        for task in running:
            try:
                await asyncio.wait_for(task["process"].wait(), timeout=3)
            except asyncio.TimeoutError:
                try:
                    if sys.platform == "win32":
                        task["process"].kill()
                    else:
                        os.killpg(os.getpgid(task["pid"]), signal.SIGKILL)
                except (ProcessLookupError, PermissionError, OSError):
                    pass
        watchers = [
            task.get("watcher") for task in self.active_tasks.values()
            if task.get("watcher") is not None
        ]
        if watchers:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*watchers, return_exceptions=True),
                    timeout=3,
                )
            except asyncio.TimeoutError:
                for watcher in watchers:
                    if not watcher.done():
                        watcher.cancel()
                await asyncio.gather(*watchers, return_exceptions=True)

    def sys_info(self) -> str:
                                          
        return (
            f"OS: {sys.platform}\n"
            f"Python: {sys.version.split()[0]}\n"
            f"Working Directory: {self.cwd}"
        )

