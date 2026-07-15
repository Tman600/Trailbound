import random
import sys
import types
import traceback

from engine import genres as genres_mod
from engine import events
from engine import endings
from engine.ai import LocalAI


class FakeUI:
    def __init__(self, rng):
        self.rng = rng

    def prompt_choice(self, question, options):
        return self.rng.randrange(len(options))

    def print_event(self, *a, **k): pass
    def print_story(self, *a, **k): pass
    def print_good(self, *a, **k): pass
    def print_bad(self, *a, **k): pass
    def print_info(self, *a, **k): pass
    def print_landmark(self, *a, **k): pass
    def render_status(self, *a, **k): pass
    def pause(self, *a, **k): pass


def run_one(genre_id, seed, ai):
    rng = random.Random(seed)
    genre = genres_mod.get_genre(genre_id)
    state = events.new_game(genre, rng)
    ui_stub = FakeUI(rng)

    max_days = 2000
    days = 0
    while not state.ended and days < max_days:
        events.advance_day(state, genre, ai, ui_stub, rng)
        days += 1
        if events.is_wiped_out(state) or events.is_stranded(state) or events.has_arrived(state):
            tier, title, text = endings.finalize(state, genre, ai)
            assert tier in genre.endings, f"Unknown ending tier {tier} for {genre_id}"
            assert isinstance(text, str) and len(text) > 0
            return days, tier
    if days >= max_days:
        raise AssertionError(f"{genre_id} seed={seed} never ended within {max_days} days")
    return days, state.ending_key


def main():
    ai = LocalAI(enabled=False)  # force fallback text path for deterministic, fast testing
    results = {}
    failures = []
    for genre_id in genres_mod.GENRES.keys():
        results[genre_id] = []
        for seed in range(40):
            try:
                days, tier = run_one(genre_id, seed, ai)
                results[genre_id].append((seed, days, tier))
            except Exception as e:
                failures.append((genre_id, seed, str(e), traceback.format_exc()))

    print("=== Results by genre ===")
    for genre_id, runs in results.items():
        tiers = {}
        for _, _, t in runs:
            tiers[t] = tiers.get(t, 0) + 1
        avg_days = sum(d for _, d, _ in runs) / len(runs) if runs else 0
        print(f"{genre_id:12s} runs={len(runs):3d}  avg_days={avg_days:6.1f}  tiers={tiers}")

    if failures:
        print("\n=== FAILURES ===")
        for genre_id, seed, err, tb in failures[:5]:
            print(f"{genre_id} seed={seed}: {err}")
            print(tb)
        print(f"\nTOTAL FAILURES: {len(failures)}")
        sys.exit(1)
    else:
        print("\nAll runs completed without error. Every run reached a valid ending tier.")


if __name__ == "__main__":
    main()
