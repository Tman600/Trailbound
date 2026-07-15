"""
Freeplay: a solo, fully free-form mode. Unlike the five structured genres
(which all share one money/food/vehicle/distance simulation), Freeplay has
no fixed setting or economy -- just a protagonist, a health total, and a
free-form inventory. The player describes the opening scene (or asks for
a surprise) and an optional goal, then every turn is: type anything, get
narrated back, with a real single-keypress stats check available anytime.

This mode requires local AI to function at all -- there's no scripted
content to fall back on for genuinely open-ended input -- so main.py only
offers it when `ai.available` is True.
"""
from dataclasses import dataclass, field
from typing import List, Dict

HEALTH_DELTA_BOUNDS = (-30, 25)
MAX_NEW_ITEMS_PER_TURN = 2
END_WORDS = {"end", "end story", "end the story", "end it here", "quit", "stop", "exit"}
SUMMARY_EVERY_N_TURNS = 6  # how often to fold recent events into the rolling summary


@dataclass
class FreeplayState:
    health: int = 100
    alive: bool = True
    inventory: List[Dict[str, str]] = field(default_factory=list)  # [{"name":..., "detail":...}]
    goal: str = ""
    log: List[str] = field(default_factory=list)
    turn: int = 0
    ended: bool = False
    ending_text: str = ""
    summary: str = ""
    summarized_up_to: int = 0  # index into log already folded into `summary`

    def note(self, text: str):
        self.log.append(text)

    def apply_health_delta(self, delta: int):
        self.health = max(0, min(100, self.health + delta))
        if self.health <= 0:
            self.alive = False

    def find_item(self, name: str):
        target = name.strip().lower()
        for item in self.inventory:
            if item["name"].strip().lower() == target:
                return item
        return None

    def add_item(self, name: str, detail: str = ""):
        name = name.strip()
        if not name:
            return
        existing = self.find_item(name)
        if existing:
            if detail:
                existing["detail"] = detail
            return
        self.inventory.append({"name": name, "detail": detail})

    def update_item(self, name: str, detail: str):
        existing = self.find_item(name)
        if existing:
            existing["detail"] = detail
        else:
            self.add_item(name, detail)

    def remove_item(self, name: str):
        existing = self.find_item(name)
        if existing:
            self.inventory.remove(existing)


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def apply_turn_result(state: FreeplayState, result: dict):
    """Applies an already-sanitized result dict (see ai.interpret_freeplay_action)
    to the state, with a final defensive clamp on health regardless of what
    the caller already did."""
    delta = _clamp(result.get("health_delta", 0), *HEALTH_DELTA_BOUNDS)
    state.apply_health_delta(delta)

    for item in (result.get("inventory_add") or [])[:MAX_NEW_ITEMS_PER_TURN]:
        state.add_item(item.get("name", ""), item.get("detail", ""))
    for item in (result.get("inventory_update") or []):
        state.update_item(item.get("name", ""), item.get("detail", ""))
    for name in (result.get("inventory_remove") or []):
        state.remove_item(name)


def maybe_update_summary(state: FreeplayState, ai):
    """Every SUMMARY_EVERY_N_TURNS turns, folds the log entries since the
    last summary update into an updated running summary. This is what keeps
    long sessions from losing early context: the raw log passed to the AI
    each turn only covers the last few beats, but the summary compresses
    everything before that into a few sentences, so key names/items/plot
    threads from turn 3 are still known at turn 50."""
    new_entries = state.log[state.summarized_up_to:]
    if len(new_entries) < SUMMARY_EVERY_N_TURNS:
        return
    fallback = state.summary or " ".join(new_entries)[:400]
    prompt = (
        f"Previous summary of the story so far: {state.summary or '(nothing yet -- this is early on)'}\n"
        f"New events since then:\n{chr(10).join(new_entries)}\n"
        "Write an updated 3-5 sentence summary of the whole story so far, folding in both the "
        "previous summary and the new events. Keep only what matters for continuity: key names, "
        "items, locations, relationships, and unresolved threads. Present tense, no headers."
    )
    system = "You write compact running summaries for a solo text adventure, for the game's own continuity tracking -- not shown to the player."
    state.summary = ai.generate(prompt, system=system, fallback=fallback, max_tokens=200)
    state.summarized_up_to = len(state.log)


def start(ai, ui):
    """Runs the setup flow (scene + optional goal) and returns
    (FreeplayState, opening_narration_text)."""
    ui.freeplay_clear()
    ui.freeplay_title()
    scene_input = ui.freeplay_prompt_line("Describe how the story begins (or type 'surprise me'):")
    goal_input = ui.freeplay_prompt_line("Optional -- what's your goal? (press Enter to skip)")

    state = FreeplayState(goal=goal_input.strip())

    surprise = not scene_input.strip() or scene_input.strip().lower() in ("surprise me", "surprise", "random")
    system = "You write terse, atmospheric scene-openers for a solo text adventure, in second person present tense. No dialogue, no headers."
    if surprise:
        fallback = ("You find yourself at the edge of a quiet forest as daylight fades, "
                    "the path ahead splitting into shadow.")
        prompt = "Invent a vivid, grounded opening scene (2-3 sentences) to drop a solo protagonist into."
    else:
        fallback = scene_input.strip()
        prompt = (f"The player wants the story to open here: \"{scene_input.strip()}\". "
                  "Write a 2-3 sentence vivid opening that stays true to what they described.")

    opening_text = ai.generate(prompt, system=system, fallback=fallback, max_tokens=110)
    state.note(opening_text)
    return state, opening_text


def play(ai, ui):
    """Runs a full Freeplay session to completion (some ending is always
    reached: death, or the player choosing to end it) and returns the final
    FreeplayState."""
    state, scene_text = start(ai, ui)

    while not state.ended:
        ui.freeplay_clear()
        ui.freeplay_print(scene_text)
        ui.freeplay_print_hint()

        action = ui.freeplay_read_action()
        if action is None:  # Tab was pressed -- show stats, then redisplay the same scene
            ui.freeplay_clear()
            ui.freeplay_print_stats(state)
            ui.freeplay_any_key()
            continue

        if action.strip().lower() in END_WORDS:
            _finalize(state, ai, ui, reason="player_choice")
            break

        state.turn += 1
        result = ai.interpret_freeplay_action(state, action)
        scene_text = result["narration"]
        apply_turn_result(state, result)
        state.note(f"You: {action}\n{scene_text}")
        maybe_update_summary(state, ai)

        if not state.alive:
            _finalize(state, ai, ui, reason="death")
            break

    return state


def _finalize(state: FreeplayState, ai, ui, reason: str):
    recent = " ".join(state.log[-6:]) if state.log else "The story barely got started."
    summary_line = f"Summary of the whole story so far: {state.summary} " if state.summary else ""
    if reason == "death":
        fallback = "It ends here -- however it happened, there's no continuing from this."
        prompt = (f"{summary_line}The protagonist's health has run out. Recent events: {recent} "
                  "Write a 3-5 sentence closing narration for this ending, grounded and matching the tone.")
    else:
        fallback = "The story pauses here, at a point of the traveler's own choosing."
        prompt = (f"{summary_line}The player chose to end the story here. Recent events: {recent} "
                  "Write a 3-5 sentence closing narration that brings this to a natural close.")
    system = "You write closing narration for a solo text adventure. No headers, no meta-commentary, no dialogue tags."
    text = ai.generate(prompt, system=system, fallback=fallback, max_tokens=180)
    state.ended = True
    state.ending_text = text
    ui.freeplay_clear()
    ui.freeplay_print_ending(text, tier="death" if reason == "death" else "closed")
    ui.freeplay_any_key()
