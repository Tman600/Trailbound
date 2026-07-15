#!/usr/bin/env python3
"""
Trailbound -- a procedurally generated, multiple-genre survival journey
for the terminal. Every run ends (five possible ending tiers per genre);
no genre or event pool repeats the same run twice.

Run it:
    python main.py

Optional: run Ollama locally (https://ollama.com) with any small model
pulled (e.g. `ollama pull llama3.2`) *before* starting Trailbound, and the
game will automatically use it to write richer, non-repeating narration
for the opening, landmarks, and ending. Nothing is required -- Trailbound
plays fully offline with its own built-in story text either way.
"""
import sys


def _rich_available() -> bool:
    try:
        import rich  # noqa: F401
        return True
    except ImportError:
        return False


if not _rich_available():
    print("Trailbound needs the 'rich' package for its terminal interface.\n")
    print("Install it with:\n    pip install rich\n")
    print("Then run this again with:\n    python main.py")
    sys.exit(1)

import random
from types import SimpleNamespace
from engine import ui
from engine import genres as genres_mod
from engine import events
from engine import endings
from engine import save
from engine import freeplay as freeplay_mod
from engine.ai import LocalAI

PACE_OPTIONS = ["grueling", "steady", "cautious"]
RATION_OPTIONS = ["bare", "meager", "filling"]

FREEPLAY_TAGLINE = "Solo, fully free-form -- type anything, judged for realism as the story unfolds."


def choose_mode(ai):
    """Returns either a Genre (start a structured journey) or the string
    'freeplay'. Freeplay only appears in the menu when local AI is
    available, since it has no scripted content to fall back on."""
    genre_list = genres_mod.list_genres()
    display_list = list(genre_list)
    if ai.available:
        display_list.append(SimpleNamespace(name="Freeplay", tagline=FREEPLAY_TAGLINE))

    ui.print_genre_menu(display_list)
    idx = ui.prompt_choice("Pick a genre", [g.name for g in display_list])

    if ai.available and idx == len(genre_list):
        return "freeplay"
    return genre_list[idx]


def start_structured_journey(genre, ai):
    rng = random.Random()
    state = events.new_game(genre, rng)
    intro = events.narrate(ai, genre, genre.intro_flavor, max_tokens=140)
    ui.print_story(intro, title=f"{genre.name} -- {genre.origin} \u2192 {state.flags['destination_name']}")
    ui.pause()
    return state, genre


def maybe_resume(ai):
    existing = save.load_game()
    if existing is None or existing.ended:
        return None, None
    resume = ui.prompt_choice(
        "A journey is already in progress.",
        [f"Continue it (Day {existing.day}, {existing.genre_id})", "Abandon it and start a new one"],
    )
    if resume == 0:
        genre = genres_mod.get_genre(existing.genre_id)
        return existing, genre
    save.clear_save()
    return None, None


def change_pace(state):
    idx = ui.prompt_choice(f"Current pace: {state.pace}", [
        "Grueling (fastest, hardest on people & vehicle)",
        "Steady (balanced)",
        "Cautious (slowest, easiest on people & vehicle)",
    ])
    state.pace = PACE_OPTIONS[idx]
    ui.print_info(f"Pace set to {state.pace}.")
    ui.pause()


def change_rations(state, genre):
    idx = ui.prompt_choice(f"Current rations: {state.rations}", [
        f"Bare (uses least {genre.food_name}, health suffers)",
        f"Meager (balanced use of {genre.food_name})",
        f"Filling (uses most {genre.food_name}, health improves)",
    ])
    state.rations = RATION_OPTIONS[idx]
    ui.print_info(f"Rations set to {state.rations}.")
    ui.pause()


def view_log(state):
    lines = state.log[-12:] if state.log else ["Nothing notable has happened yet."]
    ui.print_story("\n".join(lines), title="Journey Log")
    ui.pause()


def play_journey(state, genre, ai):
    rng = random.Random()
    while not state.ended:
        ui.render_status(state, genre)
        choice = ui.prompt_choice("What will you do?", [
            "Continue the journey",
            f"Change pace ({state.pace})",
            f"Change rations ({state.rations})",
            "View journey log",
            "Save & quit",
        ])
        if choice == 0:
            events.advance_day(state, genre, ai, ui, rng)
            if events.is_wiped_out(state) or events.is_stranded(state) or events.has_arrived(state):
                tier, title, text = endings.finalize(state, genre, ai)
                ui.render_status(state, genre)
                ui.print_ending(title, text, tier)
                save.clear_save()
                return
            save.save_game(state)
        elif choice == 1:
            change_pace(state)
        elif choice == 2:
            change_rations(state, genre)
        elif choice == 3:
            view_log(state)
        else:
            save.save_game(state)
            ui.print_info("Journey saved. Run Trailbound again any time to pick up where you left off.")
            sys.exit(0)


def main():
    ui.print_banner()
    ai = LocalAI()
    if ai.available:
        ui.print_info("Waking up the local model (first launch after it's been idle can take a bit)...")
        ai.warm_up()
    ui.print_ai_status(ai.status_line(), ai.available)

    state, genre = maybe_resume(ai)

    while True:
        if state is None:
            choice = choose_mode(ai)
            if choice == "freeplay":
                freeplay_mod.play(ai, ui)
                again = ui.prompt_choice("What next?", ["Start another journey", "Quit"])
                if again == 0:
                    continue
                ui.console.print("\n[grey58]Safe travels.[/grey58]")
                break
            state, genre = start_structured_journey(choice, ai)
        play_journey(state, genre, ai)
        again = ui.prompt_choice("What next?", ["Start a new journey", "Quit"])
        if again == 0:
            state, genre = None, None
            continue
        ui.console.print("\n[grey58]Safe travels.[/grey58]")
        break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Safe travels.")
        sys.exit(0)
