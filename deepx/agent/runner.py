import asyncio
import inspect
import json
import os
import re
import signal
import subprocess
import sys
import threading
from typing import Callable, Optional

import pyperclip
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.styles import Style as PTStyle

from rich import box
from rich.align import Align
from rich.table import Table
from rich.text import Text

from deepx.api.deep_api import (
    DeepAPI,
    DeepSeekAccountBannedError,
    DeepSeekAuthRequiredError,
)
from deepx.agent.checkpoints import classify_dangerous_operation
from deepx.agent.completer import SlashCommandCompleter
from deepx.agent.prompts import (
    _tool_result_failed,
    build_agent_system_prompt,
    build_agent_task_state,
    build_compacted_session_seed,
    compact_conversation_history,
    normalize_style_name,
)
from deepx.agent.repo_map import build_zero_turn_context
from deepx.core.config import (
    APP_DIR,
    COMMANDS_DICT,
    STYLE_CONFIGS,
)
from deepx.core.constants import (
    MAX_EMPTY_RESPONSE_RETRIES,
    MAX_TOOL_FEEDBACK_CHARS,
    MUTATING_TOOLS_REQUIRING_VERIFICATION,
    PARALLEL_READ_ONLY_TOOLS,
    TASK_GOAL_REMINDER_INTERVAL,
    TODO_NUDGE_AFTER_TOOLS,
    VERIFICATION_TOOLS,
)
from deepx.core.updater import check_for_updates, perform_self_update
from deepx.core.version import UpdateInfo, get_local_version
from deepx.parser.tool_parser import count_tokens, extract_tool_calls
from deepx.tools.manager import AgentTools
from deepx.ui.banner import (
    print_help,
    print_status,
    render_account_ban_panel,
    render_banner,
)
from deepx.ui.markup import (
    StreamingMarkupRenderer,
    get_clean_text,
    sanitize_tool_result,
)
from deepx.ui.status import SingleLineStatus, describe_tool_action
from deepx.ui.streaming import AdaptiveStreamWriter
from deepx.ui.terminal import (
    _begin_windows_ctrl_c_key_mode,
    _restore_windows_console_mode,
    _wait_for_windows_control_key,
    console,
    disable_quick_edit_mode,
    read_single_key_confirm,
    register_cleanup_callback,
)


_MODE_ALIASES = {
    "instant": "instant",
    "fast": "instant",
    "think": "think",
    "expert": "think",
    "plan": "plan",
}

AUTO_COMPACT_CHAR_THRESHOLD = 48000
RECENT_STEPS_FULL = 4


def _normalize_mode_name(value: str) -> Optional[str]:
    return _MODE_ALIASES.get((value or "").strip().lower())


async def _run_in_daemon_thread(fn: Callable):
    """Run blocking console I/O in a daemon thread so exit never waits on ReadConsoleW."""
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    def _worker():
        try:
            result = fn()
        except BaseException as exc:
            if not loop.is_closed():
                loop.call_soon_threadsafe(
                    lambda: not future.done() and future.set_exception(exc)
                )
        else:
            if not loop.is_closed():
                loop.call_soon_threadsafe(
                    lambda: not future.done() and future.set_result(result)
                )

    threading.Thread(target=_worker, daemon=True).start()
    return await future


def _extract_waiting_for_input(tool_outputs: list) -> tuple[Optional[dict], list[str]]:
    """Find a brace-balanced WAITING_FOR_INPUT payload and return other outputs."""
    waiting_payload = None
    other_outputs = []
    decoder = json.JSONDecoder()

    for output in tool_outputs:
        text = str(output or "")
        if "WAITING_FOR_INPUT" not in text or waiting_payload is not None:
            other_outputs.append(text)
            continue

        marker = re.search(r'"status"\s*:\s*"WAITING_FOR_INPUT"', text)
        parsed = None
        if marker:
            search_pos = marker.start()
            while True:
                brace_pos = text.rfind("{", 0, search_pos + 1)
                if brace_pos < 0:
                    break
                try:
                    candidate, _ = decoder.raw_decode(text[brace_pos:])
                    if isinstance(candidate, dict) and candidate.get("status") == "WAITING_FOR_INPUT":
                        parsed = candidate
                        break
                except json.JSONDecodeError:
                    pass
                search_pos = brace_pos - 1
                if search_pos < 0:
                    break

        if parsed is not None:
            waiting_payload = parsed
        else:
            other_outputs.append(text)

    return waiting_payload, other_outputs


def _summarize_tool_error(output: str, max_lines: int = 12, max_chars: int = 1200) -> str:
    """Return concise error lines; preserve full traceback when one actually occurred."""
    text = str(output or "").strip()
    if text.startswith("[TOOL RESULT for "):
        text = text.split("\n", 1)[1].strip() if "\n" in text else text
    if "Traceback (most recent call last):" in text:
        return text[-3000:]
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) > max_lines:
        lines = lines[:max_lines] + [f"... (+{len(lines) - max_lines} строк)"]
    joined = "\n".join(lines)
    if len(joined) > max_chars:
        joined = joined[:max_chars] + "..."
    return joined


class DeepCLIApp:
    def __init__(
        self,
        state_file: str = "state.json",
        headless: bool = True,
        cwd: str = None,
        confirm_fn: Optional[Callable[[str], bool]] = None,
    ):
        self.state_file = state_file
        self.headless = headless
        self.mode = "instant"
        self.agent_style = "coder"
        self.think = False
        self.search = False
        self.tools = AgentTools(cwd=cwd, browser_headless=headless)
        self.tools.add_protected(state_file)
        self._apply_style_guard()
        self._sync_mode_flags("instant", sync_think=True)
        self.last_response = ""
        self.is_new_chat = True
        self.turn_history = []
        self._pending_workspace_context = ""
        self._mode_change_notice = ""
        self._compacted_seed_pending = ""
        self._active_status: Optional[SingleLineStatus] = None
        self._exit_requested = False
        self._confirm_fn = confirm_fn or read_single_key_confirm
        self.update_info: Optional[UpdateInfo] = None

        register_cleanup_callback(self._sync_cleanup)

        completer = SlashCommandCompleter(COMMANDS_DICT)
        pt_style = PTStyle.from_dict({
            "completion-menu": "bg:#0F172A #E2E8F0",
            "completion-menu.completion": "bg:#0F172A #94A3B8",
            "completion-menu.completion.current": "bg:#536DFE #FFFFFF bold",
            "completion-menu.meta.completion": "bg:#0F172A #64748B",
            "completion-menu.meta.completion.current": "bg:#3B82F6 #EFF6FF",
            "scrollbar.background": "bg:#0F172A",
            "scrollbar.button": "bg:#334155",
            "prompt": "bold #536DFE",
            "mode-think": "bold #A78BFA",
            "mode-plan": "bold #38BDF8",
        })
        self._dialog_style = PTStyle.from_dict({
            "dialog": "bg:#0F172A #E2E8F0",
            "dialog frame.label": "bg:#0F172A #536DFE bold",
            "dialog frame.border": "#536DFE",
            "dialog.body": "bg:#1E293B #E2E8F0",
            "dialog shadow": "bg:#020617",
            "button": "bg:#1E293B #CBD5E1",
            "button.focused": "bg:#536DFE #FFFFFF bold",
            "radio-list": "bg:#1E293B #E2E8F0",
            "radio-selected": "bold #38BDF8",
            "radio-checked": "bold #38BDF8",
            "radio": "#94A3B8",
        })

        try:
            self.session = PromptSession(
                completer=completer,
                complete_while_typing=True,
                style=pt_style,
            )
        except Exception:
            from prompt_toolkit.output import DummyOutput

            self.session = PromptSession(
                completer=completer,
                complete_while_typing=True,
                style=pt_style,
                output=DummyOutput(),
            )

    def _sync_cleanup(self):
        try:
            self.tools.vds_pool.close_all()
        except Exception:
            pass
        try:
            if hasattr(self.tools, "_pty_manager"):
                self.tools._pty_manager.close_all()
        except Exception:
            pass

    def _build_prompt(self) -> FormattedText:
        parts = []
        if self.mode == "think":
            parts.append(("class:mode-think", "[think] "))
        elif self.mode == "plan":
            parts.append(("class:mode-plan", "[plan] "))
        parts.append(("class:prompt", "› "))
        return FormattedText(parts)

    async def _check_startup_updates(self, force_refresh: bool = False) -> None:
        try:
            self.update_info = await asyncio.wait_for(
                asyncio.to_thread(check_for_updates, force_refresh, 1.4),
                timeout=1.6,
            )
        except Exception:
            pass

    def refresh_ui(self, status_message: str | None = None):
        console.clear()
        render_banner(
            self.mode,
            self.agent_style,
            self.think,
            self.search,
            status_message=status_message,
            cwd=self.tools.cwd,
            update_info=self.update_info,
        )
        console.print()

    def restart_in_windows_terminal(self):
        launch_args = [
            sys.executable,
            os.path.join(APP_DIR, "deepx", "deep_cli.py"),
            "--state",
            self.state_file,
        ]
        if not self.headless:
            launch_args.append("--headful")
        inner_cmdline = subprocess.list2cmdline(launch_args)
        command = [
            "wt.exe",
            "-w",
            "new",
            "--size",
            "110,30",
            "new-tab",
            "--title",
            "DEEPX AGENT",
            "-d",
            APP_DIR,
            "cmd.exe",
            "/d",
            "/s",
            "/c",
            f'"{inner_cmdline}"',
        ]
        subprocess.Popen(
            command,
            cwd=APP_DIR,
            close_fds=True,
        )

    @property
    def allowed_tools(self):
        return STYLE_CONFIGS[self.agent_style]["tools"]

    def _apply_style_guard(self):
        self.tools.protect_self = STYLE_CONFIGS[self.agent_style].get("protect_self", False)

    def _sync_mode_flags(self, mode_name: str, sync_think: bool = True):
        normalized = _normalize_mode_name(mode_name) or "instant"
        self.mode = normalized
        self.tools.plan_mode = normalized == "plan"
        if sync_think:
            self.think = normalized in ("think", "plan")

    def _collect_repo_context(self) -> str:
        if getattr(self.tools, "protect_self", False) and self.tools.is_protected(self.tools.cwd):
            return ""
        return build_zero_turn_context(self.tools.cwd)

    async def switch_mode(self, target_mode: str, api: Optional[DeepAPI] = None) -> bool:
        normalized = _normalize_mode_name(target_mode)
        if not normalized:
            return False
        previous_mode = self.mode
        self._sync_mode_flags(normalized, sync_think=True)

        if api is not None:
            try:
                await api.set_mode(self.mode)
                await api.set_deepthink(self.think)
            except Exception:
                pass

        if normalized == "plan":
            self._mode_change_notice = (
                "[СИСТЕМА: Режим изменён на PLAN. Запись файлов и выполнение изменяющих команд заблокированы "
                "до переключения в /mode think или /mode instant.]"
            )
        elif previous_mode == "plan":
            self._mode_change_notice = (
                f"[СИСТЕМА: Режим изменён на {normalized.upper()}. Запись файлов и выполнение команд снова разрешены.]"
            )
        elif normalized != previous_mode:
            self._mode_change_notice = f"[СИСТЕМА: Активный режим — {normalized.upper()}.]"

        think_lbl = "ON" if self.think else "OFF"
        plan_note = " (read-only planning)" if normalized == "plan" else ""
        console.print(
            f"[bold #38BDF8]Mode: {normalized.upper()}{plan_note} | Think: {think_lbl}[/bold #38BDF8]"
        )
        return True

    async def switch_style(self, target_style: str, api: DeepAPI):
        target_style = normalize_style_name(target_style)
        if not target_style:
            return False
        if target_style == self.agent_style:
            console.print(
                f"[dim #64748B]Style {STYLE_CONFIGS[target_style]['label']} is already active.[/dim #64748B]"
            )
            return True

        self.agent_style = target_style
        self._apply_style_guard()
        if target_style == "osinter":
            self.search = True
        self.turn_history = []
        self._compacted_seed_pending = ""
        self._pending_workspace_context = ""
        await api.new_chat()
        self.is_new_chat = True
        self.refresh_ui()
        config = STYLE_CONFIGS[target_style]
        console.print(
            f"[bold #38BDF8]Style set to {config['label']} in a fresh session.[/bold #38BDF8]"
        )
        if config.get("description"):
            console.print(f"[dim #94A3B8]{config['description']}[/dim #94A3B8]")
        return True

    def build_compact_seed(self) -> tuple[str, int, int]:
        repo_context = self._collect_repo_context()
        system_prompt = build_agent_system_prompt(
            self.agent_style,
            self.think,
            self.tools.cwd,
            repo_context=repo_context,
            plan_mode=self.tools.plan_mode,
        )
        return build_compacted_session_seed(
            system_prompt,
            self.turn_history,
            todos=self.tools.todos,
            keep_recent=RECENT_STEPS_FULL,
        )

    async def compact_history(self, api: Optional[DeepAPI] = None) -> tuple[int, int]:
        compacted, folded_count, saved_chars = compact_conversation_history(
            self.turn_history,
            keep_recent=RECENT_STEPS_FULL,
            fold_threshold=800,
        )
        self.turn_history = compacted
        seed, extra_folded, extra_saved = self.build_compact_seed()
        total_folded = max(folded_count, extra_folded)
        total_saved = max(saved_chars, extra_saved)
        self._compacted_seed_pending = seed
        self.is_new_chat = False

        if api is not None:
            try:
                await api.new_chat()
            except Exception:
                pass
        return total_folded, total_saved

    def _remove_state_file(self) -> None:
        try:
            if self.state_file and os.path.exists(self.state_file):
                os.remove(self.state_file)
        except Exception:
            pass

    async def _authenticate_interactively(self) -> bool:
        """Run interactive browser login and return True as soon as session state is saved."""
        while not os.path.isfile(self.state_file):
            self.refresh_ui(
                "Авторизуйтесь либо создайте новый аккаунт в DeepSeek."
            )
            console.print(
                Align.center(
                    Text(
                        "CLI ожидает завершения авторизации в открывшемся браузере...",
                        style="#94A3B8",
                    )
                )
            )
            try:
                auth_api = DeepAPI(state_file=self.state_file, headless=False)
                await auth_api.wait_for_login_and_save()
                if os.path.isfile(self.state_file):
                    return True
            except DeepSeekAccountBannedError as ban_err:
                self._remove_state_file()
                self.refresh_ui("Учётная запись DeepSeek заблокирована.")
                render_account_ban_panel(
                    ban_until=ban_err.ban_until,
                    account=ban_err.account,
                    raw_message=ban_err.raw_message,
                )
                retry = await _run_in_daemon_thread(
                    lambda: self._confirm_fn("Открыть браузер для входа в другой аккаунт DeepSeek?")
                )
                if not retry:
                    return False
                continue
            except Exception as e:
                if os.path.isfile(self.state_file):
                    return True
                console.print(
                    f"\nОшибка авторизации [{type(e).__name__}]: {e}",
                    style="bold red",
                    markup=False,
                    highlight=False,
                )
                retry = await _run_in_daemon_thread(
                    lambda: self._confirm_fn("Повторить авторизацию в браузере?")
                )
                if not retry:
                    return False
                continue
        return True

    async def run(self):
        await self._check_startup_updates(force_refresh=False)

        try:
            while not self._exit_requested:
                just_authenticated = False
                if not os.path.isfile(self.state_file):
                    ok = await self._authenticate_interactively()
                    if not ok:
                        return
                    just_authenticated = True

                self.refresh_ui()
                if just_authenticated:
                    console.print(
                        Align.center(
                            Text(
                                "[+] Авторизация подтверждена. Подключаю сессию в этом же окне...",
                                style="bold #10B981",
                            )
                        )
                    )

                try:
                    async with DeepAPI(state_file=self.state_file, headless=self.headless) as api:
                        if just_authenticated:
                            self.refresh_ui()
                            console.print(
                                "[bold #10B981][+] Вход выполнен. Сессия DeepSeek активна — можно сразу писать запрос.[/bold #10B981]\n"
                            )

                        while True:
                            disable_quick_edit_mode()
                            prompt_msg = self._build_prompt()
                            try:
                                user_input = await _run_in_daemon_thread(
                                    lambda: self.session.prompt(prompt_msg)
                                )
                                user_input = user_input.strip()
                            except KeyboardInterrupt:
                                if await self.confirm_exit():
                                    self._exit_requested = True
                                    console.print("\n[bold #536DFE]Exiting DEEPX.[/bold #536DFE]")
                                    break
                                continue
                            except EOFError:
                                self._exit_requested = True
                                console.print("\n[bold #536DFE]Exiting DEEPX.[/bold #536DFE]")
                                break

                            if not user_input:
                                continue

                            if user_input.startswith("/"):
                                if await self.handle_command(user_input, api):
                                    continue

                            await self.run_query_interruptible(user_input, api)
                            if self._exit_requested:
                                console.print("\n[bold #536DFE]Exiting DEEPX.[/bold #536DFE]")
                                break
                    break

                except DeepSeekAccountBannedError as ban_err:
                    self._remove_state_file()
                    self.refresh_ui("Учётная запись DeepSeek заблокирована.")
                    render_account_ban_panel(
                        ban_until=ban_err.ban_until,
                        account=ban_err.account,
                        raw_message=ban_err.raw_message,
                    )
                    retry = await _run_in_daemon_thread(
                        lambda: self._confirm_fn("Открыть браузер для входа в другой аккаунт DeepSeek?")
                    )
                    if not retry:
                        break
                    continue

                except DeepSeekAuthRequiredError:
                    self._remove_state_file()
                    console.print(
                        "\n[bold #FBBF24][!] Сохраненная сессия DeepSeek истекла. Открываю окно входа...[/bold #FBBF24]"
                    )
                    continue

        except Exception as e:
            message = str(e).replace("\n", " ")
            if len(message) > 500:
                message = message[:500] + f"... (+{len(str(e)) - 500} chars)"
            console.print(
                f"\nSystem Error [{type(e).__name__}]: {message}",
                style="bold red",
                markup=False,
                highlight=False,
            )
        finally:
            if self._active_status is not None:
                try:
                    await asyncio.wait_for(self._active_status.stop(), timeout=1.0)
                except Exception:
                    pass
                self._active_status = None
            try:
                await asyncio.wait_for(self.tools.close_background_tasks(), timeout=2.0)
            except Exception:
                pass
            try:
                await asyncio.wait_for(self.tools.close_browser(), timeout=2.5)
            except Exception:
                pass
            try:
                self.tools.vds_pool.close_all()
            except Exception:
                pass

    async def confirm_exit(self) -> bool:
        try:
            disable_quick_edit_mode()
            answer = await _run_in_daemon_thread(
                lambda: self.session.prompt("Do you really want to exit? [y/N] "),
            )
        except (EOFError, KeyboardInterrupt):
            return False
        return answer.strip().lower() in ("y", "yes")

    async def run_query_interruptible(self, user_input: str, api: DeepAPI) -> bool:
        loop = asyncio.get_running_loop()
        interrupt_event = asyncio.Event()
        previous_sigint = signal.getsignal(signal.SIGINT)
        previous_exception_handler = loop.get_exception_handler()
        windows_console_state = _begin_windows_ctrl_c_key_mode()
        interrupted = False
        exit_requested_by_key = False
        self._exit_requested = False

        def cancellation_exception_handler(current_loop, context):
            exc = context.get("exception")
            if isinstance(exc, asyncio.CancelledError):
                return
            if previous_exception_handler is not None:
                previous_exception_handler(current_loop, context)
            else:
                current_loop.default_exception_handler(context)

        def request_stop(signum=None, frame=None):
            loop.call_soon_threadsafe(interrupt_event.set)

        signal.signal(signal.SIGINT, request_stop)
        query_task = asyncio.create_task(self.process_query(user_input, api))
        interrupt_task = asyncio.create_task(interrupt_event.wait())
        key_task = (
            asyncio.create_task(_wait_for_windows_control_key())
            if windows_console_state
            else None
        )

        try:
            while not query_task.done():
                waiters = {query_task, interrupt_task}
                if key_task is not None and not key_task.done():
                    waiters.add(key_task)
                done, _ = await asyncio.wait(
                    waiters,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if query_task in done:
                    await query_task
                    return True

                stop_key = None
                if interrupt_task in done:
                    stop_key = "ctrl_c"
                elif key_task is not None and key_task in done:
                    try:
                        stop_key = key_task.result()
                    except Exception:
                        stop_key = None

                if stop_key:
                    exit_requested_by_key = stop_key in ("exit", "ctrl_c")
                    break
                if windows_console_state and key_task is not None and key_task in done:
                    key_task = asyncio.create_task(_wait_for_windows_control_key())
                if interrupt_task in done:
                    interrupt_event = asyncio.Event()
                    interrupt_task = asyncio.create_task(interrupt_event.wait())
                    signal.signal(signal.SIGINT, request_stop)

            interrupted = True
            self.tools.todos = []
            self.tools._todo_dirty = False
            self.tools._todo_rendered_signature = None
            loop.set_exception_handler(cancellation_exception_handler)
            if self._active_status is not None:
                try:
                    await self._active_status.stop()
                except Exception:
                    pass
                self._active_status = None
            stopped = False
            try:
                stopped = await asyncio.wait_for(
                    asyncio.shield(api.stop_generation()),
                    timeout=6.0,
                )
            except Exception:
                stopped = False

            if not query_task.done():
                await asyncio.sleep(0.1)
                query_task.cancel()
            try:
                await query_task
            except asyncio.CancelledError:
                pass

            sys.stdout.write("\033[0m\r\033[K")
            sys.stdout.flush()
            if stopped:
                console.print(
                    "\n[bold #F59E0B]Генерация остановлена. Можно отправить новый запрос в этот же чат.[/bold #F59E0B]"
                )
            else:
                console.print(
                    "\n[bold #F59E0B]Ход агента отменён.[/bold #F59E0B]"
                )
        finally:
            if self._active_status is not None:
                try:
                    await self._active_status.stop()
                except Exception:
                    pass
                self._active_status = None
            for task in (interrupt_task, key_task):
                if task is not None and not task.done():
                    task.cancel()
                    try:
                        await task
                    except (asyncio.CancelledError, Exception):
                        pass
            if not query_task.done():
                query_task.cancel()
                try:
                    await query_task
                except (asyncio.CancelledError, Exception):
                    pass
            loop.set_exception_handler(previous_exception_handler)
            _restore_windows_console_mode(windows_console_state)
            signal.signal(signal.SIGINT, previous_sigint)

        if interrupted and exit_requested_by_key:
            if await self.confirm_exit():
                self._exit_requested = True
        return False

    async def handle_command(self, cmd: str, api: DeepAPI) -> bool:
        parts = cmd.split()
        main_cmd = parts[0].lower()

        if main_cmd in ["/exit", "/quit"]:
            console.print("[bold #536DFE]Exiting DEEPX.[/bold #536DFE]")
            raise SystemExit(0)

        elif main_cmd == "/help":
            print_help()
            return True

        elif main_cmd == "/clear":
            self.refresh_ui()
            return True

        elif main_cmd == "/status":
            print_status(
                self.mode,
                self.agent_style,
                self.think,
                self.search,
                self.tools.cwd,
                self.state_file,
                update_info=self.update_info,
            )
            return True

        elif main_cmd == "/update":
            arg_tokens = [tok.lower() for tok in parts[1:]]
            force = "--force" in arg_tokens or "force" in arg_tokens
            check_only = "check" in arg_tokens
            status_ind = SingleLineStatus()
            await status_ind.start("Проверяю обновления в GitHub...")
            try:
                info = await asyncio.to_thread(check_for_updates, True, 5.0)
                self.update_info = info
                if check_only:
                    await status_ind.stop()
                    if info.error:
                        console.print(
                            f"Не удалось проверить обновления: {info.error}",
                            style="bold #FBBF24",
                            markup=False,
                            highlight=False,
                        )
                    elif info.has_update:
                        console.print(
                            f"Доступно обновление: update to {info.latest_version} (текущая v{info.current_version}). Запустите /update",
                            style="bold #FBBF24",
                            markup=False,
                            highlight=False,
                        )
                    else:
                        console.print(
                            f"Установлена актуальная версия v{info.current_version}.",
                            style="bold #10B981",
                            markup=False,
                            highlight=False,
                        )
                    return True

                if info.error and not force:
                    await status_ind.stop()
                    console.print(
                        f"Не удалось проверить обновления: {info.error}",
                        style="bold #FBBF24",
                        markup=False,
                        highlight=False,
                    )
                    return True

                if not info.has_update and not force:
                    await status_ind.stop()
                    console.print(
                        f"Установлена актуальная версия v{info.current_version}. Для принудительной переустановки используйте /update --force",
                        style="bold #10B981",
                        markup=False,
                        highlight=False,
                    )
                    return True

                status_ind.update(f"Обновляю DEEPX CLI до {info.latest_version}...")
                ok, msg = await asyncio.to_thread(perform_self_update, force=force)
                if ok:
                    self.update_info = await asyncio.to_thread(check_for_updates, True, 3.0)
            finally:
                await status_ind.stop()

            console.print(
                msg,
                style="bold #10B981" if ok else "bold red",
                markup=False,
                highlight=False,
            )
            return True

        elif main_cmd == "/stealth":
            report = await self.tools.browser_stealth_report()
            signals = report["signals"]
            table = Table(
                title="PLAYWRIGHT STEALTH CHECK",
                border_style="#536DFE",
                header_style="bold #536DFE",
                box=box.ROUNDED,
            )
            table.add_column("Check", style="bold #A78BFA")
            table.add_column("Value")
            table.add_row("Package", f"playwright-stealth {report['package_version']}")
            table.add_row("Integration", report["status"])
            table.add_row("Basic result", report["basic_check"].upper())
            table.add_row("navigator.webdriver", repr(signals.get("webdriver")))
            table.add_row("User-Agent", str(signals.get("userAgent", "")))
            table.add_row("Languages", ", ".join(signals.get("languages", [])))
            table.add_row("Plugins", str(signals.get("plugins", 0)))
            table.add_row("window.chrome", str(signals.get("chromeObject")))
            console.print(table)
            for warning in report["warnings"]:
                console.print(f"[bold #F59E0B]Warning:[/bold #F59E0B] {warning}")
            return True

        elif main_cmd in ["/new", "/reset"]:
            self.turn_history = []
            self._compacted_seed_pending = ""
            self._pending_workspace_context = ""
            self._mode_change_notice = ""
            await api.new_chat()
            self.is_new_chat = True
            self.refresh_ui()
            console.print("[bold #10B981]New session initialized.[/bold #10B981]")
            return True

        elif main_cmd == "/copy":
            if self.last_response:
                pyperclip.copy(self.last_response)
                console.print("[bold #10B981]Response copied to clipboard.[/bold #10B981]")
            else:
                console.print("[dim #F59E0B]No response content to copy.[/dim #F59E0B]")
            return True

        elif main_cmd == "/cd":
            raw_arg = cmd[len(parts[0]):].strip().strip('"').strip("'")
            if not raw_arg:
                console.print(f"[dim]Текущая папка: {self.tools.cwd}[/dim]")
                return True
            target_dir = os.path.abspath(os.path.join(self.tools.cwd, raw_arg))
            if self.tools.is_protected(target_dir):
                console.print("[bold red]Доступ к служебной папке DEEPX запрещён.[/bold red]")
                return True
            if not os.path.isdir(target_dir):
                console.print(f"Папка не найдена: {target_dir}", style="bold red", markup=False, highlight=False)
                return True
            self.tools.set_workspace(target_dir)
            self._pending_workspace_context = self._collect_repo_context()
            console.print(f"Рабочая папка: {self.tools.cwd}", style="bold #38BDF8", markup=False, highlight=False)
            return True

        elif main_cmd == "/compact":
            folded, saved = await self.compact_history(api)
            console.print(
                f"[bold #10B981]Контекст сжат (свёрнуто выводов: {folded}, освобождено ~{saved} симв.).[/bold #10B981]"
            )
            return True

        elif main_cmd == "/undo":
            ok, msg = self.tools.checkpoints.undo_last()
            style = "bold #10B981" if ok else "bold #F59E0B"
            console.print(msg, style=style, markup=False, highlight=False)
            return True

        elif main_cmd == "/menu":
            await self.open_interactive_menu(api)
            return True

        elif main_cmd == "/style":
            if len(parts) > 1 and parts[1].lower() == "list":
                table = Table(
                    title="AGENT STYLES",
                    border_style="#536DFE",
                    header_style="bold #536DFE",
                    box=box.ROUNDED,
                )
                table.add_column("Style", style="bold #A78BFA")
                table.add_column("Purpose")
                table.add_column("Tools", justify="right")
                for name, config in STYLE_CONFIGS.items():
                    marker = " *" if name == self.agent_style else ""
                    table.add_row(
                        f"{name}{marker}",
                        config.get("description", ""),
                        str(len(config["tools"])),
                    )
                console.print(table)
                console.print("[dim]Switch with /style coder, /style universal or /style osinter[/dim]")
                return True

            target_style = normalize_style_name(parts[1]) if len(parts) > 1 else None
            if len(parts) > 1 and not target_style:
                console.print(
                    "[bold red]Unknown style. Use coder, universal or osinter.[/bold red]"
                )
                return True
            if not target_style:
                target_style = await radiolist_dialog(
                    title="Agent Style Selection",
                    text="Select a specialized prompt and toolset (creates a fresh session):",
                    values=[
                        ("coder", "Coder - development, Python and browser automation"),
                        ("universal", "Universal - writing, analytics & documents"),
                        ("osinter", "OSINTer - DuckDuckGo recon, verification, dossiers"),
                    ],
                    style=self._dialog_style,
                ).run_async()
            if target_style:
                await self.switch_style(target_style, api)
            return True

        elif main_cmd == "/mode":
            target_mode = None
            if len(parts) > 1:
                target_mode = _normalize_mode_name(parts[1])
                if not target_mode:
                    console.print(
                        "[bold red]Unknown mode. Use instant, think or plan.[/bold red]"
                    )
                    return True
            else:
                target_mode = await radiolist_dialog(
                    title="Mode Selection",
                    text="Select agent mode (preserves conversation history):",
                    values=[
                        ("instant", "Instant - Fast response (DeepThink OFF)"),
                        ("think", "Think - DeepThink reasoning (ON)"),
                        ("plan", "Plan - DeepThink ON + read-only planning"),
                    ],
                    style=self._dialog_style,
                ).run_async()

            if target_mode:
                await self.switch_mode(target_mode, api)
            return True

        elif main_cmd == "/think":
            if len(parts) > 1:
                self.think = parts[1].lower() in ("on", "true", "1")
            else:
                self.think = not self.think
            if self.mode != "plan":
                self._sync_mode_flags("think" if self.think else "instant", sync_think=False)
            await api.set_deepthink(self.think)
            status_str = "ON" if self.think else "OFF"
            console.print(f"[bold #38BDF8]Think: {status_str}[/bold #38BDF8]")
            return True

        elif main_cmd == "/search":
            if len(parts) > 1:
                self.search = parts[1].lower() in ("on", "true", "1")
            else:
                self.search = not self.search
            await api.set_search(self.search)
            status_str = "ON" if self.search else "OFF"
            console.print(f"[bold #38BDF8]Search: {status_str}[/bold #38BDF8]")
            return True

        else:
            console.print(f"[bold red]Unknown command: {cmd}. Type /help for command list.[/bold red]")
            return True

    async def open_interactive_menu(self, api: DeepAPI):
        option = await radiolist_dialog(
            title="DEEPX Settings Menu",
            text="Use Arrow Keys and press Enter to select setting:",
            values=[
                ("mode", f"Change Mode (Current: {self.mode.upper()})"),
                ("style", f"Change Style -> New Chat (Current: {self.agent_style.upper()})"),
                ("think", f"Toggle DeepThink (Current: {'ON' if self.think else 'OFF'})"),
                ("search", f"Toggle Web Search (Current: {'ON' if self.search else 'OFF'})"),
                ("compact", "Compact Conversation History"),
                ("undo", "Undo Last File Turn"),
                ("update", "Check & Install Updates from GitHub"),
                ("new", "Reset Session Context"),
            ],
            style=self._dialog_style,
        ).run_async()

        if option == "mode":
            mode_choice = await radiolist_dialog(
                title="Select Mode",
                text="Choose agent mode (preserves conversation):",
                values=[
                    ("instant", "Instant (Fast, DeepThink OFF)"),
                    ("think", "Think (DeepThink ON)"),
                    ("plan", "Plan (Read-only planning, DeepThink ON)"),
                ],
                style=self._dialog_style,
            ).run_async()
            if mode_choice:
                await self.switch_mode(mode_choice, api)
        elif option == "style":
            style_choice = await radiolist_dialog(
                title="Select Agent Style",
                text="Choose a specialized prompt and toolset:",
                values=[
                    ("coder", "Coder"),
                    ("universal", "Universal"),
                    ("osinter", "OSINTer"),
                ],
                style=self._dialog_style,
            ).run_async()
            if style_choice:
                await self.switch_style(style_choice, api)
        elif option == "think":
            await self.handle_command("/think", api)
        elif option == "search":
            await self.handle_command("/search", api)
        elif option == "compact":
            await self.handle_command("/compact", api)
        elif option == "undo":
            await self.handle_command("/undo", api)
        elif option == "update":
            await self.handle_command("/update", api)
        elif option == "new":
            await self.handle_command("/new", api)

    async def _execute_one_tool_call(
        self,
        call: dict,
        status: Optional[SingleLineStatus] = None,
        update_status: bool = True,
    ) -> str:
        tool_name = call.get("tool")
        tool_args = call.get("args", {})
        if update_status and status is not None and tool_name != "todo":
            status.update(describe_tool_action(tool_name, tool_args))

        danger_reason = None
        if not getattr(self.tools, "plan_mode", False):
            danger_reason = classify_dangerous_operation(tool_name, tool_args, self.tools.cwd)
        if danger_reason:
            if status is not None:
                status.clear()
            confirmed = await asyncio.to_thread(self._confirm_fn, danger_reason)
            if not confirmed:
                return f"[TOOL RESULT for '{tool_name}']:\n[Cancelled by user: action rejected at confirmation prompt]"
            if status is not None:
                status.update(describe_tool_action(tool_name, tool_args))

        try:
            result = await self.tools.execute_tool(
                tool_name,
                tool_args,
                allowed_tools=self.allowed_tools,
            )
        except Exception as error:
            result = f"[Error executing tool '{tool_name}': {type(error).__name__}: {error}]"
        clean_result = sanitize_tool_result(result)
        if _tool_result_failed(clean_result):
            if status is not None:
                status.clear()
            err_msg = _summarize_tool_error(clean_result)
            console.print(f"Ошибка ({tool_name}): {err_msg}", style="bold red", markup=False, highlight=False)
        return f"[TOOL RESULT for '{tool_name}']:\n{clean_result}"

    async def _execute_tool_calls(
        self,
        tool_calls: list,
        status: Optional[SingleLineStatus] = None,
    ):
        outputs = []
        executed_count = 0
        index = 0

        while index < len(tool_calls):
            call = tool_calls[index]
            tool_name = call.get("tool")
            if tool_name in PARALLEL_READ_ONLY_TOOLS:
                end = index + 1
                while (
                    end < len(tool_calls)
                    and tool_calls[end].get("tool") in PARALLEL_READ_ONLY_TOOLS
                ):
                    end += 1
                batch = tool_calls[index:end]
                if status is not None:
                    if len(batch) > 1:
                        status.update(f"{describe_tool_action(batch[0].get('tool'), batch[0].get('args'))} (+{len(batch) - 1})")
                    else:
                        status.update(describe_tool_action(batch[0].get("tool"), batch[0].get("args")))
                if status is not None and self.tools._todo_dirty:
                    status.clear()
                self.tools.flush_todos()
                batch_outputs = await asyncio.gather(
                    *(
                        self._execute_one_tool_call(
                            batch_call,
                            status=status,
                            update_status=(len(batch) == 1),
                        )
                        for batch_call in batch
                    )
                )
                outputs.extend(batch_outputs)
                executed_count += len(batch)
                index = end
                continue

            if status is not None and self.tools._todo_dirty:
                status.clear()
            if tool_name != "todo":
                self.tools.flush_todos()
            outputs.append(await self._execute_one_tool_call(call, status=status, update_status=True))
            if tool_name != "todo":
                executed_count += 1
            index += 1

        if status is not None and self.tools._todo_dirty:
            status.clear()
        self.tools.flush_todos()
        return outputs, executed_count

    async def process_query(self, user_input: str, api: DeepAPI):
        original_goal = user_input
        failure_counts = {}
        pending_verification = False
        strategy_change_required = False
        verification_nudges = 0
        current_prompt = user_input

        is_first_message_of_chat = self.is_new_chat
        prefix_blocks = []
        if is_first_message_of_chat:
            repo_context = self._collect_repo_context()
            system_prompt = build_agent_system_prompt(
                self.agent_style,
                self.think,
                self.tools.cwd,
                repo_context=repo_context,
                plan_mode=self.tools.plan_mode,
            )
            prefix_blocks.append(system_prompt)
            self._pending_workspace_context = ""
            self._mode_change_notice = ""
            self._compacted_seed_pending = ""
        else:
            if self._compacted_seed_pending:
                prefix_blocks.append(self._compacted_seed_pending)
            if self._pending_workspace_context:
                prefix_blocks.append(
                    f"[СМЕНА РАБОЧЕЙ ДИРЕКТОРИИ]:\n{self.tools.cwd}\n\n{self._pending_workspace_context}"
                )
            if self._mode_change_notice:
                prefix_blocks.append(self._mode_change_notice)

        if prefix_blocks:
            current_prompt = "\n\n".join(prefix_blocks) + f"\n\n[ПОЛЬЗОВАТЕЛЬСКИЙ ЗАПРОС]:\n{user_input}"

        await api.set_mode(self.mode)
        await api.set_search(self.search)
        await api.set_deepthink(self.think)

        loop_count = 0
        did_execute_tool = False
        executed_tool_count = 0
        todo_nudged = False
        empty_responses = 0
        turn_tool_outputs = []

        self.tools.todos = []
        self.tools._todo_dirty = False
        self.tools._todo_rendered_signature = None

        self.tools.checkpoints.begin_turn(label=user_input[:80])
        status = SingleLineStatus()
        self._active_status = status

        try:
            while True:
                loop_count += 1
                status.start("Думаю..." if self.think else "Обрабатываю запрос...")

                try:
                    raw_stream = api.send_message(current_prompt, stream=True)
                    stream_gen = await raw_stream if inspect.isawaitable(raw_stream) else raw_stream
                    if is_first_message_of_chat:
                        self.is_new_chat = False
                        is_first_message_of_chat = False
                    if loop_count == 1:
                        self._compacted_seed_pending = ""
                        self._pending_workspace_context = ""
                        self._mode_change_notice = ""
                except DeepSeekAccountBannedError:
                    status.clear()
                    raise
                except Exception as send_error:
                    status.clear()
                    empty_responses += 1
                    message = str(send_error).replace("\n", " ")[:200]
                    console.print(
                        f"\nЗапрос не ушёл ({type(send_error).__name__}): {message}",
                        style="bold #F59E0B",
                        markup=False,
                        highlight=False,
                    )
                    if empty_responses > MAX_EMPTY_RESPONSE_RETRIES:
                        console.print("[bold red]Повторы исчерпаны. Останавливаюсь.[/bold red]")
                        break
                    await asyncio.sleep(2 * empty_responses)
                    continue

                printed_answer = ""
                answer_started = False
                has_printed_text_this_turn = False
                final_think = ""
                final_answer = ""
                stream_renderer = StreamingMarkupRenderer()
                stream_writer = AdaptiveStreamWriter()
                drain_task = asyncio.create_task(stream_writer.drain())

                try:
                    async for chunk in stream_gen:
                        if not isinstance(chunk, dict):
                            continue

                        final_think = chunk.get("think", "")
                        final_answer = chunk.get("answer", "")

                        if final_think and not answer_started:
                            tok_count = count_tokens(final_think)
                            status.update(f"Думаю ({tok_count} т)...")

                        if final_answer:
                            answer_started = True
                            clean_source = get_clean_text(final_answer)
                            new_chars = stream_renderer.update(clean_source)
                            if new_chars:
                                status.clear()
                                if not has_printed_text_this_turn:
                                    if loop_count > 1 and did_execute_tool:
                                        sys.stdout.write("\n")
                                    has_printed_text_this_turn = True
                                stream_writer.push(new_chars)
                            elif not has_printed_text_this_turn and "tool" in final_answer:
                                status.update("Подготавливаю действие...")

                    if final_answer:
                        clean_final = get_clean_text(final_answer)
                        remaining_delta = stream_renderer.update(clean_final)
                        if remaining_delta:
                            status.clear()
                            has_printed_text_this_turn = True
                            stream_writer.push(remaining_delta)
                        flush_tail = stream_renderer.finish()
                        if flush_tail:
                            status.clear()
                            has_printed_text_this_turn = True
                            stream_writer.push(flush_tail)

                    await stream_writer.finish()
                    await drain_task
                finally:
                    if not drain_task.done():
                        drain_task.cancel()
                        try:
                            await drain_task
                        except (asyncio.CancelledError, Exception):
                            pass

                printed_answer = stream_renderer.rendered_text
                if printed_answer:
                    nl_count = len(printed_answer) - len(printed_answer.rstrip("\n"))
                    if nl_count == 0:
                        console.print("\n")
                    elif nl_count == 1:
                        console.print()

                final_answer = final_answer.strip()
                final_think = final_think.strip()

                if not final_answer:
                    status.clear()
                    if final_think:
                        console.print(
                            "\n[bold #F59E0B]Ответ оборван: модель начала размышлять, но текста ответа нет.[/bold #F59E0B]"
                        )
                        break

                    empty_responses += 1
                    if empty_responses > MAX_EMPTY_RESPONSE_RETRIES:
                        console.print(
                            f"\n[bold red]Пустой ответ {empty_responses} раз(а) подряд. Останавливаюсь.[/bold red]"
                        )
                        break

                    delay = min(2 * empty_responses, 10)
                    console.print(
                        f"\n[bold #F59E0B]Пустой ответ от API (попытка {empty_responses} из "
                        f"{MAX_EMPTY_RESPONSE_RETRIES}). Повтор через {delay} с...[/bold #F59E0B]"
                    )
                    await asyncio.sleep(delay)
                    continue

                empty_responses = 0

                clean_answer = get_clean_text(final_answer)
                if clean_answer:
                    self.last_response = clean_answer
                elif final_think:
                    self.last_response = get_clean_text(final_think)

                tool_calls = extract_tool_calls(final_answer)
                if tool_calls:
                    did_execute_tool = True
                    tool_outputs, current_executed_count = await self._execute_tool_calls(
                        tool_calls,
                        status=status,
                    )
                    executed_tool_count += current_executed_count
                    turn_tool_outputs.extend(tool_outputs)

                    batch_any_failed = False
                    batch_repeated_failure = False
                    last_mutation_index = -1

                    for call_index, (call, output) in enumerate(zip(tool_calls, tool_outputs)):
                        tool_name = str(call.get("tool", "unknown"))
                        if _tool_result_failed(output):
                            batch_any_failed = True
                            failure_key = (
                                tool_name,
                                json.dumps(
                                    call.get("args", {}),
                                    ensure_ascii=False,
                                    sort_keys=True,
                                    default=str,
                                ),
                            )
                            failure_counts[failure_key] = failure_counts.get(failure_key, 0) + 1
                            if failure_counts[failure_key] >= 2:
                                batch_repeated_failure = True

                        if tool_name in MUTATING_TOOLS_REQUIRING_VERIFICATION:
                            last_mutation_index = call_index

                    if batch_repeated_failure:
                        strategy_change_required = True
                    elif not batch_any_failed:
                        strategy_change_required = False

                    if last_mutation_index >= 0:
                        pending_verification = not any(
                            str(call.get("tool", "")) in VERIFICATION_TOOLS
                            and call_index > last_mutation_index
                            and not _tool_result_failed(tool_outputs[call_index])
                            for call_index, call in enumerate(tool_calls)
                        )
                    elif pending_verification:
                        pending_verification = not any(
                            str(call.get("tool", "")) in VERIFICATION_TOOLS
                            and not _tool_result_failed(tool_outputs[call_index])
                            for call_index, call in enumerate(tool_calls)
                        )

                    feedback = "\n\n".join(tool_outputs)
                    if len(feedback) > MAX_TOOL_FEEDBACK_CHARS:
                        feedback = (
                            feedback[:MAX_TOOL_FEEDBACK_CHARS]
                            + f"\n\n[Truncated: tool output exceeded {MAX_TOOL_FEEDBACK_CHARS} chars. "
                            "Request the remaining part in a follow-up call.]"
                        )
                    if "todo" in self.allowed_tools and not todo_nudged:
                        if executed_tool_count >= TODO_NUDGE_AFTER_TOOLS and not self.tools.todos:
                            todo_nudged = True
                            feedback += (
                                "\n\n[СИСТЕМА]: задача оказалась многошаговой, а список задач не заведён. "
                                "Следующим действием вызови todo с action=set и распиши оставшиеся шаги, "
                                "затем продолжай работу, отмечая их по мере выполнения."
                            )
                        elif self.tools.todos and not any(
                            item["status"] == "active" for item in self.tools.todos
                        ) and any(item["status"] == "pending" for item in self.tools.todos):
                            todo_nudged = True
                            feedback += (
                                "\n\n[СИСТЕМА]: в списке задач нет ни одной активной. Отметь "
                                "выполненные через complete и переведи текущую в active."
                            )

                    interactive_prompt_detected, other_outputs = _extract_waiting_for_input(tool_outputs)
                    if interactive_prompt_detected:
                        session_id = interactive_prompt_detected.get("session_id", "unknown")
                        accumulated_output = interactive_prompt_detected.get(
                            "accumulated_output", ""
                        )
                        task_state = build_agent_task_state(
                            original_goal,
                            self.tools.todos,
                            pending_verification=pending_verification,
                            strategy_change_required=strategy_change_required,
                            include_goal=(loop_count % TASK_GOAL_REMINDER_INTERVAL == 0),
                        )
                        extra_results = (
                            "\n\n[ОСТАЛЬНЫЕ РЕЗУЛЬТАТЫ ИНСТРУМЕНТОВ]\n"
                            + "\n\n".join(other_outputs)
                            + "\n[КОНЕЦ ОСТАЛЬНЫХ РЕЗУЛЬТАТОВ]"
                            if other_outputs
                            else ""
                        )
                        current_prompt = (
                            task_state
                            + ("\n" if task_state else "")
                            + "[INTERACTIVE TERMINAL PROMPT DETECTED]\n"
                            f"Программа ожидает ввода в терминал (session_id=\"{session_id}\").\n"
                            "Текущий вывод терминала:\n"
                            "---\n"
                            f"{accumulated_output}\n"
                            "---\n"
                            "Проанализируй вопрос терминала и вызови инструмент `send_input` с нужным текстом "
                            "(обязательно заканчивай строку \\n, если требуется подтверждение Enter) или `kill_cmd`, "
                            "если процесс зациклен."
                            + extra_results
                        )
                        continue

                    task_state = build_agent_task_state(
                        original_goal,
                        self.tools.todos,
                        pending_verification=pending_verification,
                        strategy_change_required=strategy_change_required,
                        include_goal=(loop_count % TASK_GOAL_REMINDER_INTERVAL == 0),
                    )
                    current_prompt = (
                        task_state
                        + ("\n" if task_state else "")
                        + "[РЕЗУЛЬТАТЫ ИНСТРУМЕНТОВ]\n"
                        + feedback
                        + "\n[КОНЕЦ РЕЗУЛЬТАТОВ]\n\n"
                        "Продолжай исходную задачу. Если она подтверждённо выполнена — дай финальный ответ с кратким итогом. "
                        "Если задача НЕ завершена — СРАЗУ вызови следующий инструмент через ```tool_call в этом же сообщении. "
                        "Не пиши промежуточные обещания («сейчас проверю», «установлю») без одновременного вызова инструмента."
                    )
                    continue

                has_unfinished_todos = any(
                    item.get("status") in ("active", "pending")
                    for item in self.tools.todos
                )
                action_promise_re = re.compile(
                    r"(?:(?:сейчас|сначала|дальше|теперь|затем|пока|пробуем|пробую|попробуем|попробую|тестируем|тестирую|проверяем|проверяю|пытаемся|пытаюсь|отправляю|отправляем)\s+(?:проверю|проверить|установлю|установить|попробую|попробовать|выполню|выполнить|сделаю|сделать|запущу|запустить|подключусь|подключиться|посмотрю|посмотреть|отправлю|отправить|перейду|перейти|протестирую|протестировать|переполнение)|"
                    r"проверю\s+(?:доступные|наличие|работу|файлы|порты|версию|команду|менеджеры|пакеты)|"
                    r"следующим\s+(?:шагом|действием)|"
                    r"(?:i\s+will|let\s+me|going\s+to)\s+(?:now\s+)?(?:check|install|run|try|execute|verify|test|send|navigate))",
                    re.IGNORECASE,
                )
                has_action_promise = bool(action_promise_re.search(clean_answer or final_answer))
                tool_call_marker_re = re.compile(
                    r"(?:```\s*(?:tool_call|tool_calls|tools|tool|json)|<(?:tool_call|function_call|invoke)|(?:^|\n)\s*tool_call\s*\n\s*\{)",
                    re.IGNORECASE,
                )
                has_unparsed_tool_markup = bool(tool_call_marker_re.search(final_answer))

                if (
                    pending_verification
                    or has_unfinished_todos
                    or has_action_promise
                    or has_unparsed_tool_markup
                ) and verification_nudges < 3:
                    verification_nudges += 1
                    if has_unparsed_tool_markup:
                        nudge_reason = "Обнаружена попытка вызова инструмента, но синтаксис был некорректен. СРАЗУ вызови нужный инструмент в правильном формате ```tool_call."
                    elif has_action_promise:
                        nudge_reason = "Ты написал, что выполнишь действие, но не вызвал инструмент в блоке ```tool_call. СРАЗУ вызови нужный инструмент."
                    elif pending_verification:
                        nudge_reason = "Ты попытался завершить задачу до проверки изменённого артефакта. Следующим сообщением вызови релевантный инструмент проверки."
                    else:
                        nudge_reason = "В списке задач остались незавершённые шаги. Вызови следующий инструмент для продолжения."

                    current_prompt = (
                        build_agent_task_state(
                            original_goal,
                            self.tools.todos,
                            pending_verification=pending_verification,
                            strategy_change_required=strategy_change_required,
                            include_goal=(loop_count % TASK_GOAL_REMINDER_INTERVAL == 0),
                        )
                        + f"\n{nudge_reason} Не повторяй неподтверждённый финальный ответ и не пиши обещания без вызова ```tool_call."
                    )
                    continue

                self.turn_history.append({
                    "user": original_goal,
                    "assistant": clean_answer or final_answer,
                    "tool_outputs": turn_tool_outputs,
                })
                compacted_hist, _, _ = compact_conversation_history(
                    self.turn_history,
                    keep_recent=RECENT_STEPS_FULL,
                    fold_threshold=1200,
                )
                self.turn_history = compacted_hist

                approx_chars = sum(
                    len(str(t.get("user", "")))
                    + len(str(t.get("assistant", "")))
                    + sum(len(str(x)) for x in t.get("tool_outputs", []))
                    for t in self.turn_history
                )
                if approx_chars >= AUTO_COMPACT_CHAR_THRESHOLD and len(self.turn_history) > RECENT_STEPS_FULL:
                    await self.compact_history(api)
                break
        finally:
            self.tools.checkpoints.end_turn()
            await status.stop()
            if self._active_status is status:
                self._active_status = None
