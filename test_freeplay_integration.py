from engine import freeplay


class FakeAI:
    available = True

    def __init__(self, action_responses):
        self.action_responses = list(action_responses)
        self.call_n = 0

    def generate(self, prompt, system="", fallback="", max_tokens=120):
        return fallback  # deterministic narration for setup/ending beats

    def interpret_freeplay_action(self, state, action_text):
        resp = self.action_responses[min(self.call_n, len(self.action_responses) - 1)]
        self.call_n += 1
        return resp


class ScriptedUI:
    """Drives a full session: setup answers, then a scripted sequence of
    actions (some of which are the sentinel None to simulate a stats-check
    request), verifying the stats screen gets shown and then play resumes."""
    def __init__(self, scene, goal, actions):
        self.scene = scene
        self.goal = goal
        self.actions = list(actions)
        self.action_i = 0
        self.stats_shown = 0
        self.any_key_calls = 0
        self.ending_shown = None

    def freeplay_clear(self): pass
    def freeplay_title(self): pass

    def freeplay_prompt_line(self, prompt_text):
        if "goal" in prompt_text.lower():
            return self.goal
        return self.scene

    def freeplay_print(self, text): pass
    def freeplay_print_hint(self): pass

    def freeplay_read_action(self):
        action = self.actions[self.action_i]
        self.action_i += 1
        return action  # may be None (stats request) or a string

    def freeplay_print_stats(self, state):
        self.stats_shown += 1

    def freeplay_any_key(self):
        self.any_key_calls += 1

    def freeplay_print_ending(self, text, tier):
        self.ending_shown = (text, tier)


def test_full_session_with_stats_check_and_player_ends_it():
    ai = FakeAI([
        {"narration": "You take a step forward.", "health_delta": -2,
         "inventory_add": [{"name": "stick", "detail": ""}], "inventory_update": [], "inventory_remove": []},
        {"narration": "You keep walking.", "health_delta": 0,
         "inventory_add": [], "inventory_update": [], "inventory_remove": []},
    ])
    ui = ScriptedUI(
        scene="a quiet forest at dusk",
        goal="find shelter before dark",
        actions=["go forward", None, "keep walking", "end the story"],
    )
    final_state = freeplay.play(ai, ui)

    assert final_state.ended is True
    assert ui.stats_shown == 1  # the None action triggered exactly one stats view
    assert ui.any_key_calls == 2  # once after stats, once after the final ending
    assert ui.ending_shown is not None
    assert ui.ending_shown[1] == "closed"  # ended by player choice, not death
    assert final_state.health == 98  # 100 - 2 from the first action
    assert final_state.find_item("stick") is not None
    assert final_state.goal == "find shelter before dark"
    print("test_full_session_with_stats_check_and_player_ends_it OK")


def test_death_ending():
    ai = FakeAI([
        {"narration": "It goes badly.", "health_delta": -30,
         "inventory_add": [], "inventory_update": [], "inventory_remove": []},
        {"narration": "It goes very badly.", "health_delta": -30,
         "inventory_add": [], "inventory_update": [], "inventory_remove": []},
        {"narration": "It goes terribly.", "health_delta": -30,
         "inventory_add": [], "inventory_update": [], "inventory_remove": []},
        {"narration": "The end.", "health_delta": -30,
         "inventory_add": [], "inventory_update": [], "inventory_remove": []},
    ])
    ui = ScriptedUI(
        scene="a collapsing cave",
        goal="",
        actions=["push forward", "push forward", "push forward", "push forward"],
    )
    final_state = freeplay.play(ai, ui)

    assert final_state.ended is True
    assert final_state.alive is False
    assert final_state.health == 0
    assert ui.ending_shown[1] == "death"
    print("test_death_ending OK")


def test_surprise_me_scene():
    ai = FakeAI([])
    ui = ScriptedUI(scene="surprise me", goal="", actions=["end"])
    final_state = freeplay.play(ai, ui)
    assert final_state.ended is True
    assert len(final_state.log) >= 1
    print("test_surprise_me_scene OK")


if __name__ == "__main__":
    test_full_session_with_stats_check_and_player_ends_it()
    test_death_ending()
    test_surprise_me_scene()
    print("\nAll Freeplay integration tests passed.")
