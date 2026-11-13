import asyncio
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from prompt_toolkit.document import Document

from deepx.agent.completer import SlashCommandCompleter
from deepx.agent.prompts import (
    build_agent_system_prompt,
    build_compacted_session_seed,
    compact_conversation_history,
)
from deepx.agent.runner import (
    DeepCLIApp,
    _extract_waiting_for_input,
    _normalize_mode_name,
    _summarize_tool_error,
)
from deepx.core.config import COMMANDS_DICT
from deepx.install import perform_health_check


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _contains_emoji(text: str) -> bool:
    for ch in text:
        cp = ord(ch)
        if cp >= 0x1F000 or (0x2600 <= cp <= 0x27BF):
            return True
    return False


class _ScriptedFakeAPI:
    """Async streaming fake DeepAPI for deterministic multi-step runner tests."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.prompts_sent = []
        self.mode_calls = []
        self.deepthink_calls = []
        self.search_calls = []
        self.new_chat_calls = 0

    async def new_chat(self):
        self.new_chat_calls += 1

    async def set_mode(self, mode: str):
        self.mode_calls.append(mode)

    async def set_deepthink(self, enable: bool):
        self.deepthink_calls.append(bool(enable))

    async def set_search(self, enable: bool):
        self.search_calls.append(bool(enable))

    async def send_message(self, prompt: str, stream: bool = False):
        self.prompts_sent.append(prompt)
        if not self.responses:
            async def _empty():
                if False:
                    yield ""
            return _empty()
        nxt = self.responses.pop(0)
        if isinstance(nxt, BaseException):
            raise nxt
        if callable(nxt):
            nxt = nxt(prompt)
        chunks = list(nxt) if isinstance(nxt, list) else [nxt]

        async def _gen():
            acc = ""
            for chunk in chunks:
                if isinstance(chunk, dict):
                    yield chunk
                else:
                    acc += str(chunk)
                    yield {"think": "", "answer": acc}

        return _gen()


class TestPromptsAndHealth:
    def test_system_prompts_fixed_and_plan_mode(self):
        nothink = (PROJECT_ROOT / "deepx" / "core" / "system_prompt_nothink.txt").read_text(encoding="utf-8")
        assert '"""' in nothink

        prompt = build_agent_system_prompt(
            "coder",
            think=True,
            workspace="C:/work",
            repo_context="Workspace: C:/work\n- app.py: def main()",
            plan_mode=True,
        )
        assert "[REPOSITORY AST MAP]" in prompt or "app.py" in prompt
        assert "PLAN MODE" in prompt.upper() or "PLAN" in prompt.upper()

    def test_compaction_keeps_recent_steps_full_and_folds_older(self):
        steps = [
            {"tool": "read_file", "output": "X" * 3000},
            {"tool": "grep_search", "output": "Y" * 2500},
            {"tool": "read_file", "output": "recent_1_" + ("A" * 2000)},
            {"tool": "read_file", "output": "recent_2_" + ("B" * 2000)},
            {"tool": "read_file", "output": "recent_3_" + ("C" * 2000)},
            {"tool": "read_file", "output": "recent_4_" + ("D" * 2000)},
        ]
        compacted, folded, saved = compact_conversation_history(steps, keep_recent=4, fold_threshold=1200)
        assert folded == 2
        assert saved > 2000
        assert len(compacted[0]["output"]) < 1000
        assert len(compacted[1]["output"]) < 1000
        # Recent 4 untouched
        assert compacted[2]["output"] == steps[2]["output"]
        assert compacted[5]["output"] == steps[5]["output"]

        seed, s_folded, _ = build_compacted_session_seed(
            "SYS",
            [
                {"user": "u1", "assistant": "a1", "tool_outputs": ["Z" * 1500]},
                {"user": "u2", "assistant": "a2", "tool_outputs": ["small"]},
            ],
            todos=[{"status": "active", "text": "Finish tests"}],
            keep_recent=1,
        )
        assert s_folded == 1
        assert "[ТЕКУЩИЕ ЗАДАЧИ]:" in seed
        assert "Finish tests" in seed

    def test_slash_command_completer_subcommands(self):
        comp = SlashCommandCompleter(COMMANDS_DICT)
        mode_vals = [c.text for c in comp.get_completions(Document("/mode "), None)]
        style_vals = [c.text for c in comp.get_completions(Document("/style "), None)]
        assert "plan" in mode_vals and "think" in mode_vals and "instant" in mode_vals
        assert "coder" in style_vals

    def test_install_health_check_passes_in_venv(self):
        assert perform_health_check(Path(sys.executable)) is True


class TestRunnerHelpers:
    def test_mode_normalization(self):
        assert _normalize_mode_name("fast") == "instant"
        assert _normalize_mode_name("instant") == "instant"
        assert _normalize_mode_name("expert") == "think"
        assert _normalize_mode_name("think") == "think"
        assert _normalize_mode_name("plan") == "plan"
        assert _normalize_mode_name("unknown") is None

    def test_extract_waiting_for_input_nested_braces_and_siblings(self):
        meta = json.dumps({"status": "WAITING_FOR_INPUT", "id": "pty-1", "cmd": "python -c 'a {b} c'"})
        wfi, others = _extract_waiting_for_input([
            "tool 1 ok",
            f"[SYSTEM: Interactive prompt]\n[INFO]\n{meta}",
            "tool 3 ok",
        ])
        assert wfi is not None
        assert wfi["id"] == "pty-1"
        assert wfi["cmd"] == "python -c 'a {b} c'"
        assert others == ["tool 1 ok", "tool 3 ok"]

    def test_summarize_tool_error_limits_size(self):
        huge = "\n".join(f"line {i}" for i in range(100))
        short = _summarize_tool_error(huge, max_lines=5, max_chars=200)
        assert short.count("\n") <= 5
        assert len(short) <= 200

    def test_restart_in_windows_terminal_quotes_space_paths(self, monkeypatch):
        captured = {}

        def fake_popen(cmd, **kwargs):
            captured["cmd"] = cmd
            captured["kwargs"] = kwargs
            return SimpleNamespace(pid=1234)

        monkeypatch.setattr(subprocess, "Popen", fake_popen)
        app = DeepCLIApp(headless=True)
        app.restart_in_windows_terminal()
        cmd = captured["cmd"]
        assert cmd[:4] == ["wt.exe", "-w", "new", "--size"]
        assert "cmd.exe" in cmd
        idx = cmd.index("cmd.exe")
        assert cmd[idx + 1 : idx + 4] == ["/d", "/s", "/c"]
        inner = cmd[idx + 4]
        assert inner.startswith('"') and inner.endswith('"')
        assert "deep_cli.py" in inner


class TestDeepCLIAppIntegration:
    def test_modes_cd_compact_undo_preserves_history(self, tmp_path):
        ws = tmp_path / "test space proj"
        ws.mkdir()
        (ws / "DEEPX.md").write_text("Keep it crisp.", encoding="utf-8")
        (ws / "hello.py").write_text("VAL = 1\n", encoding="utf-8")

        app = DeepCLIApp(headless=True, cwd=str(ws), confirm_fn=lambda _reason: True)
        api = _ScriptedFakeAPI([])
        app.turn_history = [
            {"user": "step 1", "assistant": "done 1", "tool_outputs": ["D" * 1600]},
            {"user": "step 2", "assistant": "done 2", "tool_outputs": ["ok"]},
        ]

        # /mode plan preserves history & toggles plan_mode
        assert asyncio.run(app.handle_command("/mode plan", api)) is True
        assert app.mode == "plan"
        assert app.tools.plan_mode is True
        assert len(app.turn_history) == 2
        assert api.new_chat_calls == 0

        # /mode instant disables think & exits plan mode without clearing turn_history
        assert asyncio.run(app.handle_command("/mode instant", api)) is True
        assert app.mode == "instant"
        assert app.think is False
        assert app.tools.plan_mode is False
        assert len(app.turn_history) == 2

        # /compact compresses older turns, stores pending seed, and resets API session
        assert asyncio.run(app.handle_command("/compact", api)) is True
        assert api.new_chat_calls == 1
        assert app.is_new_chat is False
        assert "[СЖАТАЯ ИСТОРИЯ ДИАЛОГА]:" in app._compacted_seed_pending

        # Checkpoint + /undo test
        app.tools.checkpoints.begin_turn("t")
        app.tools.write_file("hello.py", "VAL = 999\n")
        app.tools.checkpoints.end_turn()
        assert (ws / "hello.py").read_text(encoding="utf-8") == "VAL = 999\n"
        assert asyncio.run(app.handle_command("/undo", api)) is True
        assert (ws / "hello.py").read_text(encoding="utf-8") == "VAL = 1\n"

        # /cd test updates cwd, checkpoints, and repo context
        other = tmp_path / "second dir with spaces"
        other.mkdir()
        (other / "mod.py").write_text("def bar():\n    return 2\n", encoding="utf-8")
        assert asyncio.run(app.handle_command(f"/cd {other}", api)) is True
        assert Path(app.tools.cwd).resolve() == other.resolve()
        assert "def bar()" in app._pending_workspace_context

    def test_is_new_chat_not_reset_on_api_failure(self, tmp_path, monkeypatch):
        ws = tmp_path / "space proj"
        ws.mkdir()
        app = DeepCLIApp(headless=True, cwd=str(ws), confirm_fn=lambda _r: True)
        api = _ScriptedFakeAPI([RuntimeError("network down")] * 8)

        orig_sleep = asyncio.sleep

        async def _fast_sleep(_sec):
            await orig_sleep(0)

        monkeypatch.setattr(asyncio, "sleep", _fast_sleep)
        assert app.is_new_chat is True
        asyncio.run(app.process_query("Привет", api))
        assert app.is_new_chat is True

    def test_end_to_end_agent_turn_minimalist_no_json_or_emoji(self, tmp_path, capsys):
        ws = tmp_path / "project with spaces"
        ws.mkdir()
        (ws / "source.py").write_text("SECRET_GREETING = 'hi'\n", encoding="utf-8")

        api = _ScriptedFakeAPI([
            # Step 1: parallel read + grep
            [
                'Читаю файлы...\n```tool_call\n{"tool": "read_file", "path": "source.py"}\n```\n'
                '```tool_call\n{"tool": "list_dir", "path": "."}\n```'
            ],
            # Step 2: write target file
            [
                'Создаю скрипт...\n```tool_call\n'
                '{"tool": "write_file", "path": "greeter.py", "content": "def greet():\\n    return \'ok\'\\n"}'
                '\n```'
            ],
            # Step 3: closed-loop verification after mutating tool
            [
                '```tool_call\n{"tool": "run_python", "code": "import greeter; assert greeter.greet() == \'ok\'; print(\'VERIFIED\')"}\n```'
            ],
            # Step 4: final answer
            ["Файл `greeter.py` создан и проверен."],
        ])

        app = DeepCLIApp(headless=True, cwd=str(ws), confirm_fn=lambda _r: True)
        asyncio.run(app.process_query("Создай greeter.py на основе source.py", api))

        out = capsys.readouterr().out
        assert (ws / "greeter.py").is_file()
        assert app.is_new_chat is False
        assert len(app.turn_history) == 1
        # Zero raw tool JSON or read_file raw contents leaked to stdout
        assert '{"tool":' not in out
        assert "SECRET_GREETING" not in out
        assert "greeter.py" in out
        assert not _contains_emoji(out)

    def test_dangerous_operation_confirmation_denial_and_exception_handler_restore(self, tmp_path):
        ws = tmp_path / "danger ws"
        ws.mkdir()
        (ws / "keep.txt").write_text("important", encoding="utf-8")

        prompts_asked = []

        def deny_confirm(reason: str) -> bool:
            prompts_asked.append(reason)
            return False

        api = _ScriptedFakeAPI([
            ['```tool_call\n{"tool": "run_cmd", "command": "rm -rf keep.txt"}\n```'],
            ["Удаление отменено пользователем."],
        ])
        app = DeepCLIApp(headless=True, cwd=str(ws), confirm_fn=deny_confirm)

        async def _run_and_check_handler():
            loop = asyncio.get_running_loop()
            sentinel = lambda _loop, _ctx: None
            loop.set_exception_handler(sentinel)
            try:
                ok = await app.run_query_interruptible("Удали keep.txt", api)
                return ok, loop.get_exception_handler() is sentinel
            finally:
                loop.set_exception_handler(None)

        ok, restored = asyncio.run(_run_and_check_handler())
        assert ok is True
        assert restored is True
        assert len(prompts_asked) == 1
        assert (ws / "keep.txt").read_text(encoding="utf-8") == "important"

    def test_batch_strategy_change_triggered_on_error_then_ok(self, tmp_path):
        ws = tmp_path / "batch ws"
        ws.mkdir()
        api = _ScriptedFakeAPI([
            [
                '```tool_call\n{"tool": "read_file", "path": "missing_1.txt"}\n```\n'
                '```tool_call\n{"tool": "list_dir", "path": "."}\n```'
            ],
            [
                '```tool_call\n{"tool": "read_file", "path": "missing_1.txt"}\n```\n'
                '```tool_call\n{"tool": "list_dir", "path": "."}\n```'
            ],
            ["Завершил после смены подхода."],
        ])
        app = DeepCLIApp(headless=True, cwd=str(ws), confirm_fn=lambda _r: True)
        asyncio.run(app.process_query("Проверь missing_1.txt", api))
        assert len(api.prompts_sent) >= 3
        assert "Одинаковая ошибка повторилась" in api.prompts_sent[2]

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows ConPTY interactive TTY test")
    def test_live_conpty_tty_greeting_ctrl_x_and_ctrl_c(self, tmp_path):
        import time
        from winpty import PtyProcess

        ws = tmp_path / "pty space ws"
        ws.mkdir()
        fake_state = tmp_path / "fake_state.json"
        fake_state.write_text("{}", encoding="utf-8")

        child_code = f'''
import asyncio
import os
import sys
import warnings

warnings.simplefilter("error", RuntimeWarning)
sys.path.insert(0, {repr(str(PROJECT_ROOT))})

from deepx.ui.terminal import setup_windows_terminal
setup_windows_terminal()

import deepx.agent.runner as runner_mod

class _InteractiveFakeAPI:
    def __init__(self, state_file="", headless=True):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def new_chat(self):
        return True

    async def set_mode(self, mode):
        return True

    async def set_deepthink(self, enable):
        return True

    async def set_search(self, enable):
        return True

    async def stop_generation(self):
        return True

    async def send_message(self, prompt: str, stream: bool = False):
        if "медленно" in prompt:
            async def _slow():
                yield {{"think": "", "answer": "Начинаю "}}
                for i in range(40):
                    await asyncio.sleep(0.15)
                    yield {{"think": "", "answer": f"Начинаю шаг {{i}} "}}
            return _slow()

        async def _hello():
            await asyncio.sleep(0.05)
            yield {{"think": "", "answer": "Привет! "}}
            await asyncio.sleep(0.05)
            yield {{"think": "", "answer": "Привет! Чем помочь?"}}
        return _hello()

runner_mod.DeepAPI = _InteractiveFakeAPI
app = runner_mod.DeepCLIApp(state_file=sys.argv[1], headless=True, cwd=sys.argv[2])
asyncio.run(app.run())
'''
        script_path = tmp_path / "conpty_runner.py"
        script_path.write_text(child_code, encoding="utf-8")

        def _read_until(proc, needle: str, acc: list[str], timeout: float = 12.0) -> str:
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                joined = "".join(acc)
                if needle in joined:
                    return joined
                try:
                    chunk = proc.read(4096)
                    if chunk:
                        acc.append(chunk)
                        continue
                except EOFError:
                    break
                except Exception:
                    pass
                time.sleep(0.03)
            return "".join(acc)

        cmd = [sys.executable, "-W", "error::RuntimeWarning", str(script_path), str(fake_state), str(ws)]
        proc = PtyProcess.spawn(cmd, cwd=str(PROJECT_ROOT), dimensions=(35, 110))
        chunks: list[str] = []
        try:
            startup_out = _read_until(proc, "› ", chunks)
            assert "› " in startup_out

            idx_hello = len(chunks)
            proc.write("привет\r")
            _read_until(proc, "Чем помочь?", chunks)
            _read_until(proc, "› ", chunks, timeout=5.0)
            hello_seg = "".join(chunks[idx_hello:])
            assert "Чем помочь?" in hello_seg
            assert "Генерация остановлена" not in hello_seg

            idx_ctrl_x = len(chunks)
            proc.write("медленно\r")
            _read_until(proc, "Начинаю", chunks)
            time.sleep(0.15)
            proc.write("\x18")
            _read_until(proc, "Генерация остановлена", chunks)
            ctrl_x_seg = "".join(chunks[idx_ctrl_x:])
            assert "Генерация остановлена" in ctrl_x_seg

            time.sleep(0.25)
            idx_ctrl_c = len(chunks)
            proc.write("медленно\r")
            _read_until(proc, "Начинаю", chunks)
            time.sleep(0.15)
            proc.write("\x03")
            _read_until(proc, "Do you really want to exit?", chunks)
            assert "Do you really want to exit?" in "".join(chunks[idx_ctrl_c:])
            proc.write("y\r")

            deadline = time.monotonic() + 8.0
            while proc.isalive() and time.monotonic() < deadline:
                try:
                    c = proc.read(4096)
                    if c:
                        chunks.append(c)
                except EOFError:
                    break
                except Exception:
                    pass
                time.sleep(0.05)

            full_out = "".join(chunks)
            assert "Exiting DEEPX." in full_out
            assert "RuntimeWarning" not in full_out
            assert "Traceback" not in full_out
            assert proc.exitstatus == 0
        finally:
            if proc.isalive():
                proc.terminate(force=True)


def test_version_and_update_checks(tmp_path):
    from deepx.core.updater import check_for_updates
    from deepx.core.version import get_local_version, is_newer_version, parse_version

    assert parse_version("v3.1.2") == (3, 1, 2)
    assert is_newer_version("3.1.0", "3.0.0") is True
    assert is_newer_version("3.0.0", "3.0.0") is False
    assert is_newer_version("2.9.9", "3.0.0") is False

    (tmp_path / "VERSION").write_text("3.0.0\n", encoding="utf-8")
    assert get_local_version(tmp_path) == "3.0.0"

    cache_file = tmp_path / ".deepx" / "update_cache.json"

    info_raw = check_for_updates(
        force_refresh=True,
        project_root=tmp_path,
        cache_path=cache_file,
        fetch_text_fn=lambda url, _t: "3.1.0\n" if url.endswith("/VERSION") else None,
    )
    assert info_raw.has_update is True
    assert info_raw.latest_version == "3.1.0"
    assert info_raw.source == "raw"

    info_cached = check_for_updates(
        force_refresh=False,
        project_root=tmp_path,
        cache_path=cache_file,
        fetch_text_fn=lambda _u, _t: None,
    )
    assert info_cached.source == "cache"
    assert info_cached.has_update is True
    assert info_cached.latest_version == "3.1.0"

    info_release = check_for_updates(
        force_refresh=True,
        project_root=tmp_path,
        cache_path=cache_file,
        fetch_text_fn=lambda url, _t: '{"tag_name": "v3.2.0"}' if "releases" in url else None,
    )
    assert info_release.has_update is True
    assert info_release.latest_version == "3.2.0"
    assert info_release.source == "release"

    info_offline = check_for_updates(
        force_refresh=True,
        project_root=tmp_path,
        cache_path=cache_file,
        fetch_text_fn=lambda _u, _t: None,
    )
    assert info_offline.has_update is False
    assert info_offline.source == "offline"


def test_perform_self_update_preserves_user_files_and_blocks_zip_slip(tmp_path):
    import io
    import zipfile
    from deepx.core.updater import _extract_safe_zip, perform_self_update

    root = tmp_path / "repo"
    (root / "deepx" / "core").mkdir(parents=True)
    (root / ".deepx").mkdir(parents=True)
    (root / "VERSION").write_text("2.9.0\n", encoding="utf-8")
    (root / ".env").write_text("TOKEN=keep_secret\n", encoding="utf-8")
    (root / "deepx" / "core" / "state.json").write_text('{"keep": true}', encoding="utf-8")
    (root / ".deepx" / "vds_profiles.json").write_text('{"prod": {}}', encoding="utf-8")
    (root / "deepx" / "__init__.py").write_text("# old\n", encoding="utf-8")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("DeepCLI-main/VERSION", "3.0.0\n")
        zf.writestr("DeepCLI-main/deepx/__init__.py", "# updated\n")
        zf.writestr("DeepCLI-main/.env", "OVERWRITE_BAD\n")
        zf.writestr("DeepCLI-main/deepx/core/state.json", '{"overwrite": true}')
        zf.writestr("DeepCLI-main/.deepx/vds_profiles.json", "{}")
    zip_bytes = buf.getvalue()

    ok, msg = perform_self_update(
        project_root=root,
        fetch_text_fn=lambda url, _t: "3.0.0\n" if url.endswith("/VERSION") else None,
        download_bytes_fn=lambda _u, _t: zip_bytes,
        install_deps=False,
    )
    assert ok is True
    assert "3.0.0" in msg
    assert (root / "VERSION").read_text(encoding="utf-8").strip() == "3.0.0"
    assert (root / "deepx" / "__init__.py").read_text(encoding="utf-8") == "# updated\n"
    assert (root / ".env").read_text(encoding="utf-8") == "TOKEN=keep_secret\n"
    assert (root / "deepx" / "core" / "state.json").read_text(encoding="utf-8") == '{"keep": true}'
    assert (root / ".deepx" / "vds_profiles.json").read_text(encoding="utf-8") == '{"prod": {}}'

    evil_buf = io.BytesIO()
    with zipfile.ZipFile(evil_buf, "w") as zf:
        zf.writestr("../escape.txt", "boom")
    with pytest.raises(ValueError, match="Unsafe zip member"):
        _extract_safe_zip(evil_buf.getvalue(), tmp_path / "zip_out")


def test_render_banner_help_status_and_prompt_formatting(monkeypatch, tmp_path):
    from rich.console import Console
    import deepx.ui.banner as banner_mod
    from deepx.core.version import UpdateInfo

    def _capture(width, fn):
        cap = Console(record=True, width=width, force_terminal=False, color_system=None)
        monkeypatch.setattr(banner_mod, "console", cap)
        fn()
        return cap.export_text()

    update = UpdateInfo(
        current_version="3.0.0",
        latest_version="3.1.0",
        has_update=True,
        source="raw",
    )

    wide_out = _capture(
        100,
        lambda: banner_mod.render_banner(
            mode="think",
            style="coder",
            think=True,
            search=False,
            cwd=str(PROJECT_ROOT),
            update_info=update,
        ),
    )
    assert "██████╗" in wide_out
    assert "DeepSeek-V4.1-Flash" in wide_out
    assert "update to 3.1.0" in wide_out
    assert "/update" in wide_out
    assert not _contains_emoji(wide_out)

    narrow_out = _capture(48, lambda: banner_mod.render_banner(cwd=str(tmp_path), update_info=update))
    assert "DEEPX AGENT" in narrow_out
    assert "update to 3.1.0" in narrow_out
    assert not _contains_emoji(narrow_out)

    help_out = _capture(100, banner_mod.print_help)
    assert "/update" in help_out
    assert not _contains_emoji(help_out)

    status_out = _capture(
        100,
        lambda: banner_mod.print_status(
            "plan", "coder", True, True, str(tmp_path), str(tmp_path / "state.json"), update_info=update
        ),
    )
    assert "update to 3.1.0" in status_out
    assert "SESSION STATUS" in status_out
    assert not _contains_emoji(status_out)

    app = DeepCLIApp(cwd=str(tmp_path))
    assert "".join(text for _cls, text in app._build_prompt()) == "› "
    app.mode = "think"
    assert "".join(text for _cls, text in app._build_prompt()) == "[think] › "
    app.mode = "plan"
    assert "".join(text for _cls, text in app._build_prompt()) == "[plan] › "


def test_windows_launch_wt_handoff_gating(monkeypatch, tmp_path):
    from deepx.core import windows_launch as wl

    monkeypatch.delenv("DEEPX_NO_WT_RELAUNCH", raising=False)
    monkeypatch.setattr(wl, "is_standalone_classic_console", lambda: True)
    monkeypatch.setattr(wl, "find_windows_terminal", lambda: r"C:\Apps\wt.exe")
    monkeypatch.setattr(wl, "is_windows_11", lambda: False)

    assert wl.should_relaunch_in_windows_terminal([]) is True
    assert wl.should_relaunch_in_windows_terminal(["--headful"]) is True
    assert wl.should_relaunch_in_windows_terminal(["--version"]) is False
    assert wl.should_relaunch_in_windows_terminal(["--update"]) is False
    assert wl.should_relaunch_in_windows_terminal(["--install-cmd"]) is False
    assert wl.should_relaunch_in_windows_terminal(["--in-wt"]) is False
    assert wl.should_relaunch_in_windows_terminal(["--no-relaunch"]) is False

    space_dir = tmp_path / "dir with spaces"
    space_dir.mkdir()
    cmd = wl.build_wt_command(
        [str(space_dir / "python.exe"), "-u", "launcher.py"],
        cwd=str(space_dir),
        title="DEEPX LAUNCHER",
        wt_path=r"C:\Apps\wt.exe",
    )
    assert cmd[0] == r"C:\Apps\wt.exe"
    assert "--title" in cmd and "DEEPX LAUNCHER" in cmd
    assert "-d" in cmd and str(space_dir) in cmd
    assert cmd[-1] == "--in-wt"

    spawned = {}
    closed = {"count": 0}

    def fake_popen(popen_cmd, **kwargs):
        spawned["cmd"] = popen_cmd
        return SimpleNamespace(pid=4321)

    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    monkeypatch.setattr(wl, "close_classic_console_window", lambda: closed.__setitem__("count", closed["count"] + 1) or True)
    monkeypatch.setattr(sys, "platform", "win32")

    ok = wl.relaunch_in_windows_terminal(
        [str(space_dir / "python.exe"), "deepx/main.py"],
        cwd=str(space_dir),
        close_parent=True,
    )
    assert ok is True
    assert closed["count"] == 1
    assert "--in-wt" in spawned["cmd"]

    def broken_popen(*_a, **_kw):
        raise OSError("wt blocked")

    monkeypatch.setattr(subprocess, "Popen", broken_popen)
    assert wl.relaunch_in_windows_terminal(["python.exe"], cwd=str(space_dir)) is False


def test_install_and_uninstall_system_command(tmp_path):
    from deepx.core.windows_launch import (
        install_system_command,
        is_system_command_installed,
        uninstall_system_command,
    )

    app_root = tmp_path / "DeepX Space App"
    venv_bin = app_root / ".venv" / ("Scripts" if sys.platform == "win32" else "bin")
    venv_bin.mkdir(parents=True)
    py_name = "python.exe" if sys.platform == "win32" else "python"
    (venv_bin / py_name).write_text("", encoding="utf-8")

    bin_dir = tmp_path / "local bin"
    ok, _msg = install_system_command(project_root=app_root, bin_dir=bin_dir, update_registry=False)
    assert ok is True
    assert is_system_command_installed(project_root=app_root, bin_dir=bin_dir) is True

    cmd_text = (bin_dir / "deepx.cmd").read_text(encoding="utf-8")
    ps1_text = (bin_dir / "deepx.ps1").read_text(encoding="utf-8")
    assert str(app_root.resolve()) in cmd_text
    assert "--cwd" in cmd_text and "deepx.main" in cmd_text
    assert "deepx.main" in ps1_text and "--cwd" in ps1_text

    ok_rm, _msg_rm = uninstall_system_command(bin_dir=bin_dir, update_registry=False)
    assert ok_rm is True
    assert is_system_command_installed(project_root=app_root, bin_dir=bin_dir) is False


def test_launcher_renderable_distinct_banner_and_navigation(tmp_path):
    from rich.console import Console
    from deepx.core.version import UpdateInfo
    from deepx.launcher import LauncherSnapshot, build_launcher_renderable

    snap = LauncherSnapshot(
        local_version="3.1.0",
        update_info=UpdateInfo("3.1.0", "3.2.0", True, "raw"),
        venv_ready=True,
        cmd_installed=False,
        terminal_label="Windows Terminal (TrueColor)",
        wt_available=True,
        app_root=tmp_path,
        status_note="Dependencies verified",
    )

    cap = Console(record=True, width=100, force_terminal=False, color_system=None)
    cap.print(build_launcher_renderable(snap, selected_index=1, term_width=100))
    rendered = cap.export_text()

    assert "CONTROL HUB" in rendered
    assert "LAUNCHER EDITION" in rendered
    assert "update 3.2.0" in rendered
    assert "Launch DEEPX Agent" in rendered
    assert "Check & Install Updates" in rendered
    assert "Verify Dependencies" in rendered
    assert "Install 'deepx' Command" in rendered
    assert "Exit Launcher" in rendered
    assert "▸" in rendered
    assert "DeepSeek-V4.1-Flash" not in rendered
    assert not _contains_emoji(rendered)


def test_deep_api_close_bounded_timeout_and_terminal_helpers(monkeypatch):
    import time
    from deepx.api.deep_api import DeepAPI
    from deepx.ui.terminal import disable_quick_edit_mode, shutdown_child_processes

    class _HungBrowser:
        async def close(self):
            await asyncio.sleep(10)

    api = DeepAPI(headless=True)
    api.browser = _HungBrowser()

    started = time.monotonic()
    asyncio.run(api.close())
    elapsed = time.monotonic() - started
    assert elapsed < 3.0
    assert api.browser is None

    # Smoke-check Win32 input & child cleanup helpers never raise
    disable_quick_edit_mode()
    assert shutdown_child_processes(root_pid=99999999) == 0


def test_bootstrap_launcher_window_wt_and_fallback(monkeypatch, tmp_path):
    from deepx.core import windows_launch as wl

    app_root = tmp_path / "DeepX App"
    venv_bin = app_root / ".venv" / ("Scripts" if sys.platform == "win32" else "bin")
    venv_bin.mkdir(parents=True)
    py_name = "python.exe" if sys.platform == "win32" else "python"
    (venv_bin / py_name).write_text("", encoding="utf-8")
    (app_root / "deepx").mkdir(parents=True)
    (app_root / "deepx" / "launcher.py").write_text("# stub\n", encoding="utf-8")

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(wl, "cleanup_headless_wt_processes", lambda: 0)
    monkeypatch.setattr(wl, "find_windows_terminal", lambda: r"C:\Apps\wt.exe")

    spawned_calls = []

    def fake_popen(cmd, **kwargs):
        spawned_calls.append((cmd, kwargs))
        return SimpleNamespace(pid=9001)

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    # Case 1: WT opens a new visible window on the current desktop
    vis_seq = iter([[101], [101, 202]])
    monkeypatch.setattr(wl, "get_visible_wt_windows_on_current_desktop", lambda: next(vis_seq, [101, 202]))
    assert wl.bootstrap_launcher_window(project_root=app_root) is True
    assert len(spawned_calls) == 1
    assert spawned_calls[0][0][0] == r"C:\Apps\wt.exe"
    assert "--in-wt" in spawned_calls[0][0]

    # Case 2: WT spawns on a hidden/blocked desktop (no new visible window) -> falls back to CREATE_NEW_CONSOLE
    spawned_calls.clear()
    monkeypatch.setattr(wl, "get_visible_wt_windows_on_current_desktop", lambda: [])
    monkeypatch.setattr(wl.time, "sleep", lambda _s: None)
    clock = iter([0.0, 0.5, 1.5, 2.5])
    monkeypatch.setattr(wl.time, "monotonic", lambda: next(clock, 3.0))

    assert wl.bootstrap_launcher_window(project_root=app_root) is True
    assert len(spawned_calls) == 2
    fallback_cmd, fallback_kw = spawned_calls[1]
    assert "--no-relaunch" in fallback_cmd
    assert fallback_kw.get("creationflags", 0) == getattr(subprocess, "CREATE_NEW_CONSOLE", 0x00000010)

