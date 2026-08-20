import asyncio
import concurrent.futures
import ctypes
import difflib
import json
import os
import py_compile
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from deepx.core.constants import *
from deepx.core.config import *
from deepx.ui.markup import *
from deepx.ui.terminal import console
from deepx.tools.terminal_session import PtySessionManager, WINPTY_AVAILABLE


class SystemToolsMixin:
    """System interaction tools including ConPTY interactive terminal and background tasks."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

    @property
    def pty_manager(self) -> PtySessionManager:
        if not hasattr(self, "_pty_manager"):
            self._pty_manager = PtySessionManager()
        return self._pty_manager

    def _is_direct_executable_launch(self, command: str) -> bool:
        """Detect a foreground launch of an executable in the last cmd segment."""
        if sys.platform != "win32":
            return False
        tail = re.split(r"&&|\|\||[&|]", str(command or ""))[-1].strip()
        if not tail:
            return False
        first = tail.split(None, 1)[0].strip('"').lower()
        cmd_builtins = {
            "dir", "where", "type", "copy", "move", "del", "erase",
            "if", "for", "start", "tasklist", "taskkill",
        }
        return first not in cmd_builtins and bool(
            re.match(r'^(?:"[^"]+\.exe"|\S+\.exe)(?:\s|$)', tail, re.IGNORECASE)
        )

    def run_cmd(self, command: str, inputs: str = None) -> str:
        """Execute command in Windows ConPTY pseudo-terminal with interactive prompt detection."""
        if not command or not str(command).strip():
            return "[Error: run_cmd requires a 'command' argument]"

        if self._command_touches_self(command) or self._command_touches_self(inputs):
            return self._deny("command referencing DEEPX application files")
        kill_guard = self._process_kill_guard(command)
        if kill_guard:
            return f"[Error: {kill_guard}]"

        # ConPTY Engine Execution
        if WINPTY_AVAILABLE:
            try:
                child_env = os.environ.copy()
                child_env.pop("FUNSTAT_API_TOKEN", None)
                child_env["PYTHONIOENCODING"] = "utf-8"
                child_env["PYTHONUTF8"] = "1"

                session, err = self.pty_manager.spawn(
                    command=command,
                    cwd=self.cwd,
                    env=child_env,
                    inputs=inputs,
                )
                if err:
                    return f"[Error spawning ConPTY session: {err}]"

                # Read output until completion or interactive prompt
                return self.pty_manager.read_session_loop(session)
            except Exception as pty_err:
                # Fallback to subprocess on unexpected PTY spawn error
                pass

        # Subprocess Fallback
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
                timeout=timeout_seconds,
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

    def send_input(self, session_id: str, text: str = "") -> str:
        """Send input to an active interactive ConPTY terminal session."""
        if not session_id:
            return "[Error: send_input requires a 'session_id' argument]"
        return self.pty_manager.send_input(session_id, text)

    def kill_cmd(self, session_id: str) -> str:
        """Terminate an active interactive ConPTY terminal session."""
        if not session_id:
            return "[Error: kill_cmd requires a 'session_id' argument]"
        return self.pty_manager.kill_session(session_id)

    def run_python(self, code: str) -> str:
        """Execute Python code in an isolated temporary script."""
        if not code or not str(code).strip():
            return "[Error: run_python requires a 'code' argument]"

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
                timeout=60,
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
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def _assign_windows_kill_job(self, process) -> Optional[int]:
        if sys.platform != "win32":
            return None

        class JobObjectBasicLimitInformation(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_int64),
                ("PerJobUserTimeLimit", ctypes.c_int64),
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
                "reader_tasks": [],
                "watcher": None,
            }
            task["reader_tasks"] = [
                asyncio.create_task(
                    self._capture_background_stream(task_id, process.stdout, "")
                ),
                asyncio.create_task(
                    self._capture_background_stream(task_id, process.stderr, "STDERR")
                ),
            ]
            task["watcher"] = asyncio.create_task(
                self._watch_background_task(task_id)
            )
            self.active_tasks[task_id] = task
            if inputs:
                try:
                    process.stdin.write(inputs.encode("utf-8"))
                    await process.stdin.drain()
                    process.stdin.close()
                except (BrokenPipeError, ConnectionResetError):
                    pass
            return (
                f"[Background task started]\n"
                f"ID: {task_id}\n"
                f"PID: {process.pid}\n"
                f"Command: {command}\n"
                f"Status: running\n"
                f"Use task_status id=\"{task_id}\" or task_log id=\"{task_id}\"."
            )
        except Exception as error:
            if launcher_path:
                try:
                    os.remove(launcher_path)
                except OSError:
                    pass
            return f"[Error starting background task: {type(error).__name__}: {error}]"

    def task_status(self, id: str) -> str:
        if not id:
            return "[Error: task_status requires an 'id' argument]"
        task = self.active_tasks.get(id)
        if not task:
            return f"[Error: Unknown background task '{id}']"
        if task["ended_at"] is None:
            status = "running"
        elif task["returncode"] == 0:
            status = "completed"
        else:
            status = "failed"
        report = [
            f"[Background task status for '{id}']",
            f"Command: {task['command']}",
            f"PID: {task['pid']}",
            f"Status: {status}",
            f"Started: {task['started_at']}",
        ]
        if task["ended_at"]:
            report.append(f"Ended: {task['ended_at']}")
            report.append(f"Exit Code: {task['returncode']}")
        report.append(f"Buffered Log Chars: {len(task['log']):,}")
        return "\n".join(report)

    def task_log(self, id: str, tail_lines: int = 200) -> str:
        if not id:
            return "[Error: task_log requires an 'id' argument]"
        task = self.active_tasks.get(id)
        if not task:
            return f"[Error: Unknown background task '{id}']"
        try:
            tail_count = max(1, int(tail_lines))
        except (TypeError, ValueError):
            tail_count = 200
        lines = task["log"].splitlines()
        selected = lines[-tail_count:] if lines else []
        status = "running" if task["ended_at"] is None else "finished"
        header = (
            f"[Background task log for '{id}' ({status}, showing "
            f"{len(selected)} of {len(lines)} lines)]:\n"
        )
        return header + ("\n".join(selected) if selected else "(No output recorded yet)")

    async def close_background_tasks(self):
        """Clean up PTY sessions and background tasks on shutdown."""
        if hasattr(self, "_pty_manager"):
            self._pty_manager.close_all()

        for task in self.active_tasks.values():
            if task.get("process") and task["process"].returncode is None:
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
