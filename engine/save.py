import json
import os
from dataclasses import asdict
from .state import GameState, Character

SAVE_PATH = os.path.join(os.path.expanduser("~"), ".trailbound_save.json")


def save_game(state: GameState) -> bool:
    try:
        data = asdict(state)
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return True
    except OSError:
        return False


def load_game():
    if not os.path.exists(SAVE_PATH):
        return None
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        party_data = data.pop("party", [])
        state = GameState(**data)
        state.party = [Character(**c) for c in party_data]
        return state
    except (OSError, json.JSONDecodeError, TypeError, KeyError):
        return None


def clear_save():
    try:
        if os.path.exists(SAVE_PATH):
            os.remove(SAVE_PATH)
    except OSError:
        pass
