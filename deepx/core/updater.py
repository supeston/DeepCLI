import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Callable, Optional
import zipfile

import httpx

from deepx.core.version import (
    ARCHIVE_ZIP_URL,
    RAW_VERSION_URL,
    RELEASES_API_URL,
    UpdateInfo,
    get_local_version,
    get_project_root,
    is_newer_version,
    parse_version,
)

UPDATE_CACHE_TTL_SECONDS = 1800  # 30 minutes

_PRESERVED_ROOT_ENTRIES = {
    ".env",
    ".env.local",
    ".venv",
    "venv",
    ".git",
    ".deepx",
    ".deepx_history",
    ".deepx_project_memory.json",
    ".pytest_cache",
    "__pycache__",
    "state.json",
    "vds_profiles.json",
    "dadata_logos",
    "downloads",
}

_PRESERVED_SUFFIXES = (".env",)


def _default_cache_path(project_root: Path) -> Path:
    return project_root / ".deepx" / "update_cache.json"


def _read_cache(cache_path: Path) -> Optional[dict]:
    if not cache_path.is_file():
        return None
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("latest_version"):
            return data
    except Exception:
        pass
    return None


def _write_cache(cache_path: Path, latest_version: str) -> None:
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "checked_at": time.time(),
            "latest_version": str(latest_version).strip().lstrip("vV"),
        }
        cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _default_fetch_text(url: str, timeout: float) -> Optional[str]:
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url, headers={"Accept": "text/plain, application/json"})
            if resp.status_code == 200:
                return resp.text
    except Exception:
        return None
    return None


def _fetch_remote_version(
    timeout: float,
    fetch_text_fn: Optional[Callable[[str, float], Optional[str]]] = None,
) -> tuple[Optional[str], str]:
    fetcher = fetch_text_fn or _default_fetch_text

    raw_text = fetcher(RAW_VERSION_URL, timeout)
    if raw_text:
        candidate = raw_text.strip().splitlines()[0].strip().lstrip("vV")
        if candidate and parse_version(candidate) != (0,):
            return candidate, "raw"

    release_text = fetcher(RELEASES_API_URL, timeout)
    if release_text:
        try:
            data = json.loads(release_text)
            tag = str(data.get("tag_name") or data.get("name") or "").strip().lstrip("vV")
            if tag and parse_version(tag) != (0,):
                return tag, "release"
        except Exception:
            pass

    return None, ""


def check_for_updates(
    force_refresh: bool = False,
    timeout: float = 1.8,
    project_root: Optional[Path] = None,
    cache_path: Optional[Path] = None,
    fetch_text_fn: Optional[Callable[[str, float], Optional[str]]] = None,
) -> UpdateInfo:
    """Check whether a newer DEEPX version is available on GitHub without failing offline."""
    root = Path(project_root) if project_root is not None else get_project_root()
    current = get_local_version(root)
    cache_file = Path(cache_path) if cache_path is not None else _default_cache_path(root)

    if not force_refresh:
        cached = _read_cache(cache_file)
        if cached:
            checked_at = float(cached.get("checked_at") or 0.0)
            cached_latest = str(cached.get("latest_version") or "").strip().lstrip("vV")
            if cached_latest and (time.time() - checked_at) <= UPDATE_CACHE_TTL_SECONDS:
                return UpdateInfo(
                    current_version=current,
                    latest_version=cached_latest,
                    has_update=is_newer_version(cached_latest, current),
                    source="cache",
                )

    remote_version, source = _fetch_remote_version(timeout=timeout, fetch_text_fn=fetch_text_fn)
    if remote_version:
        _write_cache(cache_file, remote_version)
        return UpdateInfo(
            current_version=current,
            latest_version=remote_version,
            has_update=is_newer_version(remote_version, current),
            source=source,
        )

    return UpdateInfo(
        current_version=current,
        latest_version=current,
        has_update=False,
        source="offline",
        error="Не удалось получить информацию об обновлениях",
    )


def _should_preserve_relpath(rel_path: Path) -> bool:
    parts_lower = [part.lower() for part in rel_path.parts]
    if not parts_lower:
        return True
    if parts_lower[0] in _PRESERVED_ROOT_ENTRIES:
        return True
    if any(part in {".git", "__pycache__", ".venv", ".deepx", ".deepx_history", ".pytest_cache"} for part in parts_lower):
        return True
    name_lower = rel_path.name.lower()
    if name_lower in {"state.json", "vds_profiles.json", ".env"} or name_lower.endswith(_PRESERVED_SUFFIXES):
        return True
    return False


def _download_bytes(url: str, timeout: float = 30.0) -> bytes:
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.content


def _extract_safe_zip(zip_bytes: bytes, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    archive_path = dest_dir / "update.zip"
    archive_path.write_bytes(zip_bytes)
    extract_dir = dest_dir / "extracted"
    extract_dir.mkdir(parents=True, exist_ok=True)
    extract_root = extract_dir.resolve()

    with zipfile.ZipFile(archive_path, "r") as zf:
        for member in zf.infolist():
            target_path = (extract_root / member.filename).resolve()
            if not target_path.is_relative_to(extract_root):
                raise ValueError(f"Unsafe zip member path: {member.filename}")
        zf.extractall(extract_root)

    if (extract_root / "deepx").is_dir():
        return extract_root
    subdirs = [p for p in extract_root.iterdir() if p.is_dir()]
    if len(subdirs) == 1 and (subdirs[0] / "deepx").is_dir():
        return subdirs[0]
    raise RuntimeError("Архив обновления не содержит пакет deepx/")


def _sync_tree_preserving_user_data(source_root: Path, project_root: Path) -> int:
    updated_files = 0
    for src_item in source_root.rglob("*"):
        rel = src_item.relative_to(source_root)
        if _should_preserve_relpath(rel):
            continue
        dst_item = project_root / rel
        if src_item.is_dir():
            dst_item.mkdir(parents=True, exist_ok=True)
            continue
        dst_item.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_item, dst_item)
        updated_files += 1
    return updated_files


def _try_git_fast_forward(project_root: Path) -> tuple[bool, str]:
    git_exe = shutil.which("git")
    if not git_exe or not (project_root / ".git").exists():
        return False, "git-репозиторий не найден"

    status_proc = subprocess.run(
        [git_exe, "status", "--porcelain"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if status_proc.returncode != 0 or status_proc.stdout.strip():
        return False, "в рабочей директории есть локальные изменения"

    fetch_proc = subprocess.run(
        [git_exe, "fetch", "origin", "main", "--tags"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=25,
    )
    if fetch_proc.returncode != 0:
        return False, fetch_proc.stderr.strip() or "ошибка git fetch"

    pull_proc = subprocess.run(
        [git_exe, "pull", "--ff-only", "origin", "main"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=25,
    )
    if pull_proc.returncode != 0:
        return False, pull_proc.stderr.strip() or "fast-forward невозможен"
    return True, "обновлено через git fast-forward"


def perform_self_update(
    project_root: Optional[Path] = None,
    python_executable: Optional[Path] = None,
    archive_url: str = ARCHIVE_ZIP_URL,
    force: bool = False,
    fetch_text_fn: Optional[Callable[[str, float], Optional[str]]] = None,
    download_bytes_fn: Optional[Callable[[str, float], bytes]] = None,
    install_deps: bool = True,
) -> tuple[bool, str]:
    """Update DEEPX from GitHub while preserving .env, state.json, .deepx*, and .venv."""
    root = Path(project_root) if project_root is not None else get_project_root()
    py_exec = Path(python_executable) if python_executable is not None else Path(sys.executable)

    info = check_for_updates(
        force_refresh=True,
        timeout=4.0,
        project_root=root,
        fetch_text_fn=fetch_text_fn,
    )
    if info.source == "offline" and not force:
        return False, "Не удалось проверить обновления (нет доступа к GitHub)."
    if not info.has_update and not force:
        return True, f"Уже установлена актуальная версия v{info.current_version}."

    method_note = ""
    git_ok, git_msg = _try_git_fast_forward(root)
    if git_ok:
        method_note = git_msg
    else:
        downloader = download_bytes_fn or _download_bytes
        try:
            zip_bytes = downloader(archive_url, 35.0)
            with tempfile.TemporaryDirectory(prefix="deepx-update-") as td:
                src_root = _extract_safe_zip(zip_bytes, Path(td))
                count = _sync_tree_preserving_user_data(src_root, root)
            method_note = f"обновлено файлов: {count}"
        except Exception as exc:
            return False, f"Ошибка обновления: {exc} ({git_msg})"

    new_version = get_local_version(root)
    _write_cache(_default_cache_path(root), new_version)

    deps_note = ""
    req_file = root / "requirements.txt"
    if install_deps and req_file.is_file():
        pip_proc = subprocess.run(
            [str(py_exec), "-m", "pip", "install", "-r", str(req_file), "--disable-pip-version-check", "-q"],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        if pip_proc.returncode != 0:
            deps_note = " (зависимости не доустановились — выполните install.py)"

    if new_version != info.current_version:
        return True, (
            f"Обновлено с v{info.current_version} до v{new_version} ({method_note}){deps_note}. "
            "Перезапустите DEEPX для применения изменений."
        )
    return True, f"Файлы синхронизированы с веткой main ({method_note}, v{new_version}){deps_note}."
