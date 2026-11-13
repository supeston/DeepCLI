from prompt_toolkit.completion import Completer, Completion


_SUBCOMMANDS = {
    "mode": [
        ("instant", "Fast responses with DeepThink OFF"),
        ("think", "DeepThink reasoning mode ON"),
        ("plan", "Read-only planning mode (blocks file writes & commands)"),
    ],
    "style": [
        ("coder", "Software engineering, debugging & VDS deploy"),
        ("universal", "Writing, analytics & office documents"),
        ("osinter", "OSINT research & entity verification"),
    ],
    "think": [
        ("on", "Enable DeepThink reasoning"),
        ("off", "Disable DeepThink reasoning"),
    ],
    "search": [
        ("on", "Enable Smart Web Search"),
        ("off", "Disable Smart Web Search"),
    ],
}


class SlashCommandCompleter(Completer):
    """Autocomplete slash commands and known sub-arguments."""

    def __init__(self, commands: dict):
        self.commands = commands

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if not text.startswith("/"):
            return

        if " " in text:
            cmd_part, arg_part = text[1:].split(" ", 1)
            cmd_key = cmd_part.strip().lower()
            options = _SUBCOMMANDS.get(cmd_key)
            if not options:
                return
            arg_query = arg_part.lstrip().lower()
            replace_len = len(arg_part.lstrip())
            for value, desc in options:
                if value.startswith(arg_query):
                    yield Completion(
                        value,
                        start_position=-replace_len,
                        display=value,
                        display_meta=desc,
                    )
            return

        query = text[1:].lower()
        for cmd, desc in self.commands.items():
            if cmd.lower().startswith(query):
                yield Completion(
                    f"/{cmd}",
                    start_position=-len(text),
                    display=f"/{cmd}",
                    display_meta=desc,
                )
