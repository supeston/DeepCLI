import json
import os
import re
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class CheckpointManager:
    """Stores pre-modification file snapshots in `<workspace>/.deepx_history` and supports `/undo`."""

    HISTORY_DIR_NAME = ".deepx_history"
    MANIFEST_NAME = "manifest.json"
    MAX_TURN_GROUPS = 50

    def __init__(self, workspace_dir: str):
        self.workspace_dir = os.path.abspath(workspace_dir)
        self._active_turn_id: Optional[str] = None
        self._turn_snapshotted_paths: set[str] = set()

    def set_workspace(self, workspace_dir: str) -> None:
        self.workspace_dir = os.path.abspath(workspace_dir)
        self._active_turn_id = None
        self._turn_snapshotted_paths.clear()

    @property
    def history_dir(self) -> Path:
        return Path(self.workspace_dir) / self.HISTORY_DIR_NAME

    @property
    def manifest_path(self) -> Path:
        return self.history_dir / self.MANIFEST_NAME

    def begin_turn(self, label: str = "") -> str:
        """Start a grouped checkpoint turn so `/undo` rolls back all changes made in one agent turn."""
        turn_id = f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        self._active_turn_id = turn_id
        self._turn_snapshotted_paths.clear()
        return turn_id

    def end_turn(self) -> None:
        self._active_turn_id = None
        self._turn_snapshotted_paths.clear()

    def _load_manifest(self) -> List[Dict[str, Any]]:
        if not self.manifest_path.is_file():
            return []
        try:
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except Exception:
            pass
        return []

    def _save_manifest(self, groups: List[Dict[str, Any]]) -> None:
        self.history_dir.mkdir(parents=True, exist_ok=True)
        # Prune oldest turns beyond MAX_TURN_GROUPS
        while len(groups) > self.MAX_TURN_GROUPS:
            dropped = groups.pop(0)
            group_dir = self.history_dir / str(dropped.get("group_id", ""))
            if group_dir.is_dir():
                shutil.rmtree(group_dir, ignore_errors=True)
        self.manifest_path.write_text(
            json.dumps(groups, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def record_before_modify(self, target_path: str, tool_name: str = "") -> None:
        """Save pre-modification snapshot (or non-existence marker) before writing/editing `target_path`."""
        abs_target = os.path.abspath(target_path)
        norm_key = os.path.normcase(abs_target)

        # Never snapshot files inside .deepx_history itself
        try:
            if Path(abs_target).resolve().is_relative_to(self.history_dir.resolve()):
                return
        except Exception:
            pass

        groups = self._load_manifest()
        group_id = self._active_turn_id

        if group_id:
            if norm_key in self._turn_snapshotted_paths:
                return
            self._turn_snapshotted_paths.add(norm_key)
        else:
            group_id = f"step_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        group = None
        for g in reversed(groups):
            if g.get("group_id") == group_id:
                group = g
                break

        if group is None:
            group = {
                "group_id": group_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "entries": [],
            }
            groups.append(group)
        else:
            # Already snapshotted in this group?
            if any(os.path.normcase(e.get("target_path", "")) == norm_key for e in group["entries"]):
                return

        group_dir = self.history_dir / group_id
        group_dir.mkdir(parents=True, exist_ok=True)

        existed = os.path.exists(abs_target) and os.path.isfile(abs_target)
        backup_rel = None
        if existed:
            backup_name = f"file_{len(group['entries'])}_{uuid.uuid4().hex[:6]}.bak"
            backup_file = group_dir / backup_name
            shutil.copy2(abs_target, backup_file)
            backup_rel = backup_name

        group["entries"].append({
            "target_path": abs_target,
            "existed": existed,
            "backup_file": backup_rel,
            "tool": tool_name,
        })
        self._save_manifest(groups)

    def undo_last(self) -> Tuple[bool, str]:
        """Restore the most recent checkpoint group. Returns `(ok, summary_message)`."""
        groups = self._load_manifest()
        if not groups:
            return False, "Нет сохранённых чекпоинтов для отката."

        last_group = groups.pop()
        group_id = str(last_group.get("group_id", ""))
        group_dir = self.history_dir / group_id
        restored: List[str] = []
        removed: List[str] = []
        errors: List[str] = []

        # Rollback entries in reverse order
        for entry in reversed(last_group.get("entries", [])):
            target_path = entry.get("target_path")
            if not target_path:
                continue
            target = Path(target_path)
            existed = bool(entry.get("existed"))
            backup_name = entry.get("backup_file")
            try:
                rel_display = os.path.relpath(target_path, self.workspace_dir)
            except Exception:
                rel_display = target_path

            try:
                if existed and backup_name:
                    backup_file = group_dir / backup_name
                    if not backup_file.is_file():
                        errors.append(f"{rel_display}: не найден файл резервной копии")
                        continue
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_file, target)
                    restored.append(rel_display)
                elif not existed:
                    if target.is_file():
                        target.unlink()
                        removed.append(rel_display)
            except Exception as exc:
                errors.append(f"{rel_display}: {exc}")

        if group_dir.is_dir():
            shutil.rmtree(group_dir, ignore_errors=True)
        self._save_manifest(groups)

        parts: List[str] = []
        if restored:
            parts.append("Восстановлены: " + ", ".join(restored))
        if removed:
            parts.append("Удалены созданные файлы: " + ", ".join(removed))
        if errors:
            parts.append("Ошибки: " + "; ".join(errors))
        if not parts:
            parts.append("Чекпоинт снят (изменений не требовалось).")

        return not bool(errors), " | ".join(parts)

    def has_checkpoints(self) -> bool:
        return bool(self._load_manifest())


_SHELL_DELETE_RE = re.compile(
    r"(?:^|[;&|(\s])(?:"
    r"rm\s+\S+|"
    r"rmdir\b|rd\s+(?:/[sq]\s+)*\S|del\s+(?:/[pfqs]\s+)*\S|erase\s+\S|"
    r"remove-item\b|deltree\b|"
    r"git\s+(?:reset\s+--hard|clean\s+-[a-zA-Z]*f|push\s+(?:.*?\s)?(?:--force|-f)\b)|"
    r"format\s+[a-zA-Z]:|diskpart\b|shutdown\b|reg\s+delete\b|"
    r"drop\s+(?:table|database)\b"
    r")",
    re.IGNORECASE,
)

_PYTHON_DESTRUCTIVE_RE = re.compile(
    r"\b(?:shutil\.rmtree|os\.remove|os\.unlink|\.unlink\s*\(|os\.rmdir)\b"
)

_VDS_READONLY_ACTIONS = {"list_profiles", "test", "test_connection", "ping", "sys_info", "status", "info", "disconnect", "close"}


def _is_within_workspace(candidate_path: str, workspace_cwd: str) -> bool:
    if not candidate_path or not workspace_cwd:
        return True
    try:
        ws = Path(workspace_cwd).resolve()
        if os.path.isabs(candidate_path):
            target = Path(candidate_path).resolve()
        else:
            target = (ws / candidate_path).resolve()
        return target == ws or target.is_relative_to(ws)
    except Exception:
        return False


def _is_temp_path(candidate_path: str) -> bool:
    try:
        temp_dir = Path(tempfile.gettempdir()).resolve()
        return Path(candidate_path).resolve().is_relative_to(temp_dir)
    except Exception:
        return False


def classify_dangerous_operation(
    tool_name: str,
    args: Optional[Dict[str, Any]],
    workspace_cwd: str,
) -> Optional[str]:
    """Return a concise Russian reason if an operation is destructive, remote-VDS, or outside workspace.

    Normal file edits, read operations, and running tests/scripts inside workspace return None.
    """
    args = args or {}
    ws_real = os.path.abspath(workspace_cwd or os.getcwd())

    if tool_name == "vds_deploy":
        action = str(args.get("action") or "exec").strip().lower()
        if action not in _VDS_READONLY_ACTIONS:
            host = args.get("profile") or args.get("host") or "VDS"
            return f"Удалённая операция VDS ({action} -> {host})"
        return None

    # Writing/modifying/packing/extracting outside current workspace
    if tool_name in ("write_file", "edit_file", "make_docx", "make_pptx", "make_excel", "render_plan"):
        p = str(args.get("path") or args.get("output") or "").strip()
        if p and not _is_within_workspace(p, ws_real) and not _is_temp_path(p):
            return f"Изменение файла за пределами рабочей папки: {p}"
        return None

    if tool_name == "zip_pack":
        out = str(args.get("zip_path") or args.get("output") or args.get("path") or "").strip()
        src_files = args.get("files") if args.get("files") is not None else args.get("source")
        if out and not _is_within_workspace(out, ws_real):
            return f"Создание архива за пределами рабочей папки: {out}"
        items = src_files if isinstance(src_files, (list, tuple)) else ([src_files] if src_files else [])
        for item in items:
            s_item = str(item or "").strip()
            if s_item and not _is_within_workspace(s_item, ws_real):
                return f"Архивация пути за пределами рабочей папки: {s_item}"
        return None

    if tool_name == "unzip_pack":
        src = str(args.get("zip_path") or args.get("path") or args.get("source") or "").strip()
        dest = str(args.get("extract_to") or args.get("dest") or args.get("output") or "").strip()
        if dest and not _is_within_workspace(dest, ws_real):
            return f"Распаковка за пределы рабочей папки: {dest}"
        if src and not _is_within_workspace(src, ws_real):
            return f"Распаковка архива из внешней папки: {src}"
        return None

    if tool_name in ("run_cmd", "run_background_cmd"):
        cmd = str(args.get("command") or "").strip()
        cmd_cwd = str(args.get("cwd") or "").strip()
        if cmd_cwd and not _is_within_workspace(cmd_cwd, ws_real):
            return f"Запуск команды за пределами рабочей папки ({cmd_cwd}): {cmd[:60]}"
        if _SHELL_DELETE_RE.search(cmd):
            return f"Необратимая/удаляющая команда: {cmd[:70]}"
        return None

    if tool_name == "run_python":
        code = str(args.get("code") or "")
        if _PYTHON_DESTRUCTIVE_RE.search(code):
            return "Удаление файлов из Python-скрипта (rmtree/remove/unlink)"
        return None

    return None
