import os
from typing import Optional

from rich import box
from rich.align import Align
from rich.markup import escape as rich_escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from deepx.core.config import COMMANDS_DICT, STYLE_CONFIGS
from deepx.core.version import UpdateInfo, get_local_version
from deepx.ui.terminal import console

DEEPX_ASCII_ART = """\
██████╗ ███████╗███████╗██████╗ ██╗  ██╗
██╔══██╗██╔════╝██╔════╝██╔══██╗╚██╗██╔╝
██║  ██║█████╗  █████╗  ██████╔╝ ╚███╔╝
██║  ██║██╔══╝  ██╔══╝  ██╔═══╝  ██╔██╗
██████╔╝███████╗███████╗██║     ██╔╝ ██╗
╚═════╝ ╚══════╝╚══════╝╚═╝     ╚═╝  ╚═╝"""

MODEL_NAME = "DeepSeek-V4.1-Flash"
MODEL_PARAMS = "284B / 13B"
BANNER_WIDTH = 84


def _padded_ascii_block() -> str:
    lines = DEEPX_ASCII_ART.splitlines()
    max_w = max((len(line) for line in lines), default=0)
    return "\n".join(line.ljust(max_w) for line in lines)


def _format_workspace_path(cwd: str, max_len: int = 54) -> str:
    raw = str(cwd or "").strip()
    if not raw:
        return ""
    home = os.path.expanduser("~")
    if home and raw.lower().startswith(home.lower()):
        tail = raw[len(home):]
        if not tail or tail.startswith(("\\", "/")):
            raw = "~" + tail
    if len(raw) <= max_len:
        return raw
    keep = max(8, (max_len - 3) // 2)
    return f"{raw[:keep]}...{raw[-keep:]}"


def _format_mode_badge(mode: str) -> str:
    norm = str(mode or "instant").strip().lower()
    mapping = {
        "instant": "[bold #F8FAFC]Fast[/bold #F8FAFC]",
        "fast": "[bold #F8FAFC]Fast[/bold #F8FAFC]",
        "think": "[bold #A78BFA]Think[/bold #A78BFA]",
        "plan": "[bold #38BDF8]Plan[/bold #38BDF8]",
    }
    return mapping.get(norm, f"[bold #F8FAFC]{rich_escape(str(mode))}[/bold #F8FAFC]")


def render_banner(
    mode: str = "instant",
    style: str = "coder",
    think: bool = False,
    search: bool = False,
    status_message: str | None = None,
    cwd: str | None = None,
    update_info: Optional[UpdateInfo] = None,
):
    """Render the framed Rich startup banner with active state and update notices."""
    version_str = get_local_version()
    term_width = getattr(console, "width", 100) or 100
    wide_mode = term_width >= 60
    if wide_mode:
        panel_width = min(BANNER_WIDTH, max(62, term_width - 8))
    else:
        panel_width = max(34, term_width - 2)

    grid = Table.grid(expand=True)
    grid.add_column(justify="center")

    if wide_mode:
        title = Align.center(Text(_padded_ascii_block(), style="bold #536DFE", end=""))
    else:
        title = Text("DEEPX AGENT", style="bold #536DFE", end="")

    version_val = f"[#CBD5E1]v{rich_escape(version_str)}[/#CBD5E1]"
    model_val = f"[bold #536DFE]{MODEL_NAME}[/bold #536DFE]"
    params_val = f"[#64748B]({MODEL_PARAMS})[/#64748B]"
    meta_line = f"{version_val}  [dim #475569]·[/dim #475569]  {model_val} {params_val}"

    rule_width = max(24, min(58, panel_width - 16))
    divider = Text("─" * rule_width, style="#334155")

    if status_message:
        status_line = f"[bold #F8FAFC]{rich_escape(status_message)}[/bold #F8FAFC]"
    else:
        style_cfg = STYLE_CONFIGS.get(style, STYLE_CONFIGS["coder"])
        style_label = style_cfg["label"].capitalize()
        mode_val = _format_mode_badge(mode)
        style_val = f"[bold #A78BFA]{rich_escape(style_label)}[/bold #A78BFA]"
        think_val = "[bold #38BDF8]ON[/bold #38BDF8]" if think else "[#64748B]OFF[/#64748B]"
        search_val = "[bold #38BDF8]ON[/bold #38BDF8]" if search else "[#64748B]OFF[/#64748B]"
        sep = "  [dim #475569]·[/dim #475569]  "
        status_line = (
            f"[#94A3B8]Mode:[/#94A3B8] {mode_val}"
            f"{sep}[#94A3B8]Style:[/#94A3B8] {style_val}"
            f"{sep}[#94A3B8]Think:[/#94A3B8] {think_val}"
            f"{sep}[#94A3B8]Search:[/#94A3B8] {search_val}"
        )

    grid.add_row(title)
    grid.add_row(Text(""))
    grid.add_row(Text.from_markup(meta_line))
    grid.add_row(divider)
    grid.add_row(Text.from_markup(status_line))

    if cwd and not status_message:
        display_cwd = _format_workspace_path(cwd, max_len=max(24, panel_width - 24))
        if display_cwd:
            grid.add_row(
                Text.from_markup(
                    f"[#64748B]Workspace:[/#64748B] [#94A3B8]{rich_escape(display_cwd)}[/#94A3B8]"
                )
            )

    if update_info is not None and getattr(update_info, "has_update", False):
        latest = rich_escape(str(update_info.latest_version).lstrip("vV"))
        grid.add_row(Text(""))
        grid.add_row(
            Text.from_markup(
                f"[bold #FBBF24]▸ update to {latest}[/bold #FBBF24]  "
                f"[dim #475569]·[/dim #475569]  [#CBD5E1]run /update to install[/#CBD5E1]"
            )
        )

    subtitle = (
        "[dim #64748B] /help  ·  /menu  ·  Ctrl+X stop  ·  Ctrl+C exit [/dim #64748B]"
        if panel_width >= 56
        else "[dim #64748B] /help · Ctrl+C exit [/dim #64748B]"
    )

    panel = Panel(
        grid,
        border_style="#536DFE",
        box=box.ROUNDED,
        padding=(1, 3) if wide_mode else (0, 2),
        width=panel_width,
        expand=False,
        subtitle=subtitle,
        subtitle_align="center",
    )
    console.print()
    console.print(Align.center(panel))


def print_help():
    """Render structured slash-command reference panel."""
    cmd_details = [
        ("/mode <instant|think|plan>", "Режим работы: быстрый (instant), DeepThink (think), read-only (plan)"),
        ("/style <coder|universal|osinter>", "Профиль агента и доступный набор инструментов"),
        ("/think [on|off]", "Переключить движок глубоких рассуждений DeepThink"),
        ("/search [on|off]", "Переключить встроенный веб-поиск"),
        ("/cd <path>", "Сменить рабочую директорию и перестроить AST-карту проекта"),
        ("/compact", "Сжать устаревшие выводы инструментов в истории чата"),
        ("/undo", "Откатить изменения файлов за последний ход из .deepx_history"),
        ("/status", "Показать активные параметры сессии и статус обновлений"),
        ("/update", "Проверить обновления в GitHub и установить свежую версию"),
        ("/stealth", "Проверить версию playwright-stealth и сигналы отпечатка браузера"),
        ("/menu", "Открыть интерактивное TUI-меню настроек"),
        ("/new", "Сбросить текущий контекст и начать новый диалог"),
        ("/copy", "Скопировать последний ответ модели в буфер обмена"),
        ("/clear", "Очистить экран и перерисовать баннер"),
        ("/exit, /quit", "Завершить работу DEEPX CLI"),
    ]

    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold #536DFE",
        padding=(0, 1),
        expand=True,
    )
    table.add_column("Команда", style="bold #38BDF8", no_wrap=True)
    table.add_column("Описание", style="#E2E8F0")

    listed = set()
    for cmd_syntax, desc in cmd_details:
        base_cmd = cmd_syntax.split()[0].lstrip("/").rstrip(",")
        listed.add(base_cmd)
        table.add_row(cmd_syntax, desc)

    for cmd_name, desc in COMMANDS_DICT.items():
        if cmd_name not in listed and cmd_name != "help":
            table.add_row(f"/{cmd_name}", desc)

    panel = Panel(
        table,
        title="[bold #536DFE] DEEPX COMMANDS [/bold #536DFE]",
        title_align="left",
        subtitle="[dim #64748B] Tab autocomplete · Ctrl+X interrupt · Ctrl+C exit [/dim #64748B]",
        subtitle_align="left",
        border_style="#536DFE",
        box=box.ROUNDED,
        padding=(0, 1),
        expand=False,
    )
    console.print()
    console.print(panel)
    console.print()


def print_status(
    mode: str,
    style: str,
    think: bool,
    search: bool,
    cwd: str,
    state_file: str,
    update_info: Optional[UpdateInfo] = None,
):
    """Render framed session status panel."""
    version_str = get_local_version()
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold #536DFE", width=18, no_wrap=True)
    grid.add_column(style="#E2E8F0")

    style_label = STYLE_CONFIGS.get(style, STYLE_CONFIGS["coder"])["label"]
    mode_badge = _format_mode_badge(mode)
    think_badge = "[bold #38BDF8]ON[/bold #38BDF8]" if think else "[#64748B]OFF[/#64748B]"
    search_badge = "[bold #38BDF8]ON[/bold #38BDF8]" if search else "[#64748B]OFF[/#64748B]"

    grid.add_row("Version:", f"v{rich_escape(version_str)}")
    grid.add_row("Model:", f"{MODEL_NAME} [dim #64748B]({MODEL_PARAMS})[/dim #64748B]")
    grid.add_row("Mode:", mode_badge)
    grid.add_row("Style:", f"[bold #A78BFA]{rich_escape(style_label)}[/bold #A78BFA]")
    grid.add_row("DeepThink:", think_badge)
    grid.add_row("Web Search:", search_badge)
    grid.add_row("Workspace:", f"[#94A3B8]{rich_escape(str(cwd))}[/#94A3B8]")
    grid.add_row("Session State:", f"[#64748B]{rich_escape(str(state_file))}[/#64748B]")

    if update_info is not None and getattr(update_info, "has_update", False):
        latest = rich_escape(str(update_info.latest_version).lstrip("vV"))
        grid.add_row(
            "Update:",
            f"[bold #FBBF24]update to {latest}[/bold #FBBF24] [dim #64748B](/update)[/dim #64748B]",
        )
    elif update_info is not None and getattr(update_info, "source", "local") != "local":
        grid.add_row("Update:", "[bold #10B981]up to date[/bold #10B981]")

    panel = Panel(
        grid,
        title="[bold #536DFE] SESSION STATUS [/bold #536DFE]",
        title_align="left",
        border_style="#536DFE",
        box=box.ROUNDED,
        padding=(0, 2),
        expand=False,
    )
    console.print()
    console.print(panel)
    console.print()
