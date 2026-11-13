import ast
import os
import re
from pathlib import Path
from typing import List, Optional, Set, Tuple

IGNORED_DIRS: Set[str] = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    "node_modules",
    "dist",
    "build",
    "target",
    ".next",
    ".nuxt",
    ".idea",
    ".vscode",
    ".deepx_history",
    ".deepx",
    "coverage",
    "htmlcov",
}

INSTRUCTION_FILENAMES: Tuple[str, ...] = ("DEEPX.md", "AGENTS.md")


def load_project_instructions(cwd: str, max_chars: int = 8000) -> str:
    """Load DEEPX.md and/or AGENTS.md instructions from workspace directory."""
    if not cwd or not os.path.isdir(cwd):
        return ""

    base = Path(cwd).resolve()
    seen_realpaths: Set[str] = set()
    sections: List[str] = []
    remaining = max_chars

    for filename in INSTRUCTION_FILENAMES:
        candidate = base / filename
        if not candidate.is_file():
            # Case-insensitive fallback lookup inside cwd
            try:
                for entry in base.iterdir():
                    if entry.is_file() and entry.name.lower() == filename.lower():
                        candidate = entry
                        break
            except OSError:
                continue

        if not candidate.is_file():
            continue

        try:
            real_key = os.path.normcase(str(candidate.resolve()))
            if real_key in seen_realpaths:
                continue
            seen_realpaths.add(real_key)
            content = candidate.read_text(encoding="utf-8-sig", errors="replace").strip()
            if not content:
                continue
            if len(content) > remaining:
                content = content[: max(200, remaining - 32)].rstrip() + "\n...[truncated]"
            sections.append(f"[{candidate.name}]\n{content}")
            remaining -= len(sections[-1]) + 2
            if remaining <= 200:
                break
        except OSError:
            continue

    return "\n\n".join(sections)


def _format_python_args(args: ast.arguments) -> str:
    names: List[str] = []
    for a in getattr(args, "posonlyargs", []):
        names.append(a.arg)
    for a in args.args:
        names.append(a.arg)
    if args.vararg:
        names.append("*" + args.vararg.arg)
    for a in args.kwonlyargs:
        names.append(a.arg)
    if args.kwarg:
        names.append("**" + args.kwarg.arg)
    if len(names) > 6:
        return ", ".join(names[:5]) + ", ..."
    return ", ".join(names)


def _extract_python_symbols(file_path: Path, max_symbols: int = 24) -> List[str]:
    """Extract compact top-level classes, methods, and functions via ast.parse."""
    try:
        source = file_path.read_text(encoding="utf-8-sig", errors="replace")
        if len(source) > 250_000:
            return ["(file too large for AST summary)"]
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as exc:
        return [f"(syntax error at line {exc.lineno or '?'})"]
    except Exception:
        return []

    symbols: List[str] = []
    for node in tree.body:
        if len(symbols) >= max_symbols:
            symbols.append("...")
            break
        if isinstance(node, ast.ClassDef):
            methods: List[str] = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(f"{item.name}({_format_python_args(item.args)})")
                    if len(methods) >= 10:
                        methods.append("...")
                        break
            if methods:
                symbols.append(f"class {node.name}: " + ", ".join(methods))
            else:
                symbols.append(f"class {node.name}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
            symbols.append(f"{prefix} {node.name}({_format_python_args(node.args)})")
    return symbols


_JS_TS_SIG_RE = re.compile(
    r"^(?:export\s+(?:default\s+)?)?(?:async\s+)?(?:function\s+([A-Za-z_$][\w$]*)\s*\(([^)]*)\)|class\s+([A-Za-z_$][\w$]*))",
    re.MULTILINE,
)


def _extract_generic_symbols(file_path: Path, ext: str, max_symbols: int = 16) -> List[str]:
    if ext not in (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"):
        return []
    try:
        source = file_path.read_text(encoding="utf-8-sig", errors="replace")
        if len(source) > 150_000:
            return []
    except Exception:
        return []

    symbols: List[str] = []
    for m in _JS_TS_SIG_RE.finditer(source):
        if m.group(1):
            params = ", ".join(p.strip().split(":")[0].split("=")[0].strip() for p in m.group(2).split(",") if p.strip())
            if len(params) > 40:
                params = params[:37] + "..."
            symbols.append(f"fn {m.group(1)}({params})")
        elif m.group(3):
            symbols.append(f"class {m.group(3)}")
        if len(symbols) >= max_symbols:
            symbols.append("...")
            break
    return symbols


def build_repo_map(
    cwd: str,
    max_files: int = 140,
    max_lines: int = 220,
    max_chars: int = 7500,
) -> str:
    """Build a compact AST + file tree repository map excluding venv/cache/git noise."""
    if not cwd or not os.path.isdir(cwd):
        return ""

    base = Path(cwd).resolve()
    rel_files: List[Tuple[str, Path]] = []
    skipped_count = 0

    for root_str, dirs, files in os.walk(base):
        dirs[:] = sorted(
            d for d in dirs
            if d not in IGNORED_DIRS and not d.endswith(".egg-info")
        )
        for fname in sorted(files):
            if fname.endswith((".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe")):
                continue
            full_path = Path(root_str) / fname
            try:
                rel = full_path.relative_to(base).as_posix()
            except ValueError:
                continue
            if len(rel_files) < max_files:
                rel_files.append((rel, full_path))
            else:
                skipped_count += 1

    if not rel_files and skipped_count == 0:
        return f"Workspace: {base}\n(empty directory)"

    lines: List[str] = [f"Workspace: {base}"]
    total_chars = len(lines[0])

    for rel, full_path in rel_files:
        if len(lines) >= max_lines:
            skipped_count += 1
            continue

        ext = full_path.suffix.lower()
        syms: List[str] = []
        if ext == ".py":
            syms = _extract_python_symbols(full_path)
        else:
            syms = _extract_generic_symbols(full_path, ext)

        if syms:
            entry_line = f"- {rel}: " + "; ".join(syms)
        else:
            entry_line = f"- {rel}"

        if total_chars + len(entry_line) + 1 > max_chars:
            skipped_count += 1
            break

        lines.append(entry_line)
        total_chars += len(entry_line) + 1

    if skipped_count > 0:
        lines.append(f"... ({skipped_count} more files omitted)")

    return "\n".join(lines)


def build_zero_turn_context(cwd: str) -> str:
    """Build combined zero-turn workspace context: instructions (DEEPX.md/AGENTS.md) + repo map."""
    parts: List[str] = []
    repo_map = build_repo_map(cwd)
    if repo_map:
        parts.append("[REPOSITORY MAP]\n" + repo_map)
    instructions = load_project_instructions(cwd)
    if instructions:
        parts.append("[PROJECT INSTRUCTIONS]\n" + instructions)
    return "\n\n".join(parts)
