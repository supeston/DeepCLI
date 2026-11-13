import asyncio
import os
import shutil
import sys
import time
from typing import Optional


_SPINNER_FRAMES = ("|", "/", "-", "\\")


def describe_tool_action(tool_name: str, args: Optional[dict] = None) -> str:
    """Return a clean, emoji-free Russian single-line status label for a tool action."""
    args = args or {}
    path_val = str(args.get("path") or args.get("output") or args.get("source") or "").strip()
    basename = os.path.basename(path_val.rstrip("\\/")) if path_val else ""

    if tool_name == "read_file":
        return f"Читаю {basename}..." if basename else "Читаю файл..."
    if tool_name in ("write_file", "edit_file"):
        return f"Правлю {basename}..." if basename else "Редактирую файл..."
    if tool_name in ("list_dir", "grep_search", "file_info"):
        return f"Ищу в {basename}..." if basename else "Ищу по проекту..."
    if tool_name == "run_cmd":
        cmd = str(args.get("command") or "").strip().lower()
        if any(k in cmd for k in ("pytest", "unittest", "test", "py_compile", "compileall")):
            return "Проверяю запуск и тесты..."
        return "Выполняю команду..."
    if tool_name in ("run_background_cmd", "task_status", "task_log", "kill_background_cmd", "send_input", "kill_cmd"):
        return "Управляю процессом..."
    if tool_name == "run_python":
        return "Выполняю Python..."
    if tool_name == "web_search":
        return "Ищу в сети..."
    if tool_name == "fetch_url":
        return "Загружаю страницу..."
    if tool_name == "browser_action":
        return "Работаю в браузере..."
    if tool_name == "vds_deploy":
        action = str(args.get("action") or "exec").lower()
        if action in ("upload", "put", "quick_deploy", "deploy"):
            return "Деплою на сервер..."
        return "Работаю с сервером..."
    if tool_name in ("make_docx", "make_pptx", "make_excel", "render_plan"):
        return f"Создаю {basename}..." if basename else "Формирую документ..."
    if tool_name in ("zip_pack", "unzip_pack"):
        return "Обрабатываю архив..."
    if tool_name == "inspect_media":
        return f"Анализирую {basename}..." if basename else "Анализирую медиа..."
    if tool_name in ("dadata_osint", "funstat_osint"):
        return "Запрашиваю OSINT-данные..."
    if tool_name == "todo":
        return "Обновляю список задач..."
    if tool_name == "project_memory":
        return "Обновляю память проекта..."
    if "clipboard" in tool_name:
        return "Работаю с буфером обмена..."
    return f"Выполняю {tool_name}..."


class SingleLineStatus:
    """In-place minimalist single-line status indicator with elapsed timer."""

    def __init__(self, stream=None):
        self._stream = stream if stream is not None else sys.stdout
        self._text: str = ""
        self._active: bool = False
        self._started_at: float = 0.0
        self._frame_idx: int = 0
        self._ticker_task: Optional[asyncio.Task] = None
        self._last_non_tty_text: str = ""

    @property
    def active(self) -> bool:
        return self._active

    def _is_tty(self) -> bool:
        try:
            return bool(self._stream.isatty())
        except Exception:
            return False

    def _terminal_width(self) -> int:
        try:
            return max(30, shutil.get_terminal_size((100, 24)).columns)
        except Exception:
            return 100

    def _format_line(self) -> str:
        spinner = _SPINNER_FRAMES[self._frame_idx % len(_SPINNER_FRAMES)]
        elapsed = max(0.0, time.monotonic() - self._started_at)
        line = f"{spinner} {self._text} ({elapsed:.1f}s)"
        max_len = max(20, self._terminal_width() - 2)
        if len(line) > max_len:
            line = line[: max_len - 3] + "..."
        return line

    def _paint(self) -> None:
        if not self._active or not self._text:
            return
        if self._is_tty():
            line = self._format_line()
            try:
                self._stream.write(f"\r\x1b[2K{line}")
                self._stream.flush()
            except Exception:
                pass
        elif self._text != self._last_non_tty_text:
            self._last_non_tty_text = self._text
            try:
                self._stream.write(f"[*] {self._text}\n")
                self._stream.flush()
            except Exception:
                pass

    async def _ticker_loop(self) -> None:
        try:
            while self._active:
                await asyncio.sleep(0.12)
                if not self._active:
                    break
                self._frame_idx += 1
                if self._is_tty():
                    self._paint()
        except asyncio.CancelledError:
            pass

    def start(self, text: str) -> None:
        self._text = str(text or "").strip()
        if not self._text:
            return
        if not self._active:
            self._started_at = time.monotonic()
        self._active = True
        self._paint()
        if self._is_tty() and (self._ticker_task is None or self._ticker_task.done()):
            try:
                loop = asyncio.get_running_loop()
                self._ticker_task = loop.create_task(self._ticker_loop())
            except RuntimeError:
                self._ticker_task = None

    def update(self, text: str, reset_timer: bool = False) -> None:
        new_text = str(text or "").strip()
        if not new_text:
            return
        if not self._active or reset_timer:
            self._started_at = time.monotonic()
        self._text = new_text
        self._active = True
        self._paint()
        if self._is_tty() and (self._ticker_task is None or self._ticker_task.done()):
            try:
                loop = asyncio.get_running_loop()
                self._ticker_task = loop.create_task(self._ticker_loop())
            except RuntimeError:
                self._ticker_task = None

    def clear(self) -> None:
        was_active = self._active
        self._active = False
        self._text = ""
        self._last_non_tty_text = ""
        task = self._ticker_task
        self._ticker_task = None
        if task is not None and not task.done():
            task.cancel()
        if was_active and self._is_tty():
            try:
                self._stream.write("\r\x1b[2K")
                self._stream.flush()
            except Exception:
                pass

    async def stop(self) -> None:
        task = self._ticker_task
        self.clear()
        if task is not None:
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
