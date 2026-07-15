"""
The simulation heart of Trailbound. Genres only supply data (engine/genres.py);
every mechanic below is genre-agnostic and reads flavor/names out of the
Genre object passed in.
"""
import random
from . import namegen
from .state import GameState, Character

PACE_SPEED = {"grueling": (20, 28), "steady": (14, 20), "cautious": (9, 15)}
PACE_WEAR = {"grueling": (1, 4), "steady": (0, 2), "cautious": (0, 1)}
RATION_FOOD_USE = {"bare": 1, "meager": 2, "filling": 3}
RATION_HEALTH_REGEN = {"bare": -1, "meager": 1, "filling": 3}

CROSSING_THRESHOLDS = [0.20, 0.40, 0.60, 0.80]

EVENT_WEIGHTS = {
    "quiet": 10, "injury": 8, "illness": 9, "hostile": 7, "wildlife": 7,
    "breakdown": 7, "find": 18, "trade": 10, "morale_good": 12,
    "morale_bad": 8, "theft": 5, "rare": 2,
}

# Pace is a real risk/reward choice: grueling covers ground fast but courts
# danger; cautious is slower but meaningfully safer; steady is the baseline.
RISK_KINDS = {"injury", "illness", "hostile", "wildlife", "breakdown", "theft"}
SAFE_KINDS = {"quiet", "find", "morale_good"}
PACE_RISK_MULT = {"grueling": 1.35, "steady": 1.0, "cautious": 0.7}
PACE_SAFE_MULT = {"grueling": 0.8, "steady": 1.0, "cautious": 1.3}


def _event_weights_for_pace(pace: str, exclude_rare: bool) -> dict:
    weights = {}
    for kind, base in EVENT_WEIGHTS.items():
        if exclude_rare and kind == "rare":
            continue
        w = base
        if kind in RISK_KINDS:
            w *= PACE_RISK_MULT.get(pace, 1.0)
        elif kind in SAFE_KINDS:
            w *= PACE_SAFE_MULT.get(pace, 1.0)
        weights[kind] = w
    return weights


def narrate(ai, genre, flavor, max_tokens=60):
    system = ("You are a terse, atmospheric survival-journey narrator. "
              "Write 1-3 sentences, present tense, no dialogue, no headers, no repeating the input verbatim.")
    prompt = (f"Genre: {genre.name} (\"{genre.tagline}\"). Moment happening now: {flavor} "
              f"Continue naturally in the same tone and add one small vivid, concrete detail.")
    return ai.generate(prompt, system=system, fallback=flavor, max_tokens=max_tokens)


# ---------------------------------------------------------- free-text actions --
# Bounds match the scale of the scripted events above -- no amount of creative
# prompting can push a single moment's effect outside these ranges.
_ACTION_CLAMPS = {
    "money_delta": (-150, 220),
    "food_delta": (-70, 100),
    "special_resource_delta": (-15, 22),
    "vehicle_health_delta": (-32, 40),
    "morale_delta": (-20, 20),
    "distance_delta": (-20, 26),
    "target_health_delta": (-32, 26),
}


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def apply_ai_result(state, genre, ui, rng, result: dict, action_text: str):
    narration = result.get("narration")
    narration = str(narration) if narration else "The moment passes without much changing."
    ui.print_event(narration, title="Your Move")

    deltas = {k: _clamp(_safe_int(result.get(k, 0)), *bounds) for k, bounds in _ACTION_CLAMPS.items()}

    state.money = max(0, state.money + deltas["money_delta"])
    state.food = max(0, state.food + deltas["food_delta"])
    state.special_resource = max(0, state.special_resource + deltas["special_resource_delta"])
    state.vehicle_health = max(0, min(100, state.vehicle_health + deltas["vehicle_health_delta"]))
    state.morale = max(0, min(100, state.morale + deltas["morale_delta"]))
    state.distance_traveled = max(0.0, state.distance_traveled + deltas["distance_delta"])

    alive = state.alive_party()
    if deltas["target_health_delta"] != 0 and alive:
        target_name = str(result.get("target") or "")
        target = next((c for c in alive if c.name == target_name), None) or rng.choice(alive)
        target.apply_health_delta(deltas["target_health_delta"])
        if not target.alive:
            ui.print_bad(f"{target.name} does not survive.")
            state.note(f"{target.name} has died.")

    summary = []
    if deltas["money_delta"]:
        summary.append(f"{deltas['money_delta']:+d} {genre.currency}")
    if deltas["food_delta"]:
        summary.append(f"{deltas['food_delta']:+d} {genre.food_name}")
    if deltas["special_resource_delta"]:
        summary.append(f"{deltas['special_resource_delta']:+d} {genre.special_resource}")
    if deltas["vehicle_health_delta"]:
        summary.append(f"{deltas['vehicle_health_delta']:+d} {genre.vehicle} condition")
    if deltas["morale_delta"]:
        summary.append(f"{deltas['morale_delta']:+d} morale")
    if deltas["distance_delta"]:
        summary.append(f"{deltas['distance_delta']:+d} distance")
    ui.print_action_effects(summary)
    state.note(f"You chose to: {action_text}")


def try_free_text(state, genre, ai, ui, rng, situation: str, hint: str = None) -> bool:
    """If local AI is available, offer a free-text prompt. Returns True if the
    player typed something and it was fully handled (narrated + applied) --
    callers should stop and return. Returns False if the player pressed Enter
    (or AI is unavailable), meaning: fall through to the scripted logic below."""
    if not ai.available:
        return False
    action = ui.prompt_action(hint)
    if not action:
        return False
    result = ai.interpret_action(genre, state, situation, action)
    apply_ai_result(state, genre, ui, rng, result, action)
    return True


def new_game(genre, rng: random.Random) -> GameState:
    party_size = rng.randint(3, 5)
    names = namegen.make_party_names(rng, party_size)
    roles = rng.sample(genre.role_bank, min(party_size, len(genre.role_bank)))
    while len(roles) < party_size:
        roles.append(rng.choice(genre.role_bank))
    party = [Character(name=n, role=r, health=100) for n, r in zip(names, roles)]

    destination = namegen.make_name(rng, genre.destination_patterns, genre.noun_bank)

    state = GameState(
        genre_id=genre.id,
        money=rng.randint(700, 1300),
        food=rng.randint(90, 150),
        special_resource=rng.randint(15, 30),
        vehicle_health=100,
        morale=rng.randint(60, 82),
        pace="steady",
        rations="meager",
        party=party,
        total_distance=float(rng.randint(1400, 2200)),
    )
    state.next_landmark_at = float(rng.randint(120, 220))
    state.flags["destination_name"] = destination
    state.flags[genre.secret_flag] = False
    for i in range(len(CROSSING_THRESHOLDS)):
        state.flags[f"crossing_{i}"] = False
    state.note(f"Set out from {genre.origin} toward {destination}.")
    return state


def is_wiped_out(state: GameState) -> bool:
    return len(state.alive_party()) == 0


def is_stranded(state: GameState) -> bool:
    return state.vehicle_health <= 0 and state.money <= 0 and state.special_resource <= 0


def has_arrived(state: GameState) -> bool:
    return state.distance_traveled >= state.total_distance


def advance_day(state: GameState, genre, ai, ui, rng: random.Random):
    """Advance one day of the journey: consumption, health, distance, wear,
    then resolve at most one of {crossing, landmark, random event}."""
    alive = state.alive_party()

    # --- food consumption & starvation ---
    consumption = RATION_FOOD_USE[state.rations] * max(1, len(alive))
    state.food -= consumption
    starving = state.food < 0
    if starving:
        state.food = 0

    # --- health drift ---
    if starving:
        for c in alive:
            c.apply_health_delta(rng.randint(-14, -6))
        state.morale = max(0, state.morale - rng.randint(4, 9))
        ui.print_bad(f"{genre.food_name.capitalize()} run out. The party goes hungry.")
    else:
        base = RATION_HEALTH_REGEN[state.rations]
        for c in alive:
            c.apply_health_delta(base + rng.randint(-2, 2))

    newly_dead = [c for c in alive if not c.alive]
    for c in newly_dead:
        ui.print_bad(f"{c.name} does not survive the journey.")
        state.note(f"{c.name} has died.")
        state.morale = max(0, state.morale - rng.randint(8, 16))

    # --- distance & wear ---
    lo, hi = PACE_SPEED[state.pace]
    speed = rng.randint(lo, hi)
    if state.vehicle_health <= 30:
        speed = max(3, speed - 10)
    elif state.vehicle_health <= 60:
        speed = max(4, speed - 5)
    state.distance_traveled += speed

    wlo, whi = PACE_WEAR[state.pace]
    state.vehicle_health = max(0, state.vehicle_health - rng.randint(wlo, whi))

    state.day += 1
    if is_wiped_out(state) or is_stranded(state) or has_arrived(state):
        return

    # --- one big beat per day, priority: crossing > landmark > random event ---
    frac = state.progress_fraction()
    for i, threshold in enumerate(CROSSING_THRESHOLDS):
        if frac >= threshold and not state.flags.get(f"crossing_{i}"):
            state.flags[f"crossing_{i}"] = True
            resolve_crossing(state, genre, ai, ui, rng)
            return

    if state.distance_traveled >= state.next_landmark_at:
        state.landmarks_passed += 1
        state.next_landmark_at += rng.randint(140, 230)
        resolve_landmark(state, genre, ai, ui, rng)
        return

    kind = _weighted_choice(rng, _event_weights_for_pace(
        state.pace, exclude_rare=state.flags.get(genre.secret_flag) is True))
    if kind == "quiet":
        return
    _RESOLVERS[kind](state, genre, ai, ui, rng)


def _weighted_choice(rng: random.Random, weights: dict) -> str:
    keys = list(weights.keys())
    vals = list(weights.values())
    return rng.choices(keys, weights=vals, k=1)[0]


# ------------------------------------------------------------ auto events --
def resolve_injury(state, genre, ai, ui, rng):
    alive = state.alive_party()
    if not alive:
        return
    victim = rng.choice(alive)
    flavor = rng.choice(genre.flavor["injury"]).format(name=victim.name)
    text = narrate(ai, genre, flavor)
    ui.print_event(text, title="Injury")
    if try_free_text(state, genre, ai, ui, rng, text, hint="e.g. tend to them, keep moving, use supplies"):
        ui.pause()
        return
    victim.apply_health_delta(-rng.randint(10, 24))
    state.note(f"{victim.name} was injured.")
    ui.pause()


def resolve_illness(state, genre, ai, ui, rng):
    alive = state.alive_party()
    if not alive:
        return
    victim = rng.choice(alive)
    flavor = rng.choice(genre.flavor["illness"]).format(name=victim.name)
    text = narrate(ai, genre, flavor)
    ui.print_event(text, title="Illness")
    if try_free_text(state, genre, ai, ui, rng, text, hint="e.g. rest them, treat it, push on regardless"):
        ui.pause()
        return
    severity = rng.randint(8, 22)
    if state.rations == "bare":
        severity += 6
    victim.apply_health_delta(-severity)
    victim.days_sick += 1
    state.note(f"{victim.name} fell ill.")
    ui.pause()


def resolve_find(state, genre, ai, ui, rng):
    flavor = rng.choice(genre.flavor["find"])
    text = narrate(ai, genre, flavor)
    ui.print_event(text, title="A Stroke of Luck")
    if try_free_text(state, genre, ai, ui, rng, text, hint="e.g. how you use or share this"):
        ui.pause()
        return
    roll = rng.random()
    if roll < 0.5:
        amt = rng.randint(30, 70)
        state.food += amt
        ui.print_good(f"+{amt} {genre.food_name}")
    elif roll < 0.8:
        amt = rng.randint(40, 120)
        state.money += amt
        ui.print_good(f"+{amt} {genre.currency}")
    else:
        amt = rng.randint(4, 12)
        state.special_resource += amt
        ui.print_good(f"+{amt} {genre.special_resource}")
    state.morale = min(100, state.morale + rng.randint(1, 5))
    ui.pause()


def resolve_morale_good(state, genre, ai, ui, rng):
    flavor = rng.choice(genre.flavor["morale_good"])
    text = narrate(ai, genre, flavor)
    ui.print_event(text, title="Good Spirits")
    if try_free_text(state, genre, ai, ui, rng, text):
        ui.pause()
        return
    state.morale = min(100, state.morale + rng.randint(6, 14))
    ui.pause()


def resolve_morale_bad(state, genre, ai, ui, rng):
    flavor = rng.choice(genre.flavor["morale_bad"])
    text = narrate(ai, genre, flavor)
    ui.print_event(text, title="Low Spirits")
    if try_free_text(state, genre, ai, ui, rng, text):
        ui.pause()
        return
    state.morale = max(0, state.morale - rng.randint(6, 14))
    ui.pause()


def resolve_theft(state, genre, ai, ui, rng):
    flavor = rng.choice(genre.flavor["theft"])
    text = narrate(ai, genre, flavor)
    ui.print_event(text, title="Theft")
    if try_free_text(state, genre, ai, ui, rng, text, hint="e.g. give chase, let it go, raise the alarm"):
        ui.pause()
        return
    roll = rng.random()
    if roll < 0.5 and state.money > 0:
        amt = min(state.money, rng.randint(20, 80))
        state.money -= amt
        ui.print_bad(f"-{amt} {genre.currency}")
    else:
        amt = min(state.food, rng.randint(10, 35))
        state.food -= amt
        ui.print_bad(f"-{amt} {genre.food_name}")
    ui.pause()


def resolve_rare(state, genre, ai, ui, rng):
    if state.flags.get(genre.secret_flag) or rng.random() > 0.3:
        # Either already found, or this near-miss doesn't pan out -- still a nice find.
        resolve_find(state, genre, ai, ui, rng)
        return
    state.flags[genre.secret_flag] = True
    flavor = rng.choice(genre.flavor["rare"])
    text = narrate(ai, genre, flavor, max_tokens=90)
    ui.print_event(text, title="A Rare Discovery")
    state.food += rng.randint(30, 60)
    state.money += rng.randint(80, 200)
    state.special_resource += rng.randint(8, 18)
    state.morale = min(100, state.morale + 10)
    state.note(genre.secret_trigger_text)
    ui.print_good("The party is well provisioned for what's ahead.")
    ui.pause()


# ------------------------------------------------------------- choice events --
def resolve_hostile(state, genre, ai, ui, rng):
    flavor = rng.choice(genre.flavor["hostile"]).format(hostile=genre.hostile_name)
    text = narrate(ai, genre, flavor)
    ui.print_event(text, title=f"{genre.hostile_name.title()}")
    if try_free_text(state, genre, ai, ui, rng, text, hint="e.g. fight, flee, negotiate"):
        ui.pause()
        return
    choice = ui.prompt_choice("How do you respond?", [
        f"Stand and fight (risks health, costs {genre.special_resource})",
        "Try to slip away",
        f"Pay them off (costs {genre.currency})",
    ])
    alive = state.alive_party()
    if choice == 0:
        if state.special_resource >= 5 and rng.random() < 0.5 + state.morale / 400:
            spent = min(state.special_resource, rng.randint(3, 8))
            state.special_resource -= spent
            ui.print_good(f"The {genre.hostile_name} are driven off. -{spent} {genre.special_resource}")
            state.morale = min(100, state.morale + 4)
        else:
            victim = rng.choice(alive) if alive else None
            if victim:
                dmg = rng.randint(14, 28)
                victim.apply_health_delta(-dmg)
                ui.print_bad(f"The fight goes badly. {victim.name} is hurt.")
            state.special_resource = max(0, state.special_resource - rng.randint(2, 6))
            state.note(f"Fought {genre.hostile_name} and paid for it.")
    elif choice == 1:
        if rng.random() < 0.6:
            wear = rng.randint(6, 16)
            state.vehicle_health = max(0, state.vehicle_health - wear)
            ui.print_good(f"The party slips away, though the {genre.vehicle} takes a beating (-{wear}).")
        else:
            loss = rng.randint(8, 24)
            state.food = max(0, state.food - loss)
            ui.print_bad(f"The escape costs supplies. -{loss} {genre.food_name}")
    else:
        cost = rng.randint(25, 70)
        if state.money >= cost:
            state.money -= cost
            ui.print_good(f"Paying {cost} {genre.currency} keeps the peace.")
        else:
            loss = rng.randint(12, 32)
            state.food = max(0, state.food - loss)
            ui.print_bad(f"Not enough {genre.currency} to pay -- they take supplies instead. -{loss} {genre.food_name}")
    ui.pause()


def resolve_wildlife(state, genre, ai, ui, rng):
    flavor = rng.choice(genre.flavor["wildlife"]).format(wildlife=genre.wildlife_name)
    text = narrate(ai, genre, flavor)
    ui.print_event(text, title=genre.wildlife_name.title())
    if try_free_text(state, genre, ai, ui, rng, text, hint="e.g. drive them off, keep your distance"):
        ui.pause()
        return
    choice = ui.prompt_choice("What do you do?", [
        f"Drive them off (costs {genre.special_resource})",
        "Keep your distance and wait it out",
    ])
    alive = state.alive_party()
    if choice == 0 and state.special_resource >= 2:
        spent = min(state.special_resource, rng.randint(2, 6))
        state.special_resource -= spent
        if rng.random() < 0.75:
            ui.print_good(f"The {genre.wildlife_name} scatter. -{spent} {genre.special_resource}")
        else:
            victim = rng.choice(alive) if alive else None
            if victim:
                victim.apply_health_delta(-rng.randint(8, 18))
                ui.print_bad(f"{victim.name} is hurt in the scuffle.")
    else:
        if rng.random() < 0.7:
            ui.print_good(f"The {genre.wildlife_name} move on without incident.")
        else:
            loss = rng.randint(5, 18)
            state.food = max(0, state.food - loss)
            ui.print_bad(f"They get into the stores before moving on. -{loss} {genre.food_name}")
    ui.pause()


def resolve_breakdown(state, genre, ai, ui, rng):
    dmg = rng.randint(10, 25)
    state.vehicle_health = max(0, state.vehicle_health - dmg)
    flavor = rng.choice(genre.flavor["breakdown"])
    text = narrate(ai, genre, flavor)
    ui.print_event(text, title=f"{genre.vehicle.title()} Trouble")
    if try_free_text(state, genre, ai, ui, rng, text, hint="e.g. repair it, patch it, push on"):
        ui.pause()
        return
    choice = ui.prompt_choice(f"The {genre.vehicle} is damaged ({state.vehicle_health}/100). What now?", [
        f"Full repair ({genre.special_resource} + {genre.currency})",
        "Quick patch (cheap, less effective)",
        "Push on without repairs",
    ])
    if choice == 0 and state.special_resource >= 6 and state.money >= 40:
        state.special_resource -= 6
        state.money -= 40
        restored = rng.randint(25, 40)
        state.vehicle_health = min(100, state.vehicle_health + restored)
        ui.print_good(f"Solid repair job. +{restored} condition.")
    elif choice == 1 and state.money >= 15:
        state.money -= 15
        restored = rng.randint(8, 16)
        state.vehicle_health = min(100, state.vehicle_health + restored)
        ui.print_good(f"A rough patch holds for now. +{restored} condition.")
    else:
        ui.print_bad(f"No repairs made. The {genre.vehicle} stays weakened.")
    ui.pause()


def resolve_crossing(state, genre, ai, ui, rng):
    flavor = rng.choice(genre.flavor["crossing"])
    text = narrate(ai, genre, flavor, max_tokens=80)
    ui.print_event(text, title="A Hard Crossing")
    if try_free_text(state, genre, ai, ui, rng, text, hint="e.g. the safe route, the risky shortcut"):
        ui.pause()
        return
    choice = ui.prompt_choice("How do you cross?", [
        "Take the safe, slow route",
        "Risk the shortcut",
    ])
    alive = state.alive_party()
    if choice == 0:
        state.distance_traveled = max(0, state.distance_traveled - rng.randint(4, 10))
        ui.print_good("Slower, but everyone makes it across safely.")
    else:
        if rng.random() < 0.55:
            state.distance_traveled += rng.randint(10, 20)
            ui.print_good("The shortcut pays off -- real time saved.")
        else:
            dmg = rng.randint(12, 24)
            state.vehicle_health = max(0, state.vehicle_health - dmg)
            victim = rng.choice(alive) if alive and rng.random() < 0.5 else None
            if victim:
                victim.apply_health_delta(-rng.randint(10, 20))
                ui.print_bad(f"The shortcut turns rough. {victim.name} is hurt and the {genre.vehicle} takes damage.")
            else:
                ui.print_bad(f"The shortcut turns rough. The {genre.vehicle} takes damage.")
    ui.pause()


def resolve_trade(state, genre, ai, ui, rng):
    flavor = rng.choice(genre.flavor.get("trade", ["A trading opportunity presents itself."]))
    text = narrate(ai, genre, flavor)
    ui.print_event(text, title="Trade")
    if try_free_text(state, genre, ai, ui, rng, text, hint="e.g. what you want to buy, sell, or trade"):
        ui.pause()
        return
    price = rng.randint(2, 4)
    max_afford = state.money // price if price else 0
    if max_afford <= 0:
        ui.print_info(f"Nothing to trade with -- not enough {genre.currency}.")
        ui.pause()
        return
    choice = ui.prompt_choice("Trade?", [
        f"Buy {genre.food_name} ({price} {genre.currency} each)",
        "Move on",
    ])
    if choice == 0:
        qty = min(max_afford, rng.randint(50, 130))
        cost = qty * price
        state.money -= cost
        state.food += qty
        ui.print_good(f"Bought {qty} {genre.food_name} for {cost} {genre.currency}.")
    else:
        ui.print_info("You move on.")
    ui.pause()


def resolve_landmark(state, genre, ai, ui, rng):
    name = namegen.make_name(rng, genre.landmark_patterns, genre.noun_bank)
    ui.print_landmark(name)
    flavor = f"The party arrives at {name}, a waypoint on the journey to {state.flags.get('destination_name')}."
    text = narrate(ai, genre, flavor, max_tokens=80)
    ui.print_story(text, title=name)
    if try_free_text(state, genre, ai, ui, rng, text,
                      hint="e.g. rest here, trade, explore, push onward"):
        ui.pause()
        return

    options = [
        f"Rest & resupply (costs {genre.currency}, restores health & morale)",
        "Trade",
        "Push onward",
    ]
    special = None
    if genre.special_landmark_events and rng.random() < 0.4:
        special = rng.choice(genre.special_landmark_events)
        options.insert(0, f"Investigate: {special['name']}")

    choice = ui.prompt_choice("What does the party do?", options)

    if special is not None:
        if choice == 0:
            ui.print_story(special["prompt"], title=special["name"])
            go = ui.prompt_choice("Well?", ["Go ahead", "Leave it be"])
            if go == 0:
                if rng.random() < 0.6:
                    ui.print_good(special["good"])
                    state.food += rng.randint(10, 30)
                    state.money += rng.randint(20, 80)
                    state.morale = min(100, state.morale + 5)
                else:
                    ui.print_bad(special["bad"])
                    alive = state.alive_party()
                    if alive:
                        rng.choice(alive).apply_health_delta(-rng.randint(10, 22))
            ui.pause()
            return
        choice -= 1  # re-align to the standard menu below

    if choice == 0:
        cost = rng.randint(30, 90)
        if state.money >= cost:
            state.money -= cost
            for c in state.alive_party():
                c.apply_health_delta(rng.randint(8, 18))
            state.morale = min(100, state.morale + rng.randint(8, 16))
            restock = rng.randint(40, 90)
            state.food += restock
            ui.print_good(
                f"The party rests and restocks. -{cost} {genre.currency}, "
                f"+{restock} {genre.food_name}, health and morale restored."
            )
        else:
            ui.print_bad(f"Not enough {genre.currency} to rest properly here.")
    elif choice == 1:
        resolve_trade(state, genre, ai, ui, rng)
        return
    else:
        ui.print_info("The party pushes onward without stopping.")
    ui.pause()


_RESOLVERS = {
    "injury": resolve_injury,
    "illness": resolve_illness,
    "hostile": resolve_hostile,
    "wildlife": resolve_wildlife,
    "breakdown": resolve_breakdown,
    "find": resolve_find,
    "trade": resolve_trade,
    "morale_good": resolve_morale_good,
    "morale_bad": resolve_morale_bad,
    "theft": resolve_theft,
    "rare": resolve_rare,
}
