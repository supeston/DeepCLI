import ast
from pathlib import Path

import pytest

from deepx.api.deep_api import DeepAPI, _separate_reasoning, _has_complete_tool_call
from deepx.parser.tool_parser import (
    extract_tool_calls,
    normalize_tool_args,
    normalize_tool_calls,
    parse_json_lenient,
)
from deepx.ui.markup import (
    StreamingMarkupRenderer,
    get_clean_text,
    render_terminal_markup,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestToolParser:
    def test_preserves_python_keywords_and_escapes_inside_strings(self):
        payload = """```tool_call
{
  "tool": "write_file",
  "path": "sample.py",
  "content": "flag = True\\nother = False\\nval = None\\nopts = {'a': 1}\\nprint('ok\\nnext')"
}
```"""
        calls = extract_tool_calls(payload)
        assert len(calls) == 1
        assert calls[0]["tool"] == "write_file"
        content = calls[0]["args"]["content"]
        assert "flag = True" in content
        assert "other = False" in content
        assert "val = None" in content
        assert "{'a': 1}" in content
        # Must stay Python True/False/None, never lowercased JSON true/false/null
        assert "true" not in content
        assert "false" not in content
        assert "null" not in content

    def test_triple_quoted_strings_and_nested_fences(self):
        payload = '''```tool_call
{"tool": "write_file", "path": "doc.md", "content": """# Header
```python
x = {"k": [1, 2], "flag": True}
```
Body with } unmatched brace"""}
```'''
        calls = extract_tool_calls(payload)
        assert len(calls) == 1
        args = calls[0]["args"]
        assert args["path"] == "doc.md"
        assert "```python" in args["content"]
        assert "unmatched brace" in args["content"]
        assert "x = {\"k\": [1, 2], \"flag\": True}" in args["content"]

    def test_unpaired_braces_inside_json_string(self):
        payload = '{"tool": "run_python", "code": "print(\\"hello { world\\")"}'
        calls = extract_tool_calls(payload)
        assert len(calls) == 1
        assert calls[0]["tool"] == "run_python"
        assert "{ world" in calls[0]["args"]["code"]

    def test_ignores_regular_code_blocks_and_prose_calls(self):
        prose = """
Вот пример YAML конфига:
```yaml
tool: my_custom_tool
path: config.yml
```

И пример Python:
```python
def demo():
    read_file("notes.txt")
    return write_file("a.txt", "b")
```

В обычном тексте не запускай read_file("README.md") и make_excel(foo="bar").
"""
        assert extract_tool_calls(prose) == []

    def test_parses_explicit_json_and_xml_tool_calls(self):
        xml_payload = '<tool_call>{"tool": "grep_search", "query": "def main", "path": "deepx"}</tool_call>'
        calls = extract_tool_calls(xml_payload)
        assert len(calls) == 1
        assert calls[0]["tool"] == "grep_search"
        assert calls[0]["args"]["query"] == "def main"

    def test_clipboard_limit_not_overwritten_as_end_line(self):
        norm_clip = normalize_tool_args({"limit": 5}, "get_clipboard_history")
        assert norm_clip["limit"] == 5
        assert "end_line" not in norm_clip

        norm_read = normalize_tool_args({"path": "a.py", "limit": 25}, "read_file")
        assert norm_read["end_line"] == 25

    def test_non_adjacent_read_file_calls_are_not_merged(self):
        raw_calls = [
            {"tool": "read_file", "args": {"path": "runner.py", "start_line": 1, "end_line": 30}},
            {"tool": "read_file", "args": {"path": "runner.py", "start_line": 200, "end_line": 240}},
        ]
        normalized = normalize_tool_calls(raw_calls)
        assert len(normalized) == 2
        assert normalized[0]["args"]["start_line"] == 1
        assert normalized[0]["args"]["end_line"] == 30
        assert normalized[1]["args"]["start_line"] == 200
        assert normalized[1]["args"]["end_line"] == 240

    def test_adjacent_read_file_calls_merge(self):
        raw_calls = [
            {"tool": "read_file", "args": {"path": "runner.py", "start_line": 1, "end_line": 30}},
            {"tool": "read_file", "args": {"path": "runner.py", "start_line": 31, "end_line": 60}},
        ]
        normalized = normalize_tool_calls(raw_calls)
        assert len(normalized) == 1
        assert normalized[0]["args"]["start_line"] == 1
        assert normalized[0]["args"]["end_line"] == 60

    def test_parse_json_lenient_handles_trailing_commas(self):
        parsed = parse_json_lenient('{"a": 1, "b": [2, 3,],}')
        assert parsed == {"a": 1, "b": [2, 3]}


class TestDeepApiHelpers:
    def test_image_path_regex_matches_only_images(self):
        text = r"Смотри [C:\Users\home\pic.png], [/tmp/photo.jpeg], но не трогай [C:\Users\home\main.py] и [/etc/hosts]"
        matches = DeepAPI._IMAGE_PATH_RE.findall(text)
        assert matches == [r"C:\Users\home\pic.png", "/tmp/photo.jpeg"]
        cleaned = DeepAPI._IMAGE_PATH_RE.sub("", text)
        assert r"[C:\Users\home\main.py]" in cleaned
        assert "[/etc/hosts]" in cleaned

    def test_separate_reasoning_and_tool_completeness(self):
        think, answer = _separate_reasoning("мысли тут", "Готовый ответ")
        assert think == "мысли тут"
        assert answer == "Готовый ответ"
        assert _has_complete_tool_call('```tool_call\n{"tool": "list_dir"}\n```') is True
        assert _has_complete_tool_call('<tool_call>{"tool": "read_file", "path": "x.py"}</tool_call>') is True
        assert _has_complete_tool_call('```tool_call\n{"tool": "read_file"') is False
        assert _has_complete_tool_call("Обычный текст без инструментов") is False


class TestMarkupAndStreaming:
    def test_no_duplicate_stable_stream_class_in_markup_module(self):
        src = (PROJECT_ROOT / "deepx" / "ui" / "markup.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        class_names = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]
        assert class_names.count("StableStreamText") == 1
        assert class_names.count("StreamingMarkupRenderer") == 1

    def test_streaming_split_bold_reapplies_cleanly_without_losing_letters(self):
        renderer = StreamingMarkupRenderer()
        d1 = renderer.update("Привет **жир", final=False)
        d2 = renderer.update("Привет **жирный текст", final=False)
        d3 = renderer.update("Привет **жирный текст** конец", final=True)
        d4 = renderer.finish()
        combined = d1 + d2 + d3 + d4
        # Visible content without ANSI escapes must equal exact text without stray **
        import re
        visible = re.sub(r"\x1b\[[0-9;]*m", "", combined)
        assert visible == "Привет жирный текст конец"
        assert "**" not in visible
        assert "\033[1m" in combined

    def test_streaming_preserves_closing_code_fence_and_renders_box(self):
        renderer = StreamingMarkupRenderer()
        chunks = [
            "Код:\n```python\n",
            "print(1)\n",
            "```\nГотово.",
        ]
        acc = ""
        out = []
        for idx, ch in enumerate(chunks):
            acc += ch
            out.append(renderer.update(acc, final=(idx == len(chunks) - 1)))
        out.append(renderer.finish())
        rendered = "".join(out)
        assert "┌──" in rendered
        assert "python" in rendered
        assert "└──" in rendered
        assert "Готово." in rendered

    def test_closing_backticks_not_clipped_as_partial_tool_prefix(self):
        text = "```python\nx = 42\n```"
        cleaned = get_clean_text(text)
        assert cleaned.endswith("```")
        rendered = render_terminal_markup(cleaned, final=True)
        assert "┌──" in rendered and "└──" in rendered

    def test_get_clean_text_isolates_tool_calls_but_keeps_regular_code_and_json(self):
        mixed = (
            "Начинаю проверку.\n"
            '```tool_call\n{"tool": "read_file", "path": "app.py"}\n```\n'
            "<thought>hidden reasoning</thought>\n"
            "<tool_call>{\"tool\": \"list_dir\", \"path\": \".\"}</tool_call>\n"
            '{"tool": "grep_search", "query": "foo"}\n'
            "Пример конфига:\n"
            '```json\n{"host": "localhost", "port": 8080}\n```\n'
            "И код:\n"
            "```python\nprint('hello')\n```"
        )
        cleaned = get_clean_text(mixed)
        assert "tool_call" not in cleaned
        assert "hidden reasoning" not in cleaned
        assert "grep_search" not in cleaned
        assert "read_file" not in cleaned
        assert "Начинаю проверку." in cleaned
        assert '"host": "localhost"' in cleaned
        assert "print('hello')" in cleaned

    def test_get_clean_text_strips_unclosed_streaming_tool_tail(self):
        partial1 = "Сейчас посмотрю файл.\n```tool_c"
        partial2 = 'Читаю проект\n{"tool": "read_file", "path": "main'
        assert get_clean_text(partial1) == "Сейчас посмотрю файл."
        assert get_clean_text(partial2) == "Читаю проект"
