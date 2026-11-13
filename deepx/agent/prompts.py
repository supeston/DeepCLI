from pathlib import Path
import re

from deepx.core.constants import *
from deepx.core.config import *

SYSTEM_PROMPT_FILE = Path(__file__).resolve().parent.parent / "core" / "system_prompt.txt"
SYSTEM_PROMPT_NOTHINK_FILE = Path(__file__).resolve().parent.parent / "core" / "system_prompt_nothink.txt"


def load_agent_system_prompt_base(think: bool = True) -> str:
    prompt_file = SYSTEM_PROMPT_FILE if think else SYSTEM_PROMPT_NOTHINK_FILE
    if not think and not prompt_file.exists():
        prompt_file = SYSTEM_PROMPT_FILE
    try:
        prompt = prompt_file.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise RuntimeError(
            f"Cannot load editable system prompt '{prompt_file}': {error}"
        ) from error
    if not prompt:
        raise RuntimeError(f"Editable system prompt '{prompt_file}' is empty")
    return prompt


def normalize_style_name(value: str):
    name = (value or "").strip().lower()
    if name in STYLE_CONFIGS:
        return name
    return STYLE_ALIASES.get(name)


def build_agent_system_prompt(
    style: str,
    think: bool = True,
    workspace: str = None,
    repo_context: str = "",
    plan_mode: bool = False,
) -> str:
    style = normalize_style_name(style) or "coder"
    config = STYLE_CONFIGS[style]
    workspace = workspace or default_workspace_dir()
    tool_lines = [
        TOOL_DESCRIPTIONS[name]
        for name in sorted(config["tools"])
        if name in TOOL_DESCRIPTIONS
    ]
    parts = [
        load_agent_system_prompt_base(think),
        AGENT_EXECUTION_PROTOCOL,
        config["instructions"].strip(),
        (
            "РАБОЧАЯ ДИРЕКТОРИЯ:\n"
            f"{workspace}\n"
            "Все относительные пути отсчитываются отсюда. Не предполагай другую папку и не выясняй её "
            "командами — если нужен файл, ищи от этого пути через list_dir или grep_search."
        ),
        (
            "ПАМЯТЬ ПРОЕКТА:\n"
            "У тебя есть постоянная память только для текущей рабочей папки. Перед сложной, "
            "многошаговой задачей, продолжением прежней работы или если контекст неясен, сам вызови "
            "project_memory с action=get и опирайся на фактически сохранённые сведения. После важного "
            "завершённого этапа сохраняй короткий подтверждённый итог через append_event; когда меняются "
            "цель, текущая задача, факты или следующие шаги — обновляй сводку через update. Не записывай "
            "догадки, пароли, токены, полные сырые логи и личные данные без необходимости."
        ),
    ]
    if repo_context and repo_context.strip():
        parts.append(repo_context.strip())
    if plan_mode:
        parts.append(
            "АКТИВЕН РЕЖИМ PLAN (ТОЛЬКО ЧТЕНИЕ И ПЛАНИРОВАНИЕ):\n"
            "Ты можешь читать файлы, искать по коду и исследовать проект, но изменение файлов и выполнение команд "
            "временно заблокированы. Составь точный, проверяемый план действий и остановись до подтверждения "
            "пользователя (переключение в /mode think или /mode instant)."
        )
    parts.append(
        "ДОСТУПНЫЕ ИНСТРУМЕНТЫ "
        "(ВЫЗЫВАЙ ТОЛЬКО ЧЕРЕЗ ```tool_call):\n"
        + "\n".join(tool_lines)
    )
    return "\n\n".join(parts)


def _compact_task_text(value: str, limit: int = 1200) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[:limit] + f"... (+{len(text) - limit} chars)"


def _tool_result_failed(result: str) -> bool:
    lowered = str(result or "").lower()
    return any(marker in lowered for marker in (
        "[error",
        "[exit code:",
        "syntax check failed",
        "traceback (most recent call last)",
    ))


tool_result_failed = _tool_result_failed


def _summarize_large_output(output: str, tool_name: str = "", preview_chars: int = 240) -> str:
    text = str(output or "").strip()
    if len(text) <= preview_chars + 80:
        return text
    head = re.sub(r"\s+", " ", text[:preview_chars]).strip()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    tail = lines[-1][:140] if lines else ""
    label = f" {tool_name}" if tool_name else ""
    summary = f"[Свёрнутый вывод{label} ({len(text)} симв.): {head}..."
    if tail and tail not in head:
        summary += f" | конец: {tail}"
    summary += "]"
    return summary


def compact_conversation_history(
    steps: list,
    keep_recent: int = 4,
    fold_threshold: int = 1200,
) -> tuple:
    """Fold oversized tool outputs in older steps while keeping recent steps full."""
    if not isinstance(steps, list) or len(steps) <= keep_recent:
        return list(steps or []), 0, 0

    cutoff = max(0, len(steps) - max(1, int(keep_recent)))
    compacted = []
    folded_count = 0
    saved_chars = 0

    for idx, step in enumerate(steps):
        if idx >= cutoff or not isinstance(step, dict):
            compacted.append(dict(step) if isinstance(step, dict) else step)
            continue

        cloned = dict(step)
        if isinstance(cloned.get("output"), str) and len(cloned["output"]) > fold_threshold:
            old_len = len(cloned["output"])
            cloned["output"] = _summarize_large_output(
                cloned["output"],
                tool_name=str(cloned.get("tool") or ""),
            )
            folded_count += 1
            saved_chars += max(0, old_len - len(cloned["output"]))

        if isinstance(cloned.get("tool_outputs"), list):
            new_outputs = []
            for item in cloned["tool_outputs"]:
                s = str(item)
                if len(s) > fold_threshold:
                    new_s = _summarize_large_output(s)
                    new_outputs.append(new_s)
                    folded_count += 1
                    saved_chars += max(0, len(s) - len(new_s))
                else:
                    new_outputs.append(s)
            cloned["tool_outputs"] = new_outputs

        compacted.append(cloned)

    return compacted, folded_count, saved_chars


def build_compacted_session_seed(
    system_prompt: str,
    turn_history: list,
    todos: list = None,
    keep_recent: int = 4,
) -> tuple:
    """Create a compact handoff prompt after /compact to restore context cleanly."""
    compacted_turns, folded_count, saved_chars = compact_conversation_history(
        turn_history,
        keep_recent=keep_recent,
        fold_threshold=800,
    )
    sections = [system_prompt.strip()]
    if todos:
        todo_lines = [
            f"- [{item.get('status', 'pending')}] {item.get('text', '')}"
            for item in todos
            if str(item.get("text", "")).strip()
        ]
        if todo_lines:
            sections.append("[ТЕКУЩИЕ ЗАДАЧИ]:\n" + "\n".join(todo_lines))

    if compacted_turns:
        hist_lines = []
        cutoff = max(0, len(compacted_turns) - max(1, int(keep_recent)))
        for idx, turn in enumerate(compacted_turns):
            user_txt = _compact_task_text(turn.get("user", ""), 600 if idx >= cutoff else 240)
            asst_txt = _compact_task_text(turn.get("assistant", ""), 800 if idx >= cutoff else 320)
            line = f"Шаг {idx + 1}: Пользователь: {user_txt}"
            if turn.get("tool_outputs"):
                outs = "\n  ".join(str(o) for o in turn["tool_outputs"][-6:])
                line += f"\n  Инструменты:\n  {outs}"
            if asst_txt:
                line += f"\n  Агент: {asst_txt}"
            hist_lines.append(line)
        sections.append("[СЖАТАЯ ИСТОРИЯ ДИАЛОГА]:\n" + "\n\n".join(hist_lines))

    sections.append("Продолжай диалог с учётом приведённого контекста без повторного пересказа прошлых шагов.")
    return "\n\n".join(sections), folded_count, saved_chars


def build_agent_task_state(
    goal: str,
    todos: list,
    pending_verification: bool = False,
    strategy_change_required: bool = False,
    include_goal: bool = False,
) -> str:
    active = [
        str(item.get("text", "")).strip()
        for item in todos
        if item.get("status") == "active" and str(item.get("text", "")).strip()
    ]
    pending = [
        str(item.get("text", "")).strip()
        for item in todos
        if item.get("status") == "pending" and str(item.get("text", "")).strip()
    ]
    lines = []
    if include_goal:
        lines.append(f"Напоминание цели: {_compact_task_text(goal, 1200)}")
    if active:
        lines.append(f"Активный шаг: {_compact_task_text(active[0], 400)}")
    elif pending:
        lines.append(f"Следующий шаг: {_compact_task_text(pending[0], 400)}")
    if pending_verification:
        lines.append(
            "После изменения артефакта обязательная проверка ещё не выполнена."
        )
    if strategy_change_required:
        lines.append(
            "Одинаковая ошибка повторилась: смени подход и не повторяй тот же вызов."
        )
    if not lines:
        return ""
    return "\n[КРАТКОЕ СОСТОЯНИЕ]\n" + "\n".join(lines) + "\n[КОНЕЦ СОСТОЯНИЯ]\n"
