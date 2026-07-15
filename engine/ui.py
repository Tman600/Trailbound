"""
All terminal rendering lives here, built on `rich` so colors and layout
work consistently across Windows Terminal, plain cmd.exe, macOS Terminal,
and Linux terminals alike.
"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt
from rich.text import Text
from rich.align import Align

console = Console()

BANNER = r"""
 _______        _ _ _                       _
|__   __|      (_) |  |                    | |
   | |_ __ __ _ _| | |__   ___  _   _ _ __ | |
   | | '__/ _` | | | '_ \ / _ \| | | | '_ \| |
   | | | | (_| | | | |_) | (_) | |_| | | | |_|
   |_|_|  \__,_|_|_|_.__/ \___/ \__,_|_| |_(_)
"""


def print_banner():
    console.print(Text(BANNER, style="bold yellow"))
    console.print(Align.center(Text("a procedurally generated journey, told your way", style="italic grey70")))
    console.print()


def print_ai_status(line: str, ai_on: bool):
    style = "bold green" if ai_on else "grey58"
    console.print(f"[{style}]{line}[/{style}]\n")


def print_genre_menu(genres):
    table = Table(title="Choose Your Journey", show_lines=False, header_style="bold cyan")
    table.add_column("#", justify="right")
    table.add_column("Genre")
    table.add_column("Premise")
    for i, g in enumerate(genres, 1):
        table.add_row(str(i), g.name, g.tagline)
    console.print(table)


def prompt_int(question: str, choices, default=None) -> int:
    return IntPrompt.ask(question, choices=[str(c) for c in choices], default=default)


def prompt_choice(question: str, options: list) -> int:
    """Numbered menu prompt. Returns the 0-indexed choice."""
    for i, opt in enumerate(options, 1):
        console.print(f"  [bold cyan]{i}[/bold cyan]. {opt}")
    idx = IntPrompt.ask("Choose", choices=[str(i) for i in range(1, len(options) + 1)], show_choices=False)
    return idx - 1


def print_story(text: str, title: str = None, style: str = "white"):
    console.print(Panel(Text(text, style=style), title=title, border_style="cyan", padding=(1, 2)))


def print_event(text: str, title: str = "Event"):
    console.print(Panel(Text(text), title=f"[bold]{title}[/bold]", border_style="yellow", padding=(1, 2)))


def print_good(text: str):
    console.print(f"[bold green]{text}[/bold green]")


def print_bad(text: str):
    console.print(f"[bold red]{text}[/bold red]")


def print_info(text: str):
    console.print(f"[grey70]{text}[/grey70]")


def condition_style(condition: str) -> str:
    return {
        "healthy": "green",
        "weary": "yellow",
        "critical": "bold red",
        "dead": "grey50",
    }.get(condition, "white")


def render_status(state, genre):
    frac = state.progress_fraction()
    bar = "█" * int(frac * 30) + "░" * (30 - int(frac * 30))

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column(style="bold")
    table.add_column()
    table.add_row("Day", str(state.day))
    table.add_row("Route", f"[cyan]{bar}[/cyan] {frac*100:0.0f}%")
    table.add_row(genre.currency.capitalize(), str(state.money))
    table.add_row(genre.food_name.capitalize(), str(state.food))
    table.add_row(genre.special_resource.capitalize(), str(state.special_resource))
    table.add_row(genre.vehicle.capitalize() + " condition", f"{state.vehicle_health}/100")
    table.add_row("Morale", f"{state.morale}/100")
    table.add_row("Pace", state.pace)
    table.add_row("Rations", state.rations)

    party_lines = []
    for c in state.party:
        style = condition_style(c.condition)
        party_lines.append(f"[{style}]{c.name} ({c.role}) - {c.condition}[/{style}]")
    party_block = "\n".join(party_lines) if party_lines else "No one left."

    console.print(Panel(table, title="Status", border_style="blue", padding=(0, 1)))
    console.print(Panel(party_block, title="Party", border_style="magenta", padding=(0, 1)))


def print_landmark(name: str):
    console.print(Align.center(Text(f"~ {name} ~", style="bold underline cyan")))


def print_ending(title: str, text: str, tier: str):
    style_map = {
        "triumphant": "bold green",
        "secret": "bold magenta",
        "success": "bold cyan",
        "bittersweet": "bold yellow",
        "tragic": "bold red",
    }
    style = style_map.get(tier, "white")
    console.print()
    console.print(Panel(Text(text, style="white"), title=f"[{style}]{title}[/{style}]",
                         border_style=style, padding=(2, 4)))


def prompt_action(hint: str = None) -> str:
    """Free-text input for 'type your own action'. Returns '' if the person
    just presses Enter (meaning: skip to quick options / default outcome)."""
    line = "What do you do?"
    if hint:
        line += f" ({hint})"
    line += " Type it out, or press Enter for quick options."
    console.print(f"[grey70]{line}[/grey70]")
    text = Prompt.ask("[bold cyan]>[/bold cyan]", default="", show_default=False)
    return text.strip()


def print_action_effects(parts: list):
    if parts:
        console.print(f"[grey70]{' / '.join(parts)}[/grey70]")


def pause():
    Prompt.ask("\n[grey58](press Enter to continue)[/grey58]", default="", show_default=False)


# ==================================================================== #
# Freeplay: a distinct visual mode -- green, screen clears each beat,  #
# and a real single-keypress stats check that never eats a keystroke  #
# from whatever the player is about to type.                          #
# ==================================================================== #
import os
import sys

_STATS_SENTINEL = object()
_STATS_KEY = "\t"  # Tab -- never the first character of a natural sentence


def _read_single_char() -> str:
    """Reads exactly one keypress with no Enter required. Windows via
    msvcrt, Mac/Linux via termios/tty -- both standard library, no extra
    dependencies. Raises on any failure (e.g. stdin isn't a real terminal);
    callers must catch and fall back to plain input()."""
    try:
        import msvcrt
        return msvcrt.getwch()
    except ImportError:
        import termios
        import tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _raw_read_line():
    """Reads a full line character-by-character in raw mode, echoing as it
    goes, so Tab can be checked as the very first keystroke without ever
    losing the first character of a normal typed action. Returns the typed
    string, or _STATS_SENTINEL if Tab was pressed first."""
    buf = []
    first = True
    while True:
        ch = _read_single_char()
        if first and ch == _STATS_KEY:
            sys.stdout.write("\n")
            sys.stdout.flush()
            return _STATS_SENTINEL
        first = False
        if ch in ("\r", "\n"):
            sys.stdout.write("\n")
            sys.stdout.flush()
            return "".join(buf)
        if ch in ("\x7f", "\x08"):  # backspace/delete
            if buf:
                buf.pop()
                sys.stdout.write("\b \b")
                sys.stdout.flush()
            continue
        if ch == "\x03":  # Ctrl-C
            raise KeyboardInterrupt
        if ch == "":
            continue
        buf.append(ch)
        sys.stdout.write(ch)
        sys.stdout.flush()


def freeplay_clear():
    # Rich's console.clear() sends an ANSI clear-screen code, but some
    # terminals (older Windows consoles especially) don't fully honor it and
    # it ends up just scrolling content out of view instead of truly
    # clearing. The OS's own clear command is guaranteed to actually clear.
    os.system("cls" if os.name == "nt" else "clear")


def freeplay_title():
    console.print("[bold green]~ Freeplay ~[/bold green]\n")


def freeplay_print(text: str):
    console.print(Text(text, style="green"))
    console.print()


def freeplay_print_hint():
    console.print("[dim green]Tab: check stats   |   type your move and press Enter[/dim green]")


def freeplay_prompt_line(prompt_text: str) -> str:
    """Normal Enter-terminated input, used only during setup (scene/goal)."""
    console.print(f"[green]{prompt_text}[/green]")
    return Prompt.ask("[green]>[/green]", default="", show_default=False)


def freeplay_read_action():
    """Reads the player's next action. Returns None if Tab was pressed
    first (requesting a stats check) instead of a string."""
    console.print("[green]> [/green]", end="")
    try:
        result = _raw_read_line()
    except Exception:
        # No raw terminal control available (e.g. piped input in a test
        # harness, or an unusual environment) -- fall back to a plain
        # line read. Typing "stats" alone works as the equivalent there.
        line = input()
        return None if line.strip().lower() == "stats" else line
    return None if result is _STATS_SENTINEL else result


def freeplay_any_key():
    console.print("[dim green](press any key to continue)[/dim green]", end="")
    try:
        _read_single_char()
        sys.stdout.write("\n")
    except Exception:
        input()


def freeplay_print_stats(state):
    lines = [f"Health: {state.health}/100"]
    if state.goal:
        lines.append(f"Goal: {state.goal}")
    lines.append("")
    lines.append("Inventory:")
    if state.inventory:
        for item in state.inventory:
            detail = f" ({item['detail']})" if item.get("detail") else ""
            lines.append(f"  {item['name']}{detail}")
    else:
        lines.append("  (empty)")
    console.print(Panel("\n".join(lines), title="[bold green]Status[/bold green]",
                         border_style="green", style="green", padding=(1, 2)))


def freeplay_print_ending(text: str, tier: str):
    title = "It Ends Here" if tier == "death" else "The Story Ends"
    console.print(Panel(Text(text, style="green"), title=f"[bold green]{title}[/bold green]",
                         border_style="green", padding=(2, 4)))
