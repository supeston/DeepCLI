import asyncio
import os
import re

from deepx.agent.checkpoints import CheckpointManager
from deepx.core.config import APP_DIR, default_workspace_dir
from deepx.core.constants import (
    SELF_PROTECTED_DIRS,
    SELF_PROTECTED_FILES,
    SELF_PROTECTED_PREFIXES,
)
from deepx.parser.tool_parser import canonicalize_tool_name, normalize_tool_args
from deepx.tools.dadata_osint import DadataOSINTTool
from deepx.tools.funstat_osint import FunstatOSINTTool

                                                                                
                    
                                                                                

from .system import SystemToolsMixin
from .filesystem import FileSystemToolsMixin
from .browser import BrowserToolsMixin
from .documents import DocumentsToolsMixin
from .web import WebToolsMixin
from .todo import TodoToolsMixin
from .project import ProjectToolsMixin
from .media_inspector import MediaInspectorMixin
from .clipboard import ClipboardMixin
from .vds import VDSToolsMixin

class AgentTools(
    SystemToolsMixin,
    FileSystemToolsMixin,
    BrowserToolsMixin,
    DocumentsToolsMixin,
    WebToolsMixin,
    TodoToolsMixin,
    ProjectToolsMixin,
    MediaInspectorMixin,
    ClipboardMixin,
    VDSToolsMixin,
):
    _PLAN_MODE_BLOCKED_TOOLS = frozenset({
        "write_file",
        "edit_file",
        "make_excel",
        "make_docx",
        "make_pptx",
        "zip_pack",
        "unzip_pack",
        "run_cmd",
        "run_python",
        "run_background_cmd",
        "vds_deploy",
        "write_clipboard",
        "set_clipboard",
        "delete_clipboard_item",
        "clear_clipboard_history",
    })

    def __init__(
        self,
        cwd: str = None,
        browser_state_file: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core", ".deepx_browser_state.json"),
        browser_headless: bool = True
    ):
        self.cwd = os.path.abspath(cwd) if cwd else default_workspace_dir()
        self.browser_state_file = os.path.abspath(os.path.join(APP_DIR, browser_state_file))
        self.project_memory_file = os.path.abspath(
            os.path.join(self.cwd, ".deepx_project_memory.json")
        )
        self.browser_headless = browser_headless
        self.protect_self = False
        self.plan_mode = False
        self.extra_protected = set()
        self.checkpoints = CheckpointManager(self.cwd)
        self.todos = []
        self._todo_dirty = False
        self._todo_rendered_signature = None
        self.playwright = None
        self.browser = None
        self.browser_context = None
        self.page = None
        self.browser_timeout = 15000
        self.browser_stealth_status = "not initialized"
        self.active_tasks = {}
        self._background_task_counter = 0

    def set_workspace(self, cwd: str):
        self.cwd = os.path.abspath(cwd)
        self.project_memory_file = os.path.abspath(
            os.path.join(self.cwd, ".deepx_project_memory.json")
        )
        if hasattr(self, "checkpoints") and self.checkpoints is not None:
            self.checkpoints.set_workspace(self.cwd)
    def add_protected(self, path: str):
                                                                                          
        if path:
            self.extra_protected.add(os.path.realpath(os.path.abspath(os.path.join(APP_DIR, path))))
    def is_protected(self, path: str) -> bool:
                                                                                       

                                                                               
                                                                               
           
        if not path:
            return False
        try:
            real = os.path.realpath(os.path.abspath(os.path.join(self.cwd, str(path))))
        except Exception:
            return True                                               

        if not self.protect_self:
            return False

        if real in self.extra_protected:
            return True

        try:
            relative = os.path.relpath(real, APP_DIR)
        except ValueError:
            return False                                                  
                                                                                          
                                                                               
        return relative == os.curdir or not relative.startswith(os.pardir)
    def _deny(self, path: str) -> str:
        return (
            f"[Access denied: '{path}' belongs to the DEEPX application itself and is "
            "permanently blocked in this agent style. It does not exist for you. "
            "Do not attempt to reach it by another route.]"
        )
    def _command_touches_self(self, text: str) -> bool:
        if not self.protect_self or not text:
            return False
        lowered = str(text).lower()
        needles = set(SELF_PROTECTED_FILES) | set(SELF_PROTECTED_DIRS)
        needles.update(SELF_PROTECTED_PREFIXES)
        needles.update(os.path.basename(p).lower() for p in self.extra_protected)
        app_real = os.path.realpath(APP_DIR).lower()
        needles.update({
            app_real,
            APP_DIR.lower(),
            "deepx/",
            "deepx\\",
            "deepx.",
            "import deepx",
            "from deepx",
            "deepx/core",
            "deepx\\core",
            "deepx/tools",
            "deepx\\tools",
            "deepx/agent",
            "deepx\\agent",
            "tools/vds.py",
            "tools\\vds.py",
            "tools/manager.py",
            "tools\\manager.py",
        })
        return any(needle and needle in lowered for needle in needles)
    def _process_kill_guard(self, text: str):
        """Reject process-kill commands that can terminate the DEEPX runner."""
        if not text:
            return None

        command = str(text)
        lowered = command.lower()
        agent_pid = os.getpid()

        taskkill_calls = re.findall(
            r"(?:^|[&|])\s*([^&|\r\n]*\btaskkill\b[^&|\r\n]*)",
            lowered,
        )
        for taskkill_call in taskkill_calls:
            if re.search(r"/(?:im|fi)\b", taskkill_call):
                return (
                    "taskkill by image name or filter is blocked because it can "
                    "terminate DEEPX. Use only `taskkill /PID <pid> /F`."
                )
            pid_values = {
                int(value)
                for value in re.findall(r"/pid\s+(\d+)", taskkill_call)
            }
            if not pid_values:
                return (
                    "mass taskkill is blocked because it can terminate DEEPX. "
                    "Find the exact target PID first, then use "
                    "`taskkill /PID <pid> /F`."
                )
            if agent_pid in pid_values:
                return (
                    f"PID {agent_pid} belongs to the active DEEPX process and "
                    "cannot be terminated."
                )

        if re.search(r"\b(?:wmic|pkill|killall)\b.*\b(?:delete|terminate|python)", lowered):
            return (
                "mass process termination is blocked. Find the exact target "
                "PID and terminate only that PID."
            )

        if "stop-process" in lowered:
            pid_values = {
                int(value)
                for value in re.findall(r"(?:-id\s+|stop-process\s+)(\d+)", lowered)
            }
            if not pid_values:
                return (
                    "Stop-Process without an explicit numeric PID is blocked "
                    "because it can terminate DEEPX."
                )
            if agent_pid in pid_values:
                return (
                    f"PID {agent_pid} belongs to the active DEEPX process and "
                    "cannot be terminated."
                )

        direct_kill = re.search(
            r"(?:^|[&|])\s*(?:kill|tskill)\s+(?:-[a-z0-9]+\s+)*(\d+)\b",
            lowered,
        )
        if direct_kill and int(direct_kill.group(1)) == agent_pid:
            return (
                f"PID {agent_pid} belongs to the active DEEPX process and "
                "cannot be terminated."
            )

        return None
    async def execute_tool(self, tool_name: str, args: dict, allowed_tools=None) -> str:
        tool_name = canonicalize_tool_name(tool_name)
        args = normalize_tool_args(args or {})
        if allowed_tools is not None and tool_name not in allowed_tools and canonicalize_tool_name(tool_name) not in allowed_tools:
            return f"[Error: Tool '{tool_name}' is unavailable in the active agent style]"
        if getattr(self, "plan_mode", False) and tool_name in self._PLAN_MODE_BLOCKED_TOOLS:
            return (
                f"[Blocked in Plan mode: tool '{tool_name}' modifies files or executes external actions. "
                "Finish planning or switch mode with /mode think or /mode instant first.]"
            )
        if tool_name == "run_cmd":
            command = args.get("command") or args.get("cmd") or args.get("shell") or args.get("code") or ""
            return await asyncio.to_thread(
                self.run_cmd, command, args.get("inputs", None)
            )
        elif tool_name == "send_input":
            session_id = str(args.get("session_id") or args.get("id") or "")
            text_val = str(args.get("text") if args.get("text") is not None else args.get("input") if args.get("input") is not None else args.get("content", ""))
            return await asyncio.to_thread(
                self.send_input,
                session_id,
                text_val,
            )
        elif tool_name == "kill_cmd":
            return await asyncio.to_thread(
                self.kill_cmd, str(args.get("session_id") or args.get("id") or "")
            )
        elif tool_name == "run_python":
            code = args.get("code") or args.get("script") or args.get("python_code") or args.get("content") or ""
            return await asyncio.to_thread(self.run_python, code)
        elif tool_name == "run_background_cmd":
            command = args.get("command") or args.get("cmd") or ""
            return await self.run_background_cmd(
                command, args.get("inputs", None)
            )
        elif tool_name == "task_status":
            return self.task_status(str(args.get("id") or args.get("task_id") or ""))
        elif tool_name == "task_log":
            return self.task_log(
                str(args.get("id") or args.get("task_id") or ""),
                args.get("tail_lines", 200),
            )
        elif tool_name == "kill_background_cmd":
            return await self.kill_background_cmd(
                str(args.get("id") or args.get("task_id") or "")
            )
        elif tool_name == "todo":
            return self.todo(args.get("action", "list"), args)
        elif tool_name == "web_search":
            query = args.get("query") or args.get("q") or args.get("search_query") or args.get("text") or ""
            return await asyncio.to_thread(
                self.web_search,
                query,
                args.get("max_results", 10),
                args.get("site", ""),
                args.get("region", "wt-wt"),
            )
        elif tool_name == "funstat_osint":
            return await FunstatOSINTTool().run(
                args.get("action", "free_scan"),
                args.get("telegram_id"),
                args.get("username"),
                allow_paid=bool(args.get("allow_paid", True)),
            )
        elif tool_name == "dadata_osint":
            dadata_opts = args.get("options", {})
            req_out = (
                (dadata_opts.get("output_dir") if isinstance(dadata_opts, dict) else None)
                or args.get("output_dir")
            )
            resolved_out = os.path.abspath(
                os.path.join(self.cwd, str(req_out) if req_out else "dadata_logos")
            )
            if self.is_protected(resolved_out):
                return self._deny(str(req_out or resolved_out))
            return await DadataOSINTTool().run(
                action=args.get("action", ""),
                query=args.get("query"),
                lat=args.get("lat"),
                lon=args.get("lon"),
                count=args.get("count", 10),
                options=dadata_opts,
                output_dir=resolved_out,
                protected_checker=self.is_protected,
            )
        elif tool_name == "fetch_url":
            url = str(args.get("url") or args.get("link") or args.get("target") or "")
            return await asyncio.to_thread(
                self.fetch_url, url, args.get("max_chars", 6000)
            )
        elif tool_name == "read_file":
            path = str(args.get("path") or args.get("file") or args.get("filename") or "")
            return await asyncio.to_thread(
                self.read_file,
                path,
                args.get("start_line", 1),
                args.get("end_line", 500),
            )
        elif tool_name == "write_file":
            path = str(args.get("path") or args.get("file") or args.get("filename") or "")
            content = str(args.get("content") if args.get("content") is not None else args.get("code") if args.get("code") is not None else args.get("text", ""))
            return await asyncio.to_thread(
                self.write_file, path, content
            )
        elif tool_name == "edit_file":
            path = str(args.get("path") or args.get("file") or args.get("filename") or "")
            target = str(args.get("target") if args.get("target") is not None else "")
            replacement = str(args.get("replacement") if args.get("replacement") is not None else "")
            return await asyncio.to_thread(
                self.edit_file,
                path,
                target,
                replacement,
                args.get("start_line"),
                args.get("end_line"),
            )
        elif tool_name == "list_dir":
            path = str(args.get("path") or args.get("dir") or args.get("directory") or ".")
            return await asyncio.to_thread(self.list_dir, path)
        elif tool_name == "grep_search":
            pattern = str(args.get("pattern") or args.get("query") or args.get("text") or "")
            path = str(args.get("path") or args.get("dir") or ".")
            include = str(args.get("include") or args.get("glob") or "")
            return await asyncio.to_thread(
                self.grep_search,
                pattern,
                path,
                include,
                args.get("max_results", 60),
                bool(args.get("case_sensitive", False)),
            )
        elif tool_name == "file_info":
            path = str(args.get("path") or args.get("file") or args.get("filename") or "")
            return await asyncio.to_thread(self.file_info, path)
        elif tool_name == "project_memory":
            return await asyncio.to_thread(self.project_memory, args.get("action", "get"), args)
        elif tool_name == "sys_info":
            return self.sys_info()
        elif tool_name == "browser_action":
            return await self.browser_action(args.get("action", ""), args)
        elif tool_name == "render_plan":
            return await asyncio.to_thread(
                self.render_plan,
                args.get("title", "План выполнения задачи"),
                args.get("steps", []),
            )
        elif tool_name == "make_excel":
            return await asyncio.to_thread(self.make_excel, args.get("path", ""), args.get("sheets", {}))
        elif tool_name == "make_docx":
            return await asyncio.to_thread(
                self.make_docx,
                args.get("path", ""),
                args.get("title", "Document"),
                args.get("paragraphs", []),
            )
        elif tool_name == "make_pptx":
            return await asyncio.to_thread(
                self.make_pptx,
                args.get("path", ""),
                args.get("title", "Presentation"),
                args.get("slides", []),
            )
        elif tool_name == "zip_pack":
            return await asyncio.to_thread(self.zip_pack, args.get("zip_path", ""), args.get("files", []))
        elif tool_name == "unzip_pack":
            return await asyncio.to_thread(self.unzip_pack, args.get("zip_path", ""), args.get("extract_to", "."))
        elif tool_name == "inspect_media":
            return await asyncio.to_thread(
                self.inspect_media,
                args.get("path", ""),
                args.get("detailed", True),
            )
        elif tool_name == "read_clipboard":
            return await asyncio.to_thread(self.read_clipboard)
        elif tool_name == "write_clipboard":
            return await asyncio.to_thread(
                self.write_clipboard,
                args.get("content", args.get("text", "")),
            )
        elif tool_name == "get_clipboard_history":
            return await self.get_clipboard_history(args.get("limit", 10))
        elif tool_name == "get_clipboard_item":
            return await self.get_clipboard_item(
                index=args.get("index"), item_id=args.get("item_id", args.get("id"))
            )
        elif tool_name == "set_clipboard":
            return await self.set_clipboard(args.get("content", args.get("text", "")))
        elif tool_name == "delete_clipboard_item":
            return await self.delete_clipboard_item(
                index=args.get("index"), item_id=args.get("item_id", args.get("id"))
            )
        elif tool_name == "clear_clipboard_history":
            return await asyncio.to_thread(self.clear_clipboard_history)
        elif tool_name == "vds_deploy":
            safe_args = dict(args)
            vds_action = safe_args.pop("action", None)
            safe_args.pop("self", None)
            return await asyncio.to_thread(self.vds_deploy, vds_action, **safe_args)

        else:
            return f"[Error: Unknown tool '{tool_name}']"
