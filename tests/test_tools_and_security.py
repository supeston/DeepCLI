import asyncio
import base64
import io
import json
import os
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

import openpyxl
import pytest
from PIL import ExifTags, Image
from PIL.TiffImagePlugin import IFDRational

from deepx.agent.checkpoints import CheckpointManager, classify_dangerous_operation
from deepx.agent.repo_map import (
    build_repo_map,
    build_zero_turn_context,
    load_project_instructions,
)
from deepx.core.config import COMMON_FILE_TOOLS, STYLE_CONFIGS
from deepx.core.constants import PARALLEL_READ_ONLY_TOOLS
from deepx.tools.dadata_osint import DadataOSINTTool
from deepx.tools.funstat_osint import FunstatOSINTTool
from deepx.tools.manager import AgentTools
from deepx.tools.media_inspector import _dms_to_decimal, _format_bytes, _format_duration
from deepx.tools.terminal_session import (
    PtySessionManager,
    clean_ansi,
    detect_interactive_prompt,
)
from deepx.ui.status import SingleLineStatus, describe_tool_action
from deepx.ui.terminal import console


def _contains_emoji(text: str) -> bool:
    for ch in text:
        cp = ord(ch)
        if cp >= 0x1F000 or (0x2600 <= cp <= 0x27BF):
            return True
    return False


class _FakeTTYStream(io.StringIO):
    def isatty(self) -> bool:
        return True


class TestSingleLineStatus:
    def test_describe_tool_action_has_no_emojis(self):
        tools_samples = [
            ("read_file", {"path": "deepx/main.py"}),
            ("write_file", {"path": "app.py"}),
            ("edit_file", {"path": "app.py"}),
            ("grep_search", {"query": "foo", "path": "."}),
            ("run_cmd", {"command": "pytest -q"}),
            ("run_cmd", {"command": "echo ok"}),
            ("run_python", {"code": "print(1)"}),
            ("vds_deploy", {"action": "quick_deploy"}),
            ("make_docx", {"path": "out.docx"}),
            ("inspect_media", {"path": "photo.jpg"}),
            ("dadata_osint", {"action": "party"}),
        ]
        for tname, args in tools_samples:
            label = describe_tool_action(tname, args)
            assert label
            assert not _contains_emoji(label), f"Emoji in {label!r}"

    def test_tty_in_place_overwrite_and_clear(self):
        stream = _FakeTTYStream()
        status = SingleLineStatus(stream=stream)
        status.start("Читаю main.py...")
        status.update("Правлю parser.py...")
        status.clear()

        raw = stream.getvalue()
        assert "\n" not in raw
        assert raw.count("\r\x1b[2K") == 3
        assert "Читаю main.py..." in raw
        assert "Правлю parser.py..." in raw
        assert "s)" in raw
        assert not _contains_emoji(raw)

    def test_non_tty_deduplicates_identical_updates(self):
        stream = io.StringIO()
        status = SingleLineStatus(stream=stream)
        status.start("Читаю a.py...")
        status.update("Читаю a.py...")
        status.update("Правлю b.py...")
        status.clear()
        lines = [ln for ln in stream.getvalue().splitlines() if ln.strip()]
        assert lines == ["[*] Читаю a.py...", "[*] Правлю b.py..."]


class TestTodoAndDocumentsEscaping:
    def test_todo_and_render_plan_escape_rich_brackets(self, tmp_path):
        tools = AgentTools(cwd=str(tmp_path), browser_headless=True)
        with console.capture() as cap:
            res = tools.todo(
                "set",
                {"items": ["Проверить [TAG] и [/red] в тексте", "Обычный [0] шаг"]},
            )
            tools.flush_todos()
            plan_res = tools.render_plan(
                title="План [PHASE-1][/bold]",
                steps=[
                    {"text": "Шаг [1] с [/red] тегом", "status": "done"},
                    "Строка [beta] в скобках",
                ],
            )
        rendered = cap.get()
        assert "[Task" in res or "Task list" in res
        assert "[Success:" in plan_res
        assert "[TAG]" in rendered
        assert "[/red]" in rendered
        assert "[PHASE-1]" in rendered

    def test_make_excel_supports_dicts_lists_and_json_string(self, tmp_path):
        tools = AgentTools(cwd=str(tmp_path), browser_headless=True)
        out = tmp_path / "report.xlsx"
        res = tools.make_excel(
            "report.xlsx",
            {
                "Users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
                "Config": {"env": "prod", "workers": 4},
                "Matrix": [["A", "B"], [10, 20]],
            },
        )
        assert res.startswith("[Success:")
        assert out.is_file()
        wb = openpyxl.load_workbook(out)
        assert wb.sheetnames == ["Users", "Config", "Matrix"]
        assert list(wb["Users"].iter_rows(values_only=True)) == [
            ("id", "name"),
            (1, "Alice"),
            (2, "Bob"),
        ]
        assert list(wb["Config"].iter_rows(values_only=True)) == [
            ("Параметр", "Значение"),
            ("env", "prod"),
            ("workers", "4"),
        ]

    def test_make_docx_and_pptx_with_triple_quotes_and_strings(self, tmp_path):
        tools = AgentTools(cwd=str(tmp_path), browser_headless=True)
        docx_res = tools.make_docx(
            "docs/spec.docx",
            title='Отчёт """special"""',
            paragraphs='Строка с """кавычками""" и \\n текстом',
        )
        assert docx_res.startswith("[Success:")
        assert (tmp_path / "docs" / "spec.docx").is_file()

        pptx_res = tools.make_pptx(
            "docs/deck.pptx",
            title='Презентация """Test"""',
            slides=[
                {"title": "Слайд 1", "content": 'Пункт A\nПункт B """quoted"""'},
                "Слайд строкой",
            ],
        )
        assert pptx_res.startswith("[Success:")
        assert (tmp_path / "docs" / "deck.pptx").is_file()


class TestFileSystemRepoMapAndCheckpoints:
    def test_write_file_preserves_double_asterisks_and_runs_syntax_check(self, tmp_path):
        tools = AgentTools(cwd=str(tmp_path), browser_headless=True)
        md_text = "В Markdown **name** и __name__ остаются как есть.\n"
        res_md = tools.write_file("README.md", md_text)
        assert res_md.startswith("[Success:")
        assert (tmp_path / "README.md").read_text(encoding="utf-8") == md_text

        bad_py = "def broken(x):\n    return x +\n"
        res_bad = tools.write_file("bad.py", bad_py)
        assert "Syntax" in res_bad or "syntax" in res_bad
        assert "line" in res_bad.lower()

        good_py = "def add(a, b):\n    return a + b\n"
        res_good = tools.write_file("good.py", good_py)
        assert res_good.startswith("[Success:")
        assert "[Syntax Check: OK]" in res_good

        res_json = tools.write_file("broken.json", '{"a": 1, }')
        assert "Syntax Check Failed" in res_json

    def test_edit_file_checks_ambiguity_and_whitespace_target(self, tmp_path):
        tools = AgentTools(cwd=str(tmp_path), browser_headless=True)
        tools.write_file("dup.py", "x = 1\ny = 2\nx = 1\n")
        res_blank = tools.edit_file("dup.py", "   \n", "z = 3")
        assert res_blank.startswith("[Error:")

        res_ambig = tools.edit_file("dup.py", "x = 1", "x = 99")
        assert "2 times" in res_ambig or "ambiguous" in res_ambig.lower()

        tools.write_file("unique.py", "def f():\n    return 1\n")
        res_ok = tools.edit_file("unique.py", "return 1", "return 42")
        assert res_ok.startswith("[Success:")
        assert "return 42" in (tmp_path / "unique.py").read_text(encoding="utf-8")

    def test_grep_search_finds_matches_and_skips_ignored_dirs(self, tmp_path):
        (tmp_path / ".venv" / "lib").mkdir(parents=True)
        (tmp_path / ".venv" / "lib" / "noise.py").write_text("TARGET_TOKEN = 1\n", encoding="utf-8")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("def hello():\n    TARGET_TOKEN = 2\n", encoding="utf-8")
        (tmp_path / "src" / "notes.txt").write_text("TARGET_TOKEN in txt\n", encoding="utf-8")

        tools = AgentTools(cwd=str(tmp_path), browser_headless=True)
        res = tools.grep_search("TARGET_TOKEN", path=".", include="*.py")
        assert "src/main.py:2" in res
        assert "noise.py" not in res
        assert "notes.txt" not in res
        res_exec = asyncio.run(tools.execute_tool("grep_search", {"pattern": "TARGET_TOKEN", "path": "."}))
        assert "src/main.py:2" in res_exec

    def test_zip_pack_checks_protected_first_and_keeps_relative_paths(self, tmp_path):
        app_root = Path(__file__).resolve().parents[1]
        tools = AgentTools(cwd=str(tmp_path), browser_headless=True)
        tools.protect_self = True
        denied_dir = tmp_path / "never_created_zip_dir"
        denied = tools.zip_pack(
            str(denied_dir / "should_fail.zip"),
            [str(app_root / "deepx" / "core" / ".env")],
        )
        assert "Access denied" in denied
        assert not denied_dir.exists()

        sub1 = tmp_path / "pkg" / "a"
        sub2 = tmp_path / "pkg" / "b"
        sub1.mkdir(parents=True)
        sub2.mkdir(parents=True)
        (sub1 / "same.txt").write_text("from a", encoding="utf-8")
        (sub2 / "same.txt").write_text("from b", encoding="utf-8")

        pack_res = tools.zip_pack("bundle.zip", ["pkg"])
        assert pack_res.startswith("[Success:")
        with zipfile.ZipFile(tmp_path / "bundle.zip", "r") as zf:
            names = sorted(n.replace("\\", "/") for n in zf.namelist())
        assert "pkg/a/same.txt" in names
        assert "pkg/b/same.txt" in names
        assert len(names) == 2

    def test_checkpoints_undo_restores_modified_and_deletes_created(self, tmp_path):
        tools = AgentTools(cwd=str(tmp_path), browser_headless=True)
        (tmp_path / "existing.py").write_text("v = 1\n", encoding="utf-8")

        tools.checkpoints.begin_turn("turn1")
        tools.write_file("existing.py", "v = 2\n")
        tools.write_file("created.py", "new_var = True\n")
        tools.checkpoints.end_turn()

        assert (tmp_path / "existing.py").read_text(encoding="utf-8") == "v = 2\n"
        assert (tmp_path / "created.py").is_file()

        ok, msg = tools.checkpoints.undo_last()
        assert ok is True
        assert (tmp_path / "existing.py").read_text(encoding="utf-8") == "v = 1\n"
        assert not (tmp_path / "created.py").exists()
        assert "Восстановлены" in msg
        assert "created.py" in msg

    def test_dangerous_operation_classifier(self, tmp_path):
        ws = str(tmp_path)
        assert classify_dangerous_operation("write_file", {"path": "src/a.py"}, ws) is None
        assert classify_dangerous_operation("run_cmd", {"command": "pytest -v"}, ws) is None
        assert classify_dangerous_operation("run_cmd", {"command": "rm -rf build/"}, ws) is not None
        assert classify_dangerous_operation("run_python", {"code": "import shutil; shutil.rmtree('x')"}, ws) is not None
        assert classify_dangerous_operation("vds_deploy", {"action": "exec", "host": "1.2.3.4"}, ws) is not None
        assert classify_dangerous_operation("vds_deploy", {"action": "list_profiles"}, ws) is None
        assert classify_dangerous_operation("write_file", {"path": "C:/outside_dir/file.txt"}, ws) is not None

    def test_repo_map_and_project_instructions(self, tmp_path):
        (tmp_path / "DEEPX.md").write_text("Всегда используй pytest.", encoding="utf-8")
        (tmp_path / ".venv" / "site").mkdir(parents=True)
        (tmp_path / ".venv" / "site" / "hidden.py").write_text("def skip_me(): pass\n", encoding="utf-8")
        (tmp_path / "app.py").write_text(
            "class Service:\n    def run(self, port):\n        pass\n\ndef main():\n    pass\n",
            encoding="utf-8",
        )
        instr = load_project_instructions(str(tmp_path))
        assert "DEEPX.md" in instr
        assert "pytest" in instr
        rmap = build_repo_map(str(tmp_path))
        assert "app.py" in rmap
        assert "class Service" in rmap
        assert "def main()" in rmap
        assert "hidden.py" not in rmap
        zero = build_zero_turn_context(str(tmp_path))
        assert "[PROJECT INSTRUCTIONS]" in zero
        assert "[REPOSITORY MAP]" in zero


class TestMediaInspectorAndTerminal:
    def test_media_inspector_handles_ifdrational_exif_and_cover_art_audio(self, tmp_path, monkeypatch):
        assert _format_bytes(10 * 1024 ** 4) == "10.00 TB"
        assert _format_duration(65) == "01:05.00 (65.00s)"
        lat = _dms_to_decimal((IFDRational(55, 1), IFDRational(45, 1), IFDRational(20, 1)), "N")
        assert lat is not None and abs(lat - 55.755556) < 1e-4

        img_path = tmp_path / "photo.jpg"
        im = Image.new("RGB", (120, 80), color=(20, 40, 60))
        exif = im.getexif()
        exif[ExifTags.Base.Make] = "TestCam"
        exif[ExifTags.Base.ExposureTime] = IFDRational(1, 250)
        exif[ExifTags.Base.FNumber] = IFDRational(28, 10)
        exif[ExifTags.Base.FocalLength] = IFDRational(35, 1)
        im.save(img_path, exif=exif)

        tools = AgentTools(cwd=str(tmp_path), browser_headless=True)
        report = tools.inspect_media("photo.jpg")
        assert "120 x 80" in report
        assert "1/250s" in report
        assert "f/2.8" in report
        assert "35.0 mm" in report
        assert not _contains_emoji(report)

        # Mock ffprobe audio with attached_pic album cover stream
        audio_file = tmp_path / "track.flac"
        audio_file.write_bytes(b"fLaCmock")
        monkeypatch.setattr(
            tools,
            "_run_ffprobe",
            lambda abs_p: {
                "format": {"format_name": "flac", "duration": "125.5", "size": "1048576", "bit_rate": "900000", "tags": {"artist": "A", "title": "T"}},
                "streams": [
                    {"codec_type": "audio", "codec_name": "flac", "sample_rate": "44100", "channels": 2, "bits_per_raw_sample": "24"},
                    {"codec_type": "video", "codec_name": "mjpeg", "width": 600, "height": 600, "disposition": {"attached_pic": 1}},
                ],
                "chapters": [],
            },
        )
        audio_rep = tools.inspect_media("track.flac")
        assert "Audio Stream #1" in audio_rep
        assert "24-bit" in audio_rep
        assert "Album Cover" in audio_rep or "cover" in audio_rep.lower()
        assert "Video Stream" not in audio_rep
        assert not _contains_emoji(audio_rep)

    def test_terminal_session_ansi_prompt_detection_and_conpty_utf8(self, tmp_path):
        assert clean_ansi("\x1b]0;Window Title\x07\x1b[32mHello\x1b[0m") == "Hello"
        assert detect_interactive_prompt("C:\\Users\\home>")[0] is False
        assert detect_interactive_prompt("Status: OK:")[0] is False
        assert detect_interactive_prompt("Continue? [y/N]:")[0] is True
        assert detect_interactive_prompt("Enter password:")[0] is True

        mgr = PtySessionManager()
        try:
            sess, err = mgr.spawn("echo Привет Мир", cwd=str(tmp_path))
            assert err is None and sess is not None
            out = mgr.read_session_loop(sess, max_duration=10.0)
        finally:
            mgr.close_all()
        assert "Привет Мир" in out

    def test_system_capture_stream_decodes_split_utf8_and_kills_bg(self, tmp_path):
        tools = AgentTools(cwd=str(tmp_path), browser_headless=True)

        class _SplitReader:
            def __init__(self, chunks):
                self._chunks = list(chunks)

            async def read(self, _n):
                return self._chunks.pop(0) if self._chunks else b""

        # Cyrillic "П" is b"\xd0\x9f" split across two reads
        tools.active_tasks["bg1"] = {"log": ""}
        asyncio.run(
            tools._capture_background_stream(
                "bg1",
                _SplitReader([b"\xd0", b"\x9f\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82\n"]),
                "STDOUT",
            )
        )
        assert "Привет" in tools.active_tasks["bg1"]["log"]
        assert "\ufffd" not in tools.active_tasks["bg1"]["log"]

        # Sync task_status & task_log work cleanly via execute_tool
        async def _test_bg_exec():
            tools.active_tasks["bg2"] = {
                "cmd": "python -m http.server",
                "status": "RUNNING",
                "log": "started",
                "proc": MagicMock(returncode=None, terminate=MagicMock(), kill=MagicMock(), wait=asyncio.coroutine(lambda: 0) if hasattr(asyncio, "coroutine") else None),
            }
            async def _wait_zero():
                return 0
            tools.active_tasks["bg2"]["proc"].wait = _wait_zero
            st = await tools.execute_tool("task_status", {"id": "bg2"})
            lg = await tools.execute_tool("task_log", {"id": "bg2"})
            kr = await tools.execute_tool("kill_background_cmd", {"id": "bg2"})
            return st, lg, kr

        st, lg, kr = asyncio.run(_test_bg_exec())
        assert "status: running" in st.lower()
        assert "started" in lg
        assert "killed" in kr.lower() or "stopped" in kr.lower() or "завершена" in kr.lower() or "task" in kr.lower()


class TestSecurityVDSAndOSINT:
    def test_protect_self_blocks_env_browser_dadata_runpython_and_osinter(self, tmp_path):
        tools = AgentTools(cwd=str(tmp_path), browser_headless=True)
        tools.protect_self = True

        # 1. osinter profile has no vds_deploy
        assert "vds_deploy" not in COMMON_FILE_TOOLS
        assert "vds_deploy" not in STYLE_CONFIGS["osinter"]["tools"]

        # 2. child env scrubs DEEPX secrets
        os.environ["DEEPSEEK_API_KEY"] = "secret_dummy_value"
        try:
            env = tools._build_child_env()
            assert "DEEPSEEK_API_KEY" not in env
            assert "FUNSTAT_API_TOKEN" not in env
        finally:
            os.environ.pop("DEEPSEEK_API_KEY", None)

        # 3. run_python audit sandbox blocks reading protected deepx/.env via obfuscated string
        app_root = Path(__file__).resolve().parents[1]
        res_py = asyncio.run(
            tools.execute_tool(
                "run_python",
                {
                    "code": (
                        f"import os; p = os.path.join(r'{app_root}', 'deepx', 'core', '.' + 'env')\n"
                        "print(open(p).read())"
                    )
                },
            )
        )
        assert "PermissionError" in res_py or "Access denied" in res_py or "Traceback" in res_py

        # 3b. run_python imports workspace modules from cwd cleanly under protect_self=True
        (tmp_path / "local_mod.py").write_text("VALUE = 42\n", encoding="utf-8")
        res_ws_py = asyncio.run(
            tools.execute_tool(
                "run_python",
                {"code": "import local_mod; print('WS_VAL=' + str(local_mod.VALUE))"},
            )
        )
        assert "WS_VAL=42" in res_ws_py

        # 4. browser blocks file:// URLs to protected files & local protected uploads/screenshots
        res_nav = asyncio.run(
            tools.execute_tool(
                "browser_action",
                {"action": "navigate", "url": (app_root / ".env").as_uri()},
            )
        )
        assert "Access denied" in res_nav

        res_shot = asyncio.run(
            tools.execute_tool(
                "browser_action",
                {"action": "screenshot", "path": str(app_root / "deepx" / "agent" / "evil.png")},
            )
        )
        assert "Access denied" in res_shot

        # 5. browser_stealth_report exists and runs cleanly when closed in same loop
        async def _check_stealth():
            try:
                return await tools.browser_stealth_report()
            finally:
                await tools.close_browser()

        stealth = asyncio.run(_check_stealth())
        assert isinstance(stealth, dict)
        assert stealth["basic_check"] in ("pass", "warn")
        assert "signals" in stealth
        assert "status" in stealth

        # 6. dadata_osint logo_by_domain blocks protected directory
        res_dd = asyncio.run(
            tools.execute_tool(
                "dadata_osint",
                {"action": "logo_by_domain", "query": "sber.ru", "output_dir": str(app_root / "deepx" / "core")},
            )
        )
        assert "Access denied" in res_dd or "DADATA_API_KEY" in res_dd

        # Direct Dadata unit test with fake key verifies protected_checker specifically
        dd = DadataOSINTTool(api_key="real_test_key_123")
        assert DadataOSINTTool._is_placeholder("your_api_key_here") is True
        assert DadataOSINTTool._is_placeholder("<insert>") is True
        dd_res = asyncio.run(
            dd.run(
                "logo_by_domain",
                query="sber.ru",
                output_dir=str(tmp_path / "deepx" / "core"),
                protected_checker=lambda p: "deepx" in str(p).lower(),
            )
        )
        assert "Access denied" in dd_res

        # 7. funstat paid guard & emoji-free output
        fs = FunstatOSINTTool(token="dummy")
        paid_block = asyncio.run(fs.run(action="free_scan", username="durov", allow_paid=False))
        assert "allow_paid=false" in paid_block.lower() or "paid" in paid_block.lower()
        assert "💠" not in (app_root / "deepx" / "tools" / "funstat_osint.py").read_text(encoding="utf-8")

    def test_plan_mode_blocks_mutating_tools(self, tmp_path):
        tools = AgentTools(cwd=str(tmp_path), browser_headless=True)
        tools.plan_mode = True
        tools.write_file  # exists
        res_w = asyncio.run(tools.execute_tool("write_file", {"path": "x.txt", "content": "hi"}))
        res_c = asyncio.run(tools.execute_tool("run_cmd", {"command": "echo hi"}))
        res_r = asyncio.run(tools.execute_tool("list_dir", {"path": "."}))
        assert "Plan" in res_w
        assert "Plan" in res_c
        assert "Plan" not in res_r

    def test_vds_fixes_octal_sudo_start_line_exclude_and_self_kwarg(self, tmp_path, monkeypatch):
        tools = AgentTools(cwd=str(tmp_path), browser_headless=True)

        # Fake SSH client + SFTP
        executed_cmds = []
        sftp_mkdirs = []
        sftp_puts = []
        sftp_chmods = []

        class _FakeFile:
            def __init__(self, written=None):
                self._buf = written if written is not None else []
            def write(self, data):
                self._buf.append(data)
            def read(self):
                return b""
            def close(self):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *a):
                pass

        class _FakeSFTP:
            def stat(self, path):
                raise FileNotFoundError(path)
            def mkdir(self, path):
                sftp_mkdirs.append(path)
            def file(self, path, mode="r"):
                return _FakeFile()
            def open(self, path, mode="r"):
                return _FakeFile()
            def chmod(self, path, mode):
                sftp_chmods.append((path, mode))
            def getfo(self, remote_p, buf):
                buf.write(b"line1\nline2\n")
            def putfo(self, fileobj, remote_p):
                data = fileobj.read()
                sftp_puts.append(("<putfo>", remote_p, len(data)))
            def put(self, local_p, remote_p):
                sftp_puts.append((local_p.replace("\\", "/"), remote_p))

        class _Channel:
            def recv_exit_status(self):
                return 0

        class _Stdout:
            def __init__(self, text):
                self.channel = _Channel()
                self._text = text
            def read(self):
                return self._text.encode("utf-8")

        fake_sftp = _FakeSFTP()

        class _FakeSSH:
            def exec_command(self, cmd, timeout=None, get_pty=False):
                executed_cmds.append((cmd, get_pty))
                if "sed -n" in cmd:
                    return (_FakeFile(), _Stdout("line1\n"), _Stdout(""))
                return (_FakeFile(), _Stdout("OK"), _Stdout(""))
            def open_sftp(self):
                return fake_sftp

        monkeypatch.setattr(tools.vds_pool, "get_client", lambda *a, **kw: (_FakeSSH(), None))
        monkeypatch.setattr(tools.vds_pool, "get_sftp", lambda *a, **kw: (fake_sftp, None))

        # 1. Passing "self" in args must not throw TypeError: multiple values for 'self'
        res_self = asyncio.run(
            tools.execute_tool(
                "vds_deploy",
                {"action": "write_file", "self": "sneaky", "host": "1.2.3.4", "password": "pw", "remote_path": "/tmp/a.conf", "content": "hi", "mode": "644"},
                allowed_tools=["vds_deploy"],
            )
        )
        assert not res_self.startswith("[Error executing")
        assert sftp_chmods[-1] == ("/tmp/a.conf", 0o644)

        # 2. _vds_service must NOT double sudo
        tools._vds_service("1.2.3.4", 22, "ubuntu", "pw", None, None, None, 15, {"service": "nginx", "operation": "restart", "sudo": True})
        svc_cmd, _ = executed_cmds[-1]
        assert svc_cmd.count("sudo") == 1

        # 3. _vds_read_file clamps start_line=0 -> 1
        read_out = tools._vds_read_file("1.2.3.4", 22, "root", "pw", None, None, None, 15, {"remote_path": "/tmp/a.conf", "start_line": 0, "end_line": 1})
        assert "showing 1-1)" in read_out
        assert "1: line1" in read_out
        assert "line2" not in read_out

        # 4. _vds_upload prunes .venv and custom exclude via dirs[:]
        proj = tmp_path / "proj"
        (proj / ".venv").mkdir(parents=True)
        (proj / ".venv" / "junk.py").write_text("x", encoding="utf-8")
        (proj / "custom_skip").mkdir()
        (proj / "custom_skip" / "s.py").write_text("x", encoding="utf-8")
        (proj / "app").mkdir()
        (proj / "app" / "main.py").write_text("print(1)", encoding="utf-8")
        sftp_puts.clear()
        tools._vds_upload("1.2.3.4", 22, "root", "pw", None, None, None, 15, {"local_path": "proj", "remote_path": "/srv/proj", "exclude": ["custom_skip"]})
        uploaded_names = [item[0] for item in sftp_puts]
        assert any(p.endswith("app/main.py") for p in uploaded_names)
        assert not any("junk.py" in p for p in uploaded_names)
        assert not any("custom_skip" in p for p in uploaded_names)

        # 5. _vds_script with sudo=True passes get_pty=True and sudo -S -p ''
        tools._vds_script("1.2.3.4", 22, "ubuntu", "secretpw", None, None, None, 15, {"script": "whoami", "sudo": True})
        script_cmd, script_pty = executed_cmds[-1]
        assert script_pty is True
        assert "sudo -S -p ''" in script_cmd

        # 6. _vds_quick_deploy stops cleanly if step fails
        monkeypatch.setattr(tools, "_vds_upload", lambda *a, **kw: "[Error: upload failed]")
        qd_res = tools._vds_quick_deploy("1.2.3.4", 22, "root", "pw", None, None, None, 15, {"local_path": "proj", "remote_path": "/srv/proj"})
        assert "upload failed" in qd_res
        assert "Successfully" not in qd_res
