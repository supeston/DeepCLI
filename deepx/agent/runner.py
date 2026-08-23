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
from deepx.parser.tool_parser import *
from deepx.ui.terminal import *
from deepx.ui.terminal import _begin_windows_ctrl_c_key_mode, _restore_windows_console_mode, _wait_for_windows_control_key
from deepx.ui.banner import *
from deepx.ui.streaming import *
from deepx.agent.prompts import *
from deepx.agent.prompts import _tool_result_failed
from deepx.agent.completer import *


class DeepCLIApp:
    def __init__(self, state_file: str = "state.json", headless: bool = True):
        self.state_file = state_file
        self.headless = headless
        self.mode = "instant"
        self.agent_style = "coder"
        self.think = False
        self.search = False
        self.tools = AgentTools(browser_headless=headless)
        self.tools.add_protected(state_file)
        self._apply_style_guard()
        self.last_response = ""
        self.is_new_chat = True
        self._active_file_live = None
        self._stream_file_activities = {}

        completer = SlashCommandCompleter(COMMANDS_DICT)
        pt_style = PTStyle.from_dict({
            'completion-menu.completion': 'bg:#172554 fg:#93C5FD',
            'completion-menu.completion.current': 'bg:#2563EB fg:#FFFFFF bold',
            'completion-menu.meta.completion': 'bg:#172554 fg:#60A5FA',
            'completion-menu.meta.completion.current': 'bg:#2563EB fg:#EFF6FF',
            'prompt': 'bold #536DFE',
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

    def refresh_ui(self, status_message: str | None = None):
                                                                                        
        console.clear()
        render_banner(
            self.mode,
            self.agent_style,
            self.think,
            self.search,
            status_message=status_message,
        )
        console.print()

    def restart_in_windows_terminal(self):
                                                                           
        command = [
            "wt.exe",
            "-w", "new",
            "--size", "110,30",
            "new-tab",
            "--title", "DEEPX AGENT",
            "-d", APP_DIR,
            "cmd.exe", "/d", "/c",
            sys.executable,
            os.path.join(APP_DIR, "deepx", "deep_cli.py"),
            "--state", self.state_file,
        ]
        if not self.headless:
            command.append("--headful")
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
        if target_style == "osinter" and self.mode != "expert":
            self.search = True
        await api.new_chat()
        self.is_new_chat = True
        self.refresh_ui()
        config = STYLE_CONFIGS[target_style]
        console.print(
            f"[bold #38BDF8]Agent style set to {config['label']} in a fresh session.[/bold #38BDF8]"
        )
        if config.get("description"):
            console.print(f"[dim #94A3B8]{config['description']}[/dim #94A3B8]")
        return True

    async def run(self):
                                                                           
                                                              
        if not os.path.isfile(self.state_file):
            self.refresh_ui(
                "Авторизуйтесь либо создайте новый аккаунт в DeepSeek."
            )
            console.print(
                Align.center(
                    Text(
                        "CLI ожидает завершения авторизации в открывшемся браузере…",
                        style="#94A3B8",
                    )
                )
            )
            try:
                auth_api = DeepAPI(state_file=self.state_file, headless=False)
                await auth_api.wait_for_login_and_save()
                console.print(
                    "\n[bold #38BDF8]Авторизация получена. "
                    "Перезапускаю DEEPX…[/bold #38BDF8]"
                )
                self.restart_in_windows_terminal()
            except Exception as e:
                console.print(
                    f"\nОшибка авторизации [{type(e).__name__}]: {e}",
                    style="bold red",
                    markup=False,
                    highlight=False,
                )
            return

        self.refresh_ui()

        try:
            async with DeepAPI(state_file=self.state_file, headless=self.headless) as api:
                while True:
                    prompt_str = "› "
                    try:
                        user_input = await asyncio.get_running_loop().run_in_executor(
                            None, lambda: self.session.prompt(prompt_str)
                        )
                        user_input = user_input.strip()
                    except KeyboardInterrupt:
                        if await self.confirm_exit():
                            console.print(
                                "\n[bold #8B5CF6]Exiting DEEPX. Goodbye![/bold #8B5CF6]"
                            )
                            break
                        continue
                    except EOFError:
                        console.print("\n[bold #8B5CF6]Exiting DEEPX. Goodbye![/bold #8B5CF6]")
                        break

                    if not user_input:
                        continue

                                           
                    if user_input.startswith("/"):
                        if await self.handle_command(user_input, api):
                            continue

                                        
                    await self.run_query_interruptible(user_input, api)

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
            await self.tools.close_background_tasks()
            await self.tools.close_browser()

    async def confirm_exit(self) -> bool:
        try:
            answer = await asyncio.get_running_loop().run_in_executor(
                None,
                lambda: self.session.prompt("Do you really want to exit? [y/N] "),
            )
        except (EOFError, KeyboardInterrupt):
            return False
        return answer.strip().lower() in ("y", "yes")

    async def run_query_interruptible(self, user_input: str, api: DeepAPI) -> bool:
        query_task = asyncio.create_task(self.process_query(user_input, api))
        loop = asyncio.get_running_loop()
        windows_console_state = _begin_windows_ctrl_c_key_mode()
        interrupt_event = None
        if windows_console_state:
            interrupt_task = asyncio.create_task(_wait_for_windows_control_key())
        else:
            interrupt_event = asyncio.Event()
            interrupt_task = asyncio.create_task(interrupt_event.wait())
        interrupted = False
        previous_sigint = signal.getsignal(signal.SIGINT)
        previous_exception_handler = loop.get_exception_handler()

        def cancellation_exception_handler(active_loop, context):
            if (
                interrupted
                and str(context.get("message", "")).startswith(
                    "socket.send() raised exception"
                )
            ):
                return
            if previous_exception_handler:
                previous_exception_handler(active_loop, context)
            else:
                active_loop.default_exception_handler(context)

        def request_stop(_signum, _frame):
            if query_task.done() or interrupt_event.is_set():
                return
            loop.call_soon_threadsafe(interrupt_event.set)

        if not windows_console_state:
            signal.signal(signal.SIGINT, request_stop)
        try:
            while True:
                done, _ = await asyncio.wait(
                    (query_task, interrupt_task),
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if query_task in done:
                    await query_task
                    return True

                action = (
                    interrupt_task.result()
                    if windows_console_state
                    else "exit"
                )
                if action != "exit":
                    break

                _restore_windows_console_mode(windows_console_state)
                windows_console_state = None
                if await self.confirm_exit():
                    interrupted = True
                    loop.set_exception_handler(cancellation_exception_handler)
                    try:
                        await asyncio.wait_for(
                            asyncio.shield(api.stop_generation()),
                            timeout=6.0,
                        )
                    except Exception:
                        pass
                    if not query_task.done():
                        query_task.cancel()
                    try:
                        await query_task
                    except asyncio.CancelledError:
                        pass
                    console.print(
                        "\n[bold #8B5CF6]Exiting DEEPX. Goodbye![/bold #8B5CF6]"
                    )
                    raise SystemExit(0)

                if sys.platform == "win32":
                    windows_console_state = _begin_windows_ctrl_c_key_mode()
                if windows_console_state:
                    interrupt_task = asyncio.create_task(
                        _wait_for_windows_control_key()
                    )
                else:
                    interrupt_event = asyncio.Event()
                    interrupt_task = asyncio.create_task(interrupt_event.wait())
                    signal.signal(signal.SIGINT, request_stop)

            interrupted = True
            loop.set_exception_handler(cancellation_exception_handler)
            sys.stdout.write("\033[0m\r\033[K")
            sys.stdout.flush()
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
                    "\n[bold #F59E0B]Генерация остановлена. "
                    "Можно отправить новый запрос в этот же чат.[/bold #F59E0B]"
                )
            else:
                console.print(
                    "\n[bold #F59E0B]Ход агента отменён. "
                    "Кнопка остановки DeepSeek не найдена, но CLI снова готова к вводу.[/bold #F59E0B]"
                )
            return False
        finally:
            self._stop_streaming_file_visual()
            if not interrupt_task.done():
                interrupt_task.cancel()
            if not query_task.done():
                query_task.cancel()
            if not interrupted:
                loop.set_exception_handler(previous_exception_handler)
            _restore_windows_console_mode(windows_console_state)
            if not windows_console_state:
                signal.signal(signal.SIGINT, previous_sigint)

    async def handle_command(self, cmd: str, api: DeepAPI) -> bool:
        parts = cmd.split()
        main_cmd = parts[0].lower()

        if main_cmd in ["/exit", "/quit"]:
            console.print("[bold #8B5CF6]Exiting DEEPX. Goodbye![/bold #8B5CF6]")
            raise SystemExit(0)

        elif main_cmd == "/help":
            print_help()
            return True

        elif main_cmd == "/clear":
            self.refresh_ui()
            return True

        elif main_cmd == "/status":
            print_status(
                self.mode, self.agent_style, self.think, self.search,
                self.tools.cwd, self.state_file
            )
            return True

        elif main_cmd == "/stealth":
            report = await self.tools.browser_stealth_report()
            signals = report["signals"]
            table = Table(title="PLAYWRIGHT STEALTH CHECK", border_style="#536DFE")
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
            console.print(
                "[dim]This checks common browser signals, but cannot guarantee "
                "that Google or another anti-bot system will not detect automation.[/dim]"
            )
            return True

        elif main_cmd in ["/new", "/reset"]:
            console.print("[bold #8B5CF6]Initializing fresh session context...[/bold #8B5CF6]")
            await api.new_chat()
            self.is_new_chat = True
            self.refresh_ui()
            console.print("[bold #10B981]New session initialized.[/bold #10B981]")
            return True

        elif main_cmd == "/copy":
            if self.last_response:
                pyperclip.copy(self.last_response)
                console.print("[bold #10B981]Response copied to clipboard![/bold #10B981]")
            else:
                console.print("[dim #F59E0B]No response content to copy.[/dim #F59E0B]")
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
                        ("coder", "Coder — development, Python and browser automation"),
                        ("universal", "Universal"),
                        ("osinter", "OSINTer — DuckDuckGo recon, source verification, reports"),
                    ],
                ).run_async()
            if target_style:
                await self.switch_style(target_style, api)
            return True

        elif main_cmd == "/mode":
            target_mode = None
            if len(parts) > 1 and parts[1].lower() in ["instant", "expert", "vision"]:
                target_mode = parts[1].lower()
            else:
                selected = await radiolist_dialog(
                    title="Model Mode Selection",
                    text="Select operating model mode (Creates a new chat session context):",
                    values=[
                        ("instant", "Instant Mode (Fast & Responsive)"),
                        ("expert", "Expert Mode (Deep Reasoning Engine)"),
                        ("vision", "Vision Mode (Multimodal Recognition)")
                    ]
                ).run_async()
                if selected:
                    target_mode = selected

            if target_mode and target_mode != self.mode:
                self.mode = target_mode
                console.print(f"[bold #536DFE]Switching model mode to {self.mode.upper()} (Initializing fresh chat session...)[/bold #536DFE]")
                await api.new_chat()
                self.is_new_chat = True
                self.refresh_ui()
                console.print(f"[bold #38BDF8]Model mode set to {self.mode.upper()} in new session.[/bold #38BDF8]")
            return True

        elif main_cmd == "/think":
            if len(parts) > 1:
                self.think = (parts[1].lower() in ("on", "true", "1"))
            else:
                self.think = not self.think
            await api.set_deepthink(self.think)
            status_str = "ON" if self.think else "OFF"
            console.print(f"[bold #38BDF8]Think : {status_str}[/bold #38BDF8]")
            return True

        elif main_cmd == "/search":
            if self.mode == "expert":
                console.print("[dim #64748B]Smart Search is not available in Expert mode.[/dim #64748B]")
                return True
            if len(parts) > 1:
                self.search = (parts[1].lower() in ("on", "true", "1"))
            else:
                self.search = not self.search
            await api.set_search(self.search)
            status_str = "ON" if self.search else "OFF"
            console.print(f"[bold #38BDF8]Search : {status_str}[/bold #38BDF8]")
            return True

        else:
            console.print(f"[bold red]Unknown command: {cmd}. Type /help for command list.[/bold red]")
            return True

    async def open_interactive_menu(self, api: DeepAPI):
                                                        
        option = await radiolist_dialog(
            title="DEEPX Settings Menu",
            text="Use Arrow Keys (up/down) and press Enter to select setting to modify:",
            values=[
                ("mode", f"Change Model Mode -> Creates New Chat (Current: {self.mode.upper()})"),
                ("style", f"Change Agent Style -> Creates New Chat (Current: {self.agent_style.upper()})"),
                ("think", f"Toggle DeepThink Reasoning (Current: {'ON' if self.think else 'OFF'})"),
                ("search", f"Toggle Smart Web Search (Current: {'ON' if self.search else 'OFF'})"),
                ("new", "Reset Session Context")
            ]
        ).run_async()

        if option == "mode":
            mode_choice = await radiolist_dialog(
                title="Select Model Mode",
                text="Choose target model (Will initialize a new chat session):",
                values=[
                    ("instant", "Instant Mode (Fast)"),
                    ("expert", "Expert Mode (Deep Reasoning)"),
                    ("vision", "Vision Mode (Multimodal)")
                ]
            ).run_async()
            if mode_choice and mode_choice != self.mode:
                self.mode = mode_choice
                console.print(f"[bold #536DFE]Switching model mode to {self.mode.upper()} (Initializing fresh chat session...)[/bold #536DFE]")
                await api.new_chat()
                self.is_new_chat = True
                self.refresh_ui()
                console.print(f"[bold #38BDF8]Model mode set to {self.mode.upper()} in new session.[/bold #38BDF8]")
        elif option == "style":
            style_choice = await radiolist_dialog(
                title="Select Agent Style",
                text="Choose a specialized prompt and toolset:",
                values=[
                    ("coder", "Coder — development, Python and browser automation"),
                    ("universal", "Universal"),
                    ("osinter", "OSINTer — DuckDuckGo recon, source verification, reports"),
                ],
            ).run_async()
            if style_choice:
                await self.switch_style(style_choice, api)
        elif option == "think":
            self.think = not self.think
            await api.set_deepthink(self.think)
            status_str = "ON" if self.think else "OFF"
            console.print(f"[bold #38BDF8]Think : {status_str}[/bold #38BDF8]")
        elif option == "search":
            if self.mode == "expert":
                console.print("[dim #64748B]Smart Search is not available in Expert mode.[/dim #64748B]")
            else:
                self.search = not self.search
                await api.set_search(self.search)
                status_str = "ON" if self.search else "OFF"
                console.print(f"[bold #38BDF8]Search : {status_str}[/bold #38BDF8]")
        elif option == "new":
            await api.new_chat()
            self.is_new_chat = True
            self.refresh_ui()
            console.print("[bold #38BDF8]Session reset successfully.[/bold #38BDF8]")

    def _print_tool_call_panel(self, call: dict):
        tool_name = call.get("tool")
        tool_args = call.get("args", {})
        if tool_name in FILE_VISUAL_TOOL_NAMES or tool_name in ["render_plan", "todo"]:
            return
        if tool_name in ["run_cmd", "run_background_cmd"]:
            cmd_preview = tool_args.get("command", "")
            if len(cmd_preview) > 55:
                cmd_preview = cmd_preview[:52] + "..."
            summary_str = f"{tool_name}: {cmd_preview}"
        elif tool_name in ["read_file", "file_info"]:
            path_preview = tool_args.get("path", "") or "<no path>"
            summary_str = f"{tool_name}: {path_preview}"
            if tool_name == "read_file" and tool_args.get("start_line"):
                summary_str += (
                    f" [{tool_args.get('start_line')}-{tool_args.get('end_line')}]"
                )
        elif tool_name == "run_python":
            code_preview = tool_args.get("code", "").replace("\n", " ")
            if len(code_preview) > 55:
                code_preview = code_preview[:52] + "..."
            summary_str = f"run_python: {code_preview}"
        else:
            arg_preview = str(tool_args)
            if len(arg_preview) > 45:
                arg_preview = arg_preview[:42] + "..."
            summary_str = f"{tool_name}: {arg_preview}"

        console.print(Panel(
            f"[bold #536DFE]> {summary_str}[/bold #536DFE]",
            box=box.ROUNDED,
            border_style="#536DFE",
            padding=(0, 1),
            expand=False,
        ))

    def _file_visual_snapshot(self, path: str):
        abs_path = os.path.abspath(os.path.join(self.tools.cwd, path or ""))
        exists = os.path.isfile(abs_path)
        if not exists:
            return False, []
        if Path(abs_path).suffix.lower() in {
            ".xlsx", ".xls", ".docx", ".pptx", ".zip"
        }:
            return True, []
        try:
            with open(abs_path, "r", encoding="utf-8", errors="replace") as file:
                return True, file.read().splitlines()
        except OSError:
            return True, []

    def _file_visual_style(self, action: str):
        return {
            "created": ("FILE CREATED", "#10B981"),
            "modified": ("FILE MODIFIED", "#38BDF8"),
            "deleted": ("FILE DELETED", "#EF4444"),
        }[action]

    def _file_visual_line(
        self,
        action: str,
        filename: str,
        spinner: str = "",
        added: int = 0,
        removed: int = 0,
    ):
        label, color = self._file_visual_style(action)
        line = Text()
        line.append("▌", style=f"bold {color}")
        line.append(" ")
        line.append(label.ljust(13), style=f"bold {color}")
        line.append(" ")
        line.append(filename or "<unknown>", style="bold white")
        if spinner:
            line.append(f" {spinner}", style=f"bold {color}")
        else:
            if added:
                line.append(f" +{added}", style="bold #10B981")
            if removed:
                line.append(f" -{removed}", style="bold #EF4444")
        return line

    def _file_visual_diff(self, before_lines: list, after_lines: list):
        added = 0
        removed = 0
        matcher = difflib.SequenceMatcher(a=before_lines, b=after_lines, autojunk=False)
        for operation, before_start, before_end, after_start, after_end in matcher.get_opcodes():
            if operation in ("insert", "replace"):
                added += after_end - after_start
            if operation in ("delete", "replace"):
                removed += before_end - before_start
        return added, removed

    def _detect_streaming_file_activities(self, text: str):
        """Find file tool calls as soon as their tool name and path are streamed."""
        tool_pattern = re.compile(
            r'"tool"\s*:\s*"('
            + "|".join(sorted(FILE_VISUAL_TOOL_NAMES))
            + r')"'
        )
        matches = list(tool_pattern.finditer(text or ""))
        detected = []
        for index, match in enumerate(matches):
            segment_end = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else min(len(text), match.end() + 4000)
            )
            segment = text[match.end():segment_end]
            path_match = re.search(
                r'"path"\s*:\s*"((?:\\.|[^"\\])*)"',
                segment,
                flags=re.DOTALL,
            )
            if not path_match:
                continue
            raw_path = path_match.group(1)
            try:
                path = json.loads(f'"{raw_path}"')
            except Exception:
                path = raw_path.replace(r"\\", "\\").replace(r"\"", '"')
            path = str(path or "").strip()
            if not path:
                continue
            tool_name = match.group(1)
            before_exists, _ = self._file_visual_snapshot(path)
            action = (
                "created"
                if tool_name != "edit_file" and not before_exists
                else "modified"
            )
            detected.append((tool_name, path, action))
        return detected

    def _streaming_file_renderable(self, frame_index: int):
        renderables = []
        for activity in self._stream_file_activities.values():
            renderables.append(self._file_visual_line(
                activity["action"],
                activity["filename"],
                spinner=FILE_PROGRESS_FRAMES[
                    frame_index % len(FILE_PROGRESS_FRAMES)
                ],
            ))
        return Group(*renderables)

    def _update_streaming_file_visual(
        self,
        text: str,
        frame_index: int,
        leading_newlines: int = 0,
    ):
        detected = self._detect_streaming_file_activities(text)
        if not detected:
            return set()

        if not hasattr(self, "_stream_file_activities"):
            self._stream_file_activities = {}
        for tool_name, path, action in detected:
            key = (tool_name, path)
            self._stream_file_activities.setdefault(key, {
                "action": action,
                "filename": path.replace("\\", "/").split("/")[-1] or path,
            })

        renderable = self._streaming_file_renderable(frame_index)
        if getattr(self, "_active_file_live", None) is None:
            if leading_newlines > 0:
                sys.stdout.write("\n" * leading_newlines)
                sys.stdout.flush()
            self._active_file_live = Live(
                renderable,
                console=console,
                refresh_per_second=20,
                transient=True,
            )
            self._active_file_live.start()
        else:
            self._active_file_live.update(renderable, refresh=False)
        return {(tool_name, path) for tool_name, path, _ in detected}

    def _stop_streaming_file_visual(self):
        live = getattr(self, "_active_file_live", None)
        if live is not None:
            try:
                live.stop()
            finally:
                self._active_file_live = None
        if hasattr(self, "_stream_file_activities"):
            self._stream_file_activities = {}

    async def _execute_file_tool_call(self, tool_name: str, tool_args: dict):
        tool_args = dict(tool_args or {})
        stream_previewed = bool(tool_args.pop("_stream_previewed", False))
        path = str(tool_args.get("path", "") or "")
        filename = path.replace("\\", "/").split("/")[-1] or path or "<unknown>"
        before_exists, before_lines = self._file_visual_snapshot(path)
        pending_action = (
            "created"
            if tool_name in ("write_file", "make_excel") and not before_exists
            else "modified"
        )
        if stream_previewed:
            result = await self.tools.execute_tool(
                tool_name,
                tool_args,
                allowed_tools=self.allowed_tools,
            )
        else:
            started_at = asyncio.get_running_loop().time()
            frame_index = 0
            operation = asyncio.create_task(self.tools.execute_tool(
                tool_name,
                tool_args,
                allowed_tools=self.allowed_tools,
            ))

            with Live(
                self._file_visual_line(
                    pending_action,
                    filename,
                    spinner=FILE_PROGRESS_FRAMES[0],
                ),
                console=console,
                refresh_per_second=20,
                transient=True,
            ) as live:
                while (
                    not operation.done()
                    or asyncio.get_running_loop().time() - started_at
                    < FILE_PROGRESS_MIN_SECONDS
                ):
                    live.update(self._file_visual_line(
                        pending_action,
                        filename,
                        spinner=FILE_PROGRESS_FRAMES[
                            frame_index % len(FILE_PROGRESS_FRAMES)
                        ],
                    ))
                    frame_index += 1
                    await asyncio.sleep(FILE_PROGRESS_FRAME_SECONDS)
                result = await operation

        result_text = str(result)
        if result_text.startswith(("[Error", "[Access denied")):
            return result

        after_exists, after_lines = self._file_visual_snapshot(path)
        if before_exists and not after_exists:
            final_action = "deleted"
        elif not before_exists and after_exists:
            final_action = "created"
        else:
            final_action = "modified"
        added, removed = self._file_visual_diff(before_lines, after_lines)
        console.print(self._file_visual_line(
            final_action,
            filename,
            added=added,
            removed=removed,
        ))
        return result

    async def _execute_one_tool_call(self, call: dict):
        tool_name = call.get("tool")
        tool_args = call.get("args", {})
        try:
            if tool_name in FILE_VISUAL_TOOL_NAMES:
                result = await self._execute_file_tool_call(tool_name, tool_args)
            else:
                result = await self.tools.execute_tool(
                    tool_name,
                    tool_args,
                    allowed_tools=self.allowed_tools,
                )
        except Exception as error:
            result = f"[Error executing tool '{tool_name}': {type(error).__name__}: {error}]"
        clean_result = sanitize_tool_result(result)
        return f"[TOOL RESULT for '{tool_name}']:\n{clean_result}"

    async def _execute_tool_calls(self, tool_calls: list):
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
                for batch_call in batch:
                    self._print_tool_call_panel(batch_call)
                self.tools.flush_todos()
                batch_outputs = await asyncio.gather(
                    *(self._execute_one_tool_call(batch_call) for batch_call in batch)
                )
                outputs.extend(batch_outputs)
                executed_count += len(batch)
                index = end
                continue

            self._print_tool_call_panel(call)
            if tool_name != "todo":
                self.tools.flush_todos()
            outputs.append(await self._execute_one_tool_call(call))
            if tool_name != "todo":
                executed_count += 1
            index += 1

        self.tools.flush_todos()
        return outputs, executed_count

    async def process_query(self, user_input: str, api: DeepAPI):
                                                                                                                    
        
        original_goal = user_input
        failure_counts = {}
        pending_verification = False
        strategy_change_required = False
        verification_nudges = 0
        current_prompt = user_input
                                                                                      
        if self.is_new_chat:
            system_prompt = build_agent_system_prompt(self.agent_style, self.think, self.tools.cwd)
            if self.mode == "expert":
                system_prompt += (
                    "\n\n[EXPERT MODE]: Never invoke or refer to DeepSeek's internal "
                    "Search/link-reading feature and never tell the user to switch to "
                    "Fast/Instant mode. Use only the external tools listed in this prompt."
                )
            current_prompt = (
                f"{system_prompt}\n\n[ПОЛЬЗОВАТЕЛЬСКИЙ ЗАПРОС]:\n"
                f"{user_input}"
            )
            self.is_new_chat = False

        if self.is_new_chat:
            await api.new_chat()
            self.is_new_chat = False

        await api.set_mode(self.mode)
        if self.mode == "instant":
            await api.set_search(self.search)
        await api.set_deepthink(self.think)

        loop_count = 0
        did_execute_tool = False
        executed_tool_count = 0
        todo_nudged = False
        empty_responses = 0
                                                                                            
                                                              
        if self.tools.todos and all(
            item["status"] in ("done", "cancelled") for item in self.tools.todos
        ):
            self.tools.todos = []

        spinner_frames = ["|", "/", "-", "\\"]

        while True:
            loop_count += 1

            if loop_count == 1:
                sys.stdout.write("\n")
                sys.stdout.flush()

            try:
                stream_gen = await api.send_message(current_prompt, stream=True)
            except Exception as send_error:
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
            thinking_line_printed = False
            answer_started = False
            has_printed_text_this_turn = False
            final_think = ""
            final_answer = ""
            stream_previewed_file_calls = set()
            stream_visual_frame = 0
            stream_file_visual_was_shown = False
            stable_stream_text = StableStreamText()
            self._stop_streaming_file_visual()
            stream_writer = AdaptiveStreamWriter()
            drain_task = asyncio.create_task(stream_writer.drain())

            async for chunk in stream_gen:
                if not isinstance(chunk, dict):
                    continue

                final_think = chunk.get("think", "")
                final_answer = chunk.get("answer", "")

                if final_answer:
                    answer_started = True

                if final_think and not answer_started:
                    thinking_line_printed = True
                    tok_count = count_tokens(final_think)
                    frame = spinner_frames[len(final_think) % len(spinner_frames)]
                    sys.stdout.write(f"\r\033[K\033[38;2;83;109;254m[THINKING {frame}] Reasoning in progress... ({tok_count} tokens)\033[0m")
                    sys.stdout.flush()
                
                if final_answer:
                    if thinking_line_printed:
                        sys.stdout.write("\r\033[K")
                        sys.stdout.flush()
                        thinking_line_printed = False

                    stable_source = stable_stream_text.update(
                        get_clean_text(final_answer)
                    )
                    cleaned = render_terminal_markup(stable_source, final=False)
                    
                    if (
                        not stream_file_visual_was_shown
                        and len(cleaned) > len(printed_answer)
                    ):
                        if cleaned.startswith(printed_answer):
                            new_chars = cleaned[len(printed_answer):]
                            if not has_printed_text_this_turn:
                                if loop_count > 1 and did_execute_tool:
                                    sys.stdout.write("\n")
                                has_printed_text_this_turn = True
                            stream_writer.push(new_chars)
                            printed_answer = cleaned
                        elif cleaned.startswith(printed_answer.rstrip("\n")):
                            base = printed_answer.rstrip("\n")
                            new_chars = cleaned[len(base):]
                            if not has_printed_text_this_turn:
                                if loop_count > 1 and did_execute_tool:
                                    sys.stdout.write("\n")
                                has_printed_text_this_turn = True
                            stream_writer.push(new_chars)
                            printed_answer = cleaned

                    pending_file_calls = self._detect_streaming_file_activities(
                        final_answer
                    )
                    if pending_file_calls and not stream_file_visual_was_shown:
                        # Finish ordinary stdout before Rich Live starts moving
                        # the terminal cursor.
                        await stream_writer.finish()
                        await drain_task

                    detected_file_calls = self._update_streaming_file_visual(
                        final_answer,
                        stream_visual_frame,
                        leading_newlines=(
                            max(
                                0,
                                2 - (
                                    len(printed_answer)
                                    - len(printed_answer.rstrip("\n"))
                                ),
                            )
                            if printed_answer
                            and not stream_file_visual_was_shown
                            else 0
                        ),
                    )
                    if detected_file_calls:
                        stream_previewed_file_calls.update(detected_file_calls)
                        stream_visual_frame += 1
                        stream_file_visual_was_shown = True

                                                                                       
            await stream_writer.finish()
            await drain_task
            self._stop_streaming_file_visual()
            final_display = render_terminal_markup(get_clean_text(final_answer), final=True)
            if len(final_display) > len(printed_answer):
                if final_display.startswith(printed_answer):
                    await write_streaming_chars(final_display[len(printed_answer):])
                else:
                    common_len = 0
                    for old_char, new_char in zip(printed_answer, final_display):
                        if old_char != new_char:
                            break
                        common_len += 1
                    await write_streaming_chars(final_display[common_len:])
                printed_answer = final_display

            if printed_answer and not stream_file_visual_was_shown:
                nl_count = len(printed_answer) - len(printed_answer.rstrip('\n'))
                if nl_count == 0:
                    console.print("\n")
                elif nl_count == 1:
                    console.print()

            final_answer = final_answer.strip()
            final_think = final_think.strip()

                                                                                       
                                                                                 
                                                                                        
                                                                      
            if not final_answer:
                if final_think:
                    console.print(
                        "\n[bold #F59E0B]Ответ оборван: модель начала размышлять, но текста "
                        "ответа нет.[/bold #F59E0B]"
                    )
                    console.print(
                        "[dim #94A3B8]Автопродолжение не выполняется. Напиши, что делать "
                        "дальше.[/dim #94A3B8]"
                    )
                    break

                empty_responses += 1
                if empty_responses > MAX_EMPTY_RESPONSE_RETRIES:
                    console.print(
                        f"\n[bold red]Пустой ответ {empty_responses} раз(а) подряд. "
                        "Останавливаюсь.[/bold red]"
                    )
                    break

                delay = 2 * empty_responses
                console.print(
                    f"\n[bold #F59E0B]Пустой ответ от API (попытка {empty_responses} из "
                    f"{MAX_EMPTY_RESPONSE_RETRIES}). Повтор через {delay} с...[/bold #F59E0B]"
                )
                await asyncio.sleep(delay)
                continue

            empty_responses = 0

            full_rendered = ""
            if final_think:
                full_rendered += f"--- [РАЗМЫШЛЕНИЯ] ---\n{get_clean_text(final_think)}\n\n"
            if final_answer:
                full_rendered += get_clean_text(final_answer)

            self.last_response = full_rendered

                                                             
            tool_calls = extract_tool_calls(final_answer)
            if tool_calls:
                    for call in tool_calls:
                        tool_name = str(call.get("tool", ""))
                        tool_path = str(call.get("args", {}).get("path", "") or "")
                        if (tool_name, tool_path) in stream_previewed_file_calls:
                            call.setdefault("args", {})["_stream_previewed"] = True
                    did_execute_tool = True
                    tool_outputs, current_executed_count = await self._execute_tool_calls(
                        tool_calls
                    )
                    executed_tool_count += current_executed_count

                    last_mutation_index = -1
                    for call_index, (call, output) in enumerate(
                        zip(tool_calls, tool_outputs)
                    ):
                        tool_name = str(call.get("tool", "unknown"))
                        if _tool_result_failed(output):
                            failure_key = (
                                tool_name,
                                json.dumps(
                                    call.get("args", {}),
                                    ensure_ascii=False,
                                    sort_keys=True,
                                    default=str,
                                ),
                            )
                            failure_counts[failure_key] = (
                                failure_counts.get(failure_key, 0) + 1
                            )
                            if failure_counts[failure_key] >= 2:
                                strategy_change_required = True
                        else:
                            strategy_change_required = False

                        if tool_name in MUTATING_TOOLS_REQUIRING_VERIFICATION:
                            last_mutation_index = call_index

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
                    interactive_prompt_detected = None
                    for output in tool_outputs:
                        if "WAITING_FOR_INPUT" in output:
                            try:
                                json_match = re.search(
                                    r'\{[^{}]*"status"\s*:\s*"WAITING_FOR_INPUT"[^{}]*\}',
                                    output,
                                    re.DOTALL,
                                )
                                if json_match:
                                    interactive_prompt_detected = json.loads(json_match.group(0))
                                    break
                            except Exception:
                                pass

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
                            include_goal=(
                                loop_count % TASK_GOAL_REMINDER_INTERVAL == 0
                            ),
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
                        )
                        continue

                    task_state = build_agent_task_state(
                        original_goal,
                        self.tools.todos,
                        pending_verification=pending_verification,
                        strategy_change_required=strategy_change_required,
                        include_goal=(
                            loop_count % TASK_GOAL_REMINDER_INTERVAL == 0
                        ),
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
            else:
                has_unfinished_todos = any(
                    item.get("status") in ("active", "pending")
                    for item in self.tools.todos
                )
                action_promise_re = re.compile(
                    r"(?:(?:сейчас|сначала|дальше|теперь|затем|пока|пробуем|пробую|попробуем|попробую|тестируем|тестирую|проверяем|проверяю|пытаемся|пытаюсь|отправляю|отправляем)\s+(?:проверю|проверить|установлю|установить|попробую|попробовать|выполню|выполнить|сделаю|сделать|запущу|запустить|подключусь|подключиться|посмотрю|посмотреть|отправлю|отправить|перейду|перейти|протестирую|протестировать|переполнение)|"
                    r"проверю\s+(?:доступные|наличие|работу|файлы|порты|версию|команду|менеджеры|пакеты)|"
                    r"пробуем\s+(?:переполнение|инъекци|запрос|отправить|проверить|тестировать|подобрать|найти)|"
                    r"пробую\s+(?:переполнение|инъекци|запрос|отправить|проверить|тестировать|подобрать|найти)|"
                    r"тестирую\s+(?:инъекци|запрос|эндпоинт|авторизаци|логин|пароль|токен|ошибк)|"
                    r"тестируем\s+(?:инъекци|запрос|эндпоинт|авторизаци|логин|пароль|токен|ошибк)|"
                    r"отправляю\s+(?:запрос|payload|данные|пакет|параметр)|"
                    r"отправляем\s+(?:запрос|payload|данные|пакет|параметр)|"
                    r"установлю\s+(?:через|с\s+помощью|пакет)|"
                    r"попробую\s+(?:подключиться|запустить|выполнить|установить)|"
                    r"(?:перехожу|приступаю)\s+к|"
                    r"следующим\s+(?:шагом|действием)|"
                    r"(?:i\s+will|let\s+me|going\s+to|testing|trying|sending)\s+(?:now\s+)?(?:check|install|run|try|execute|verify|test|send|navigate))",
                    re.IGNORECASE,
                )
                has_action_promise = bool(action_promise_re.search(final_answer))
                
                tool_call_marker_re = re.compile(
                    r"(?:```\s*(?:tool_call|tool_calls|tools|tool|json)|<(?:tool_call|function_call|invoke)|(?:^|\n)\s*tool_call\s*\n\s*\{)",
                    re.IGNORECASE
                )
                has_unparsed_tool_markup = bool(tool_call_marker_re.search(final_answer))

                if (pending_verification or has_unfinished_todos or has_action_promise or has_unparsed_tool_markup) and verification_nudges < 3:
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
                            include_goal=(
                                loop_count % TASK_GOAL_REMINDER_INTERVAL == 0
                            ),
                        )
                        + f"\n{nudge_reason} Не повторяй неподтверждённый финальный ответ и не пиши обещания без вызова ```tool_call."
                    )
                    continue
                break
