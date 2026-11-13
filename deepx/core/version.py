from dataclasses import dataclass
from pathlib import Path
import re
from typing import Optional

__version__ = "3.1.0"

GITHUB_REPO = "supeston/DeepCLI"
GITHUB_BRANCH = "main"
RAW_VERSION_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/VERSION"
RELEASES_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
ARCHIVE_ZIP_URL = f"https://github.com/{GITHUB_REPO}/archive/refs/heads/{GITHUB_BRANCH}.zip"


@dataclass(frozen=True)
class UpdateInfo:
    current_version: str
    latest_version: str
    has_update: bool
    source: str = "local"
    error: str = ""


def parse_version(raw: str) -> tuple[int, ...]:
    """Parse a semantic version string into an integer tuple for safe comparison."""
    cleaned = str(raw or "").strip().lstrip("vV")
    nums = [int(part) for part in re.findall(r"\d+", cleaned)]
    return tuple(nums[:4]) if nums else (0,)


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_local_version(project_root: Optional[Path] = None) -> str:
    """Read local version from VERSION file, falling back to bundled __version__."""
    root = Path(project_root) if project_root is not None else get_project_root()
    version_file = root / "VERSION"
    if version_file.is_file():
        try:
            text = version_file.read_text(encoding="utf-8").strip().lstrip("vV")
            if text:
                return text
        except Exception:
            pass
    return __version__


def is_newer_version(candidate: str, current: str) -> bool:
    """Return True strictly when candidate semantic version is greater than current."""
    cand_t = parse_version(candidate)
    curr_t = parse_version(current)
    max_len = max(len(cand_t), len(curr_t))
    cand_padded = cand_t + (0,) * (max_len - len(cand_t))
    curr_padded = curr_t + (0,) * (max_len - len(curr_t))
    return cand_padded > curr_padded
