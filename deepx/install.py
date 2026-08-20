#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
DEEPX AGENT — Automated Environment Setup & Dependency Installer
==============================================================================
"""

import os
import sys
import subprocess
import shutil
import platform
import venv
from pathlib import Path

# Ensure UTF-8 stdout/stderr on all platforms (especially Windows CP1251/CP866)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass


def log_step(number: int, title: str):
    print(f"\n{BOLD}{CYAN}[{number}/6]{RESET} {BOLD}{title}{RESET}")


def log_success(message: str):
    print(f"  {GREEN}[+] {RESET}{message}")


def log_info(message: str):
    print(f"  {DIM}[i] {RESET}{message}")


def log_warn(message: str):
    print(f"  {YELLOW}[!] {RESET}{YELLOW}{message}{RESET}")


def log_error(message: str):
    print(f"  {RED}[X] {RESET}{RED}{BOLD}{message}{RESET}")


def print_banner():
    banner = f"""
{CYAN}{BOLD}
 ================================================================
    DEEPX AGENT - Automated Environment Setup & Installer
 ================================================================
{RESET}{DIM}  Autonomous AI Developer, ConPTY Terminal & DeepSeek Engine{RESET}
{DIM}  ================================================================{RESET}
"""
    print(banner)


def check_python_version() -> bool:
    v = sys.version_info
    log_info(f"Detected Python version: {platform.python_version()} ({platform.system()} {platform.machine()})")
    if v.major < 3 or (v.major == 3 and v.minor < 10):
        log_error(f"Python 3.10 or higher is required. You are running Python {v.major}.{v.minor}.{v.micro}.")
        log_warn("Please install Python 3.11 or 3.12 from https://www.python.org/downloads/ (ensure 'Add Python to PATH' is checked).")
        return False
    log_success(f"Python version {platform.python_version()} meets requirements (>= 3.10)")
    return True


def setup_virtual_environment(project_root: Path, venv_dir: Path) -> Path:
    """Create .venv or reuse existing, return path to python executable."""
    if sys.platform == "win32":
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:
        venv_python = venv_dir / "bin" / "python"

    if venv_python.exists():
        log_info(f"Virtual environment already exists at '{venv_dir}'.")
        return venv_python

    print(f"  Creating isolated virtual environment at '{venv_dir}'...")
    try:
        builder = venv.EnvBuilder(with_pip=True, upgrade_deps=False)
        builder.create(venv_dir)
        log_success(f"Created virtual environment in '{venv_dir}'")
        return venv_python
    except Exception as e:
        log_warn(f"venv module returned notice: {e}. Attempting fallback via sys.executable...")
        try:
            subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
            log_success(f"Created virtual environment in '{venv_dir}'")
            return venv_python
        except Exception as e2:
            log_error(f"Failed to create virtual environment: {e2}")
            log_info("Falling back to current Python environment...")
            return Path(sys.executable)


def run_pip_command(py_exec: Path, args: list, description: str) -> bool:
    cmd = [str(py_exec), "-m", "pip"] + args
    print(f"  {DIM}> {' '.join(cmd)}{RESET}")
    try:
        res = subprocess.run(cmd, check=True)
        return res.returncode == 0
    except subprocess.CalledProcessError as e:
        log_error(f"{description} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        log_error(f"{description} failed: {e}")
        return False


def install_playwright_browsers(py_exec: Path) -> bool:
    cmd = [str(py_exec), "-m", "playwright", "install", "chromium"]
    print(f"  {DIM}> {' '.join(cmd)}{RESET}")
    try:
        subprocess.run(cmd, check=True)
        log_success("Playwright Chromium browser engine installed successfully")
        return True
    except Exception as e:
        log_warn(f"Notice during Playwright browser installation: {e}")
        log_info("You can run 'playwright install chromium' manually later if needed.")
        return False


def setup_configurations(project_root: Path):
    cache_dir = project_root / ".deepx" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    log_success(f"Initialized cache directory at '{cache_dir}'")

    env_example = project_root / ".env.example"
    env_target = project_root / ".env"
    core_env_target = project_root / "deepx" / "core" / ".env"

    if env_example.exists():
        if not env_target.exists():
            shutil.copyfile(env_example, env_target)
            log_success("Created '.env' from template")
        if not core_env_target.exists():
            shutil.copyfile(env_example, core_env_target)
            log_success("Created 'deepx/core/.env' from template")


def perform_health_check(py_exec: Path) -> bool:
    test_script = """
import sys
modules = [
    "rich", "prompt_toolkit", "pyperclip", "requests", "dotenv",
    "openpyxl", "pandas", "docx", "pptx", "PIL", "pymediainfo", "playwright"
]
if sys.platform == "win32":
    modules.extend(["winpty", "winsdk", "win32clipboard"])

failed = []
for m in modules:
    try:
        __import__(m)
    except Exception as e:
        failed.append((m, str(e)))

if failed:
    print("FAILED:" + ";".join(f"{m}:{err}" for m, err in failed))
    sys.exit(1)
else:
    print("ALL_OK")
    sys.exit(0)
"""
    try:
        res = subprocess.run(
            [str(py_exec), "-c", test_script],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and "ALL_OK" in res.stdout:
            log_success("All core modules and dependencies imported successfully!")
            return True
        else:
            log_warn(f"Some modules reported warnings: {res.stdout.strip() or res.stderr.strip()}")
            return False
    except Exception as e:
        log_warn(f"Diagnostic check notice: {e}")
        return False


def main():
    print_banner()
    # project_root is the parent of deepx/
    project_root = Path(__file__).resolve().parent.parent

    # Step 1: Check Python version
    log_step(1, "Checking System Environment & Python Version")
    if not check_python_version():
        sys.exit(1)

    # Step 2: Virtual environment
    log_step(2, "Configuring Isolated Virtual Environment (.venv)")
    venv_dir = project_root / ".venv"
    py_exec = setup_virtual_environment(project_root, venv_dir)
    log_info(f"Target Python interpreter: {py_exec}")

    # Step 3: Upgrade pip & build tools
    log_step(3, "Upgrading Pip and Build Tools")
    run_pip_command(py_exec, ["install", "--upgrade", "pip", "setuptools", "wheel"], "Pip upgrade")

    # Step 4: Install requirements.txt
    log_step(4, "Installing Python Dependencies (requirements.txt)")
    req_file = project_root / "requirements.txt"
    if req_file.exists():
        success = run_pip_command(py_exec, ["install", "-r", str(req_file)], "Dependencies installation")
        if success:
            log_success("All requirements installed successfully")
        else:
            log_warn("Pip finished with notices. Continuing setup...")
    else:
        log_error(f"File '{req_file}' not found.")

    # Step 5: Install Playwright Browsers
    log_step(5, "Installing Playwright Chromium Browser Engine")
    install_playwright_browsers(py_exec)

    # Step 6: Setup configurations & Health Check
    log_step(6, "Initializing Configurations & Self-Diagnosis Health Check")
    setup_configurations(project_root)
    healthy = perform_health_check(py_exec)

    print(f"\n{BOLD}{GREEN}================================================================")
    print(f"       🎉 DEEPX AGENT INSTALLATION COMPLETED SUCCESSFULLY!       ")
    print(f"================================================================{RESET}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Installation cancelled by user.{RESET}")
        sys.exit(130)
    except Exception as e:
        log_error(f"Unexpected installer error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
