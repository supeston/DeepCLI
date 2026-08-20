import asyncio
import ctypes
import json
import os
import queue
import re
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

try:
    from winpty import PtyProcess
    WINPTY_AVAILABLE = True
except ImportError:
    WINPTY_AVAILABLE = False


ANSI_ESCAPE_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

INTERACTIVE_PROMPT_PATTERNS = [
    re.compile(r"\[[yY]/[nN]\]\s*$", re.MULTILINE),
    re.compile(r"\([yY]/[nN]\)\s*$", re.MULTILINE),
    re.compile(r"\[default:\s*[^\]]+\]\s*$", re.MULTILINE),
    re.compile(r"(?:password|passphrase|username|login|email):\s*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"(?:enter|type)\s+[^:\n]+:\s*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"(?:select|choose|choice|confirm|continue|overwrite|proceed)\??\s*[:?]\s*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"(?:Press any key to continue|Press Enter to continue|Hit Enter)[^\n]*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"[?:]\s*$", re.MULTILINE),
    re.compile(r"(?:[❯›>])\s*$", re.MULTILINE),
]


def clean_ansi(text: str) -> str:
    """Strip ANSI VT100 escape codes and normalize carriage returns."""
    if not text:
        return ""
    cleaned = ANSI_ESCAPE_RE.sub("", text)
    cleaned = cleaned.replace("\r\r\n", "\n").replace("\r\n", "\n").replace("\r", "\n")
    return cleaned


def detect_interactive_prompt(text: str) -> Tuple[bool, str]:
    """Check if the text ends with an interactive prompt waiting for user input."""
    if not text:
        return False, ""

    clean = clean_ansi(text).strip()
    if not clean:
        return False, ""

    last_lines = [l.strip() for l in clean.splitlines() if l.strip()]
    if not last_lines:
        return False, ""

    tail = last_lines[-1]
    for pattern in INTERACTIVE_PROMPT_PATTERNS:
        if pattern.search(tail):
            return True, tail

    if len(last_lines) >= 2:
        combined = " ".join(last_lines[-2:])
        for pattern in INTERACTIVE_PROMPT_PATTERNS:
            if pattern.search(combined):
                return True, combined

    return False, ""


# Windows Job Objects definitions for clean child process termination
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


@dataclass
class PtySession:
    session_id: str
    command: str
    proc: Any
    job_handle: Optional[int]
    out_queue: queue.Queue = field(default_factory=queue.Queue)
    reader_thread: Optional[threading.Thread] = None
    accumulated_raw: str = ""
    accumulated_clean: str = ""
    created_at: float = field(default_factory=time.time)
    last_output_time: float = field(default_factory=time.time)
    input_count: int = 0
    status: str = "RUNNING"  # "RUNNING", "WAITING_FOR_INPUT", "COMPLETED", "FAILED", "KILLED"
    exit_code: Optional[int] = None
    prompt_text: str = ""
    stop_event: threading.Event = field(default_factory=threading.Event)


class PtySessionManager:
    """Manages interactive Windows ConPTY pseudo-terminal sessions."""

    def __init__(self):
        self._session_counter: int = 0
        self.active_sessions: Dict[str, PtySession] = {}
        self._lock = threading.Lock()

    def _create_job_object(self) -> Optional[int]:
        """Create a Windows Job Object with KILL_ON_JOB_CLOSE flag."""
        if sys.platform != "win32":
            return None
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.CreateJobObjectW.restype = ctypes.c_void_p
            job_handle = kernel32.CreateJobObjectW(None, None)
            if not job_handle:
                return None
            info = JobObjectExtendedLimitInformation()
            info.BasicLimitInformation.LimitFlags = 0x00002000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            kernel32.SetInformationJobObject(
                ctypes.c_void_p(job_handle),
                9,  # JobObjectExtendedLimitInformation
                ctypes.byref(info),
                ctypes.sizeof(info),
            )
            return int(job_handle)
        except Exception:
            return None

    def _assign_pid_to_job(self, job_handle: int, pid: int) -> bool:
        """Assign PID to the Windows Job Object."""
        if sys.platform != "win32" or not job_handle or not pid:
            return False
        try:
            kernel32 = ctypes.windll.kernel32
            h_process = kernel32.OpenProcess(0x1F0FFF, False, pid)
            if not h_process:
                return False
            assigned = kernel32.AssignProcessToJobObject(
                ctypes.c_void_p(job_handle),
                ctypes.c_void_p(h_process),
            )
            kernel32.CloseHandle(ctypes.c_void_p(h_process))
            return bool(assigned)
        except Exception:
            return False

    def _close_job_handle(self, job_handle: Optional[int]):
        """Close a Job Object handle safely."""
        if job_handle and sys.platform == "win32":
            try:
                ctypes.windll.kernel32.CloseHandle(ctypes.c_void_p(job_handle))
            except Exception:
                pass

    def spawn(
        self,
        command: str,
        cwd: str,
        env: Optional[Dict[str, str]] = None,
        inputs: Optional[str] = None,
    ) -> Tuple[PtySession, Optional[str]]:
        """Spawn a new ConPTY session for command execution."""
        if not WINPTY_AVAILABLE:
            raise RuntimeError("pywinpty is required for ConPTY terminal sessions")

        with self._lock:
            self._session_counter += 1
            session_id = f"pty_{self._session_counter:04d}"

        job_handle = self._create_job_object()

        if sys.platform == "win32":
            spawn_args = [
                os.environ.get("COMSPEC", "cmd.exe"),
                "/c",
                command,
            ]
        else:
            spawn_args = ["/bin/sh", "-c", command]

        child_env = os.environ.copy()
        if env:
            child_env.update(env)
        child_env["PYTHONIOENCODING"] = "utf-8"
        child_env["PYTHONUTF8"] = "1"

        proc = PtyProcess.spawn(
            spawn_args,
            cwd=cwd,
            env=child_env,
            dimensions=(24, 120),
        )

        if job_handle and proc.pid:
            self._assign_pid_to_job(job_handle, proc.pid)

        session = PtySession(
            session_id=session_id,
            command=command,
            proc=proc,
            job_handle=job_handle,
        )

        def reader():
            while not session.stop_event.is_set():
                try:
                    chunk = proc.read(1024)
                    if not chunk:
                        break
                    session.out_queue.put(chunk)
                except Exception:
                    break

        t = threading.Thread(target=reader, daemon=True, name=f"PtyReader-{session_id}")
        session.reader_thread = t
        t.start()

        with self._lock:
            self.active_sessions[session_id] = session

        # If initial inputs provided upfront, write immediately
        if inputs:
            try:
                proc.write(inputs if inputs.endswith("\n") else inputs + "\r\n")
            except Exception:
                pass

        return session, None

    def read_session_loop(
        self,
        session: PtySession,
        max_duration: float = 180.0,
        silence_threshold: float = 1.0,
    ) -> str:
        """
        Poll session output. Returns:
        - If completed: final clean text output.
        - If waiting for input: JSON formatted string with status WAITING_FOR_INPUT.
        """
        start_time = time.time()
        last_data_time = time.time()
        had_data_since_idle = False

        while True:
            # Drain queue
            while not session.out_queue.empty():
                try:
                    chunk = session.out_queue.get_nowait()
                    if chunk:
                        session.accumulated_raw += chunk
                        session.last_output_time = time.time()
                        last_data_time = time.time()
                        had_data_since_idle = True
                except queue.Empty:
                    break

            session.accumulated_clean = clean_ansi(session.accumulated_raw)

            # Check if process exited
            is_alive = session.proc.isalive()
            if not is_alive:
                # Process finished - give reader a moment to drain remaining bytes
                time.sleep(0.15)
                while not session.out_queue.empty():
                    try:
                        chunk = session.out_queue.get_nowait()
                        if chunk:
                            session.accumulated_raw += chunk
                    except queue.Empty:
                        break

                session.accumulated_clean = clean_ansi(session.accumulated_raw)
                session.status = "COMPLETED"
                try:
                    session.exit_code = session.proc.exitstatus
                except Exception:
                    session.exit_code = 0

                self._cleanup_session(session.session_id)

                out = session.accumulated_clean.strip()
                if session.exit_code and session.exit_code != 0:
                    out += f"\n[Exit Code: {session.exit_code}]"
                return out if out else "[OK]"

            # Check interactive prompt wait condition ONLY if we have non-empty clean output
            now = time.time()
            silence_duration = now - last_data_time

            if session.accumulated_clean.strip() and silence_duration >= silence_threshold and had_data_since_idle:
                is_prompt, prompt_line = detect_interactive_prompt(session.accumulated_clean)
                if is_prompt or silence_duration >= (silence_threshold * 2.0):
                    session.status = "WAITING_FOR_INPUT"
                    session.prompt_text = prompt_line or (
                        session.accumulated_clean.splitlines()[-1]
                        if session.accumulated_clean.splitlines()
                        else ""
                    )

                    payload = {
                        "status": "WAITING_FOR_INPUT",
                        "session_id": session.session_id,
                        "prompt_text": session.prompt_text,
                        "accumulated_output": session.accumulated_clean.strip(),
                    }
                    return json.dumps(payload, ensure_ascii=False, indent=2)

            # Global timeout check
            if now - start_time >= max_duration:
                self.kill_session(session.session_id)
                return (
                    f"[Timeout: Process in session '{session.session_id}' exceeded "
                    f"{max_duration}s without completing. Terminated.]\n"
                    f"Last output:\n{session.accumulated_clean.strip()}"
                )

            time.sleep(0.06)

    def send_input(self, session_id: str, text: str) -> str:
        """Send input string to an active ConPTY session and continue reading."""
        with self._lock:
            session = self.active_sessions.get(session_id)

        if not session:
            return f"[Error: No active PTY session with ID '{session_id}']"

        if not session.proc.isalive():
            self._cleanup_session(session_id)
            return f"[Error: PTY session '{session_id}' has already terminated]"

        session.input_count += 1
        if session.input_count > 10:
            self.kill_session(session_id)
            return (
                f"[Error: Maximum interactive input steps (10) exceeded for session "
                f"'{session_id}'. Terminated to prevent infinite loop.]"
            )

        input_str = text if text is not None else ""
        if not input_str.endswith("\n") and not input_str.endswith("\r"):
            input_str += "\r\n"
        else:
            input_str = input_str.replace("\r\n", "\n").replace("\n", "\r\n")

        try:
            session.proc.write(input_str)
        except Exception as e:
            return f"[Error writing to PTY session '{session_id}': {e}]"

        session.status = "RUNNING"
        return self.read_session_loop(session)

    def kill_session(self, session_id: str) -> str:
        """Terminate an active ConPTY session."""
        with self._lock:
            session = self.active_sessions.get(session_id)

        if not session:
            return f"[Error: No active PTY session with ID '{session_id}']"

        session.stop_event.set()
        session.status = "KILLED"

        try:
            session.proc.sendintr()
            time.sleep(0.1)
        except Exception:
            pass

        try:
            session.proc.terminate()
        except Exception:
            pass

        try:
            session.proc.close()
        except Exception:
            pass

        self._close_job_handle(session.job_handle)

        with self._lock:
            self.active_sessions.pop(session_id, None)

        return f"[Success: ConPTY session '{session_id}' terminated.]"

    def _cleanup_session(self, session_id: str):
        """Internal cleanup of session resources."""
        with self._lock:
            session = self.active_sessions.pop(session_id, None)
        if session:
            session.stop_event.set()
            try:
                session.proc.close()
            except Exception:
                pass
            self._close_job_handle(session.job_handle)

    def close_all(self):
        """Terminate all active PTY sessions."""
        with self._lock:
            sessions = list(self.active_sessions.values())
            self.active_sessions.clear()

        for session in sessions:
            session.stop_event.set()
            try:
                session.proc.terminate()
            except Exception:
                pass
            try:
                session.proc.close()
            except Exception:
                pass
            self._close_job_handle(session.job_handle)
