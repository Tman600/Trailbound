import random
from engine import genres as genres_mod
from engine import events

genre = genres_mod.get_genre("western")


class FakeAI:
    """Simulates LocalAI.interpret_action with scripted responses, and
    LocalAI.generate for the atmospheric narrate() calls."""
    available = True

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def generate(self, prompt, system="", fallback="", max_tokens=60):
        return fallback  # keep atmospheric narration deterministic for the test

    def interpret_action(self, genre, state, situation, action_text):
        resp = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        return resp


class ScriptedUI:
    """Feeds one free-text action, then blanks (to fall through to menus /
    defaults on any subsequent internal prompts within the same resolver)."""
    def __init__(self, rng, first_action="I try something bold"):
        self.rng = rng
        self.first_action = first_action
        self.asked = 0

    def prompt_action(self, hint=None):
        self.asked += 1
        return self.first_action if self.asked == 1 else ""

    def prompt_choice(self, question, options):
        return 0

    def print_event(self, *a, **k): pass
    def print_story(self, *a, **k): pass
    def print_good(self, *a, **k): pass
    def print_bad(self, *a, **k): pass
    def print_info(self, *a, **k): pass
    def print_landmark(self, *a, **k): pass
    def print_action_effects(self, *a, **k): pass
    def render_status(self, *a, **k): pass
    def pause(self, *a, **k): pass


def make_state(rng):
    return events.new_game(genre, rng)


def test_normal_response():
    rng = random.Random(1)
    state = make_state(rng)
    ai = FakeAI([{
        "narration": "You size up the situation and act decisively.",
        "money_delta": 50, "food_delta": 20, "special_resource_delta": 5,
        "vehicle_health_delta": -5, "morale_delta": 8, "distance_delta": 10,
        "target": state.party[0].name, "target_health_delta": -10,
    }])
    ui = ScriptedUI(rng)
    before_money = state.money
    before_health = state.party[0].health
    handled = events.try_free_text(state, genre, ai, ui, rng, "a hostile encounter")
    assert handled is True
    assert state.money == before_money + 50
    assert state.party[0].health == before_health - 10
    print("test_normal_response OK")


def test_extreme_values_get_clamped():
    rng = random.Random(2)
    state = make_state(rng)
    before_morale = state.morale
    ai = FakeAI([{
        "narration": "You attempt something absurd.",
        "money_delta": 999999, "food_delta": -999999, "special_resource_delta": 999999,
        "vehicle_health_delta": 999999, "morale_delta": -999999, "distance_delta": 999999,
        "target": "", "target_health_delta": -999999,
    }])
    ui = ScriptedUI(rng)
    events.try_free_text(state, genre, ai, ui, rng, "a moment")
    assert state.money <= 220 + 1300  # starting money + clamp ceiling, sanity bound
    assert state.vehicle_health == 100  # clamped to [0,100]
    assert state.morale == max(0, before_morale - 20)  # morale_delta clamped to -20
    assert 0 <= state.morale <= 100
    print("test_extreme_values_get_clamped OK")


def test_missing_and_malformed_keys():
    rng = random.Random(3)
    state = make_state(rng)
    ai = FakeAI([{"narration": "Something happens."}])  # all deltas missing
    ui = ScriptedUI(rng)
    before = (state.money, state.food, state.vehicle_health, state.morale, state.distance_traveled)
    events.try_free_text(state, genre, ai, ui, rng, "a moment")
    after = (state.money, state.food, state.vehicle_health, state.morale, state.distance_traveled)
    assert before == after, "missing keys should default to zero effect"
    print("test_missing_and_malformed_keys OK")


def test_bad_types_do_not_crash():
    rng = random.Random(4)
    state = make_state(rng)
    ai = FakeAI([{
        "narration": None,  # not even a string
        "money_delta": "lots", "food_delta": [1, 2, 3], "special_resource_delta": None,
        "vehicle_health_delta": {}, "morale_delta": "up", "distance_delta": "far",
        "target": 12345, "target_health_delta": "ouch",
    }])
    ui = ScriptedUI(rng)
    # Should not raise.
    events.try_free_text(state, genre, ai, ui, rng, "a moment")
    print("test_bad_types_do_not_crash OK")


def test_invalid_target_falls_back_to_random_alive():
    rng = random.Random(5)
    state = make_state(rng)
    ai = FakeAI([{
        "narration": "Someone gets hurt.",
        "money_delta": 0, "food_delta": 0, "special_resource_delta": 0,
        "vehicle_health_delta": 0, "morale_delta": 0, "distance_delta": 0,
        "target": "NotARealPartyMember", "target_health_delta": -15,
    }])
    ui = ScriptedUI(rng)
    total_health_before = sum(c.health for c in state.alive_party())
    events.try_free_text(state, genre, ai, ui, rng, "a moment")
    total_health_after = sum(c.health for c in state.alive_party())
    assert total_health_after == total_health_before - 15
    print("test_invalid_target_falls_back_to_random_alive OK")


def test_blank_input_falls_through():
    rng = random.Random(6)
    state = make_state(rng)
    ai = FakeAI([{}])

    class BlankUI(ScriptedUI):
        def prompt_action(self, hint=None):
            return ""  # player just pressed Enter

    ui = BlankUI(rng)
    handled = events.try_free_text(state, genre, ai, ui, rng, "a moment")
    assert handled is False
    assert ai.calls == 0, "AI should not even be consulted when input is blank"
    print("test_blank_input_falls_through OK")


def test_ai_unavailable_skips_entirely():
    rng = random.Random(7)
    state = make_state(rng)

    class UnavailableAI(FakeAI):
        available = False

    ai = UnavailableAI([{}])
    ui = ScriptedUI(rng)
    handled = events.try_free_text(state, genre, ai, ui, rng, "a moment")
    assert handled is False
    print("test_ai_unavailable_skips_entirely OK")


def test_full_resolver_integration():
    """Run every choice-based resolver through the free-text path end to end."""
    rng = random.Random(8)
    state = make_state(rng)
    ai = FakeAI([{
        "narration": "It goes about as well as can be expected.",
        "money_delta": 5, "food_delta": 5, "special_resource_delta": 1,
        "vehicle_health_delta": -2, "morale_delta": 2, "distance_delta": 3,
        "target": "", "target_health_delta": 0,
    }] * 20)
    ui = ScriptedUI(rng)
    for fn in [events.resolve_injury, events.resolve_illness, events.resolve_hostile,
               events.resolve_wildlife, events.resolve_breakdown, events.resolve_crossing,
               events.resolve_trade, events.resolve_find, events.resolve_morale_good,
               events.resolve_morale_bad, events.resolve_theft, events.resolve_landmark]:
        ui.asked = 0  # reset so each resolver gets a fresh "typed action"
        fn(state, genre, ai, ui, rng)
    print("test_full_resolver_integration OK")


if __name__ == "__main__":
    test_normal_response()
    test_extreme_values_get_clamped()
    test_missing_and_malformed_keys()
    test_bad_types_do_not_crash()
    test_invalid_target_falls_back_to_random_alive()
    test_blank_input_falls_through()
    test_ai_unavailable_skips_entirely()
    test_full_resolver_integration()
    print("\nAll free-text action tests passed.")
