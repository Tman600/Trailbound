from engine.freeplay import FreeplayState, maybe_update_summary, SUMMARY_EVERY_N_TURNS, play


class FakeSummaryAI:
    def __init__(self):
        self.generate_calls = 0

    def generate(self, prompt, system="", fallback="", max_tokens=120):
        self.generate_calls += 1
        return f"SUMMARY_{self.generate_calls}"


def test_no_trigger_below_threshold():
    ai = FakeSummaryAI()
    s = FreeplayState()
    for i in range(SUMMARY_EVERY_N_TURNS - 1):
        s.note(f"event {i}")
    maybe_update_summary(s, ai)
    assert s.summary == ""
    assert ai.generate_calls == 0
    print("test_no_trigger_below_threshold OK")


def test_triggers_exactly_at_threshold():
    ai = FakeSummaryAI()
    s = FreeplayState()
    for i in range(SUMMARY_EVERY_N_TURNS):
        s.note(f"event {i}")
    maybe_update_summary(s, ai)
    assert s.summary == "SUMMARY_1"
    assert s.summarized_up_to == len(s.log)
    print("test_triggers_exactly_at_threshold OK")


def test_incorporates_previous_summary_in_prompt():
    captured = {}

    class CapturingAI:
        def generate(self, prompt, system="", fallback="", max_tokens=120):
            captured["prompt"] = prompt
            return "NEW_SUMMARY"

    s = FreeplayState(summary="Earlier: found a key.")
    s.summarized_up_to = 0
    for i in range(SUMMARY_EVERY_N_TURNS):
        s.note(f"new event {i}")
    maybe_update_summary(s, CapturingAI())
    assert "Earlier: found a key." in captured["prompt"]
    assert "new event 0" in captured["prompt"]
    print("test_incorporates_previous_summary_in_prompt OK")


class PlayableFakeAI:
    """Enough of the LocalAI interface for a live play() session that runs
    long enough to cross the summary threshold at least once."""
    available = True

    def generate(self, prompt, system="", fallback="", max_tokens=120):
        return fallback

    def interpret_freeplay_action(self, state, action_text):
        return {
            "narration": f"You {action_text}.", "health_delta": 0,
            "inventory_add": [], "inventory_update": [], "inventory_remove": [],
        }


class LongScriptedUI:
    def __init__(self, n_actions):
        self.actions = [f"do thing {i}" for i in range(n_actions)] + ["end"]
        self.i = 0

    def freeplay_clear(self): pass
    def freeplay_title(self): pass
    def freeplay_prompt_line(self, prompt_text):
        return "" if "goal" in prompt_text.lower() else "a quiet room"
    def freeplay_print(self, text): pass
    def freeplay_print_hint(self): pass
    def freeplay_read_action(self):
        action = self.actions[self.i]
        self.i += 1
        return action
    def freeplay_print_stats(self, state): pass
    def freeplay_any_key(self): pass
    def freeplay_print_ending(self, text, tier): pass


def test_live_session_triggers_summary_without_crashing():
    ai = PlayableFakeAI()
    ui = LongScriptedUI(n_actions=SUMMARY_EVERY_N_TURNS + 2)
    final_state = play(ai, ui)
    assert final_state.ended is True
    assert final_state.summary != "", "summary should have been generated during a long enough session"
    print("test_live_session_triggers_summary_without_crashing OK")


if __name__ == "__main__":
    test_no_trigger_below_threshold()
    test_triggers_exactly_at_threshold()
    test_incorporates_previous_summary_in_prompt()
    test_live_session_triggers_summary_without_crashing()
    print("\nAll rolling-summary tests passed.")
