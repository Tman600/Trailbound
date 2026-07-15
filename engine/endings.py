"""
Every run ends -- there is no infinite trail. This module decides *which*
of a genre's five ending tiers a run earned, then asks the local AI (or
falls back to hand-written genre copy) to narrate it.
"""
from .events import is_wiped_out, is_stranded, has_arrived


def determine_cause(state) -> str:
    """Only meaningful when the run ended in the 'tragic' tier."""
    if is_wiped_out(state):
        return "wiped_out"
    if is_stranded(state):
        return "stranded"
    return "timeout"


def determine_tier(state, genre) -> str:
    if is_wiped_out(state) or is_stranded(state) or not has_arrived(state):
        return "tragic"

    total = len(state.party)
    alive = state.alive_party()
    survivors_fraction = (len(alive) / total) if total else 0
    avg_health = (sum(c.health for c in alive) / len(alive)) if alive else 0
    score = survivors_fraction * 55 + (avg_health / 100) * 25 + (state.vehicle_health / 100) * 20

    if state.flags.get(genre.secret_flag):
        return "secret"
    if score >= 78:
        return "triumphant"
    if score >= 48:
        return "success"
    return "bittersweet"


_STRANDED_FALLBACK = (
    "The {vehicle} won't move another mile, and there's nothing left to trade, repair, or bargain "
    "with. Every one of the {survivor_count} who set out is still standing -- just nowhere near "
    "{destination}, with no way left to close the distance."
)
_TIMEOUT_FALLBACK = (
    "The journey drags on so long that {destination} starts to feel like a rumor. The {vehicle} "
    "keeps moving, but the road behaves like it has no end."
)


def narrate_ending(state, genre, ai, tier: str):
    ending_def = genre.endings[tier]
    destination = state.flags.get("destination_name", "the destination")
    survivors = state.alive_party()
    lost = [c.name for c in state.party if not c.alive]
    cause = determine_cause(state) if tier == "tragic" else None

    if cause == "stranded":
        fallback = _STRANDED_FALLBACK.format(vehicle=genre.vehicle, destination=destination,
                                              survivor_count=len(survivors))
        cause_note = ("The party is fully alive and in reasonable health -- the journey failed "
                       "because the vehicle broke down for good with no money, materials, or "
                       "supplies left to fix it or press on. This is a stranding, not a death toll.")
    elif cause == "timeout":
        fallback = _TIMEOUT_FALLBACK.format(vehicle=genre.vehicle, destination=destination)
        cause_note = "The journey simply never reached its destination in a reasonable time."
    else:
        fallback = ending_def["fallback"].format(destination=destination)
        cause_note = "The party was lost along the way." if cause == "wiped_out" else ""

    recent_log = "; ".join(state.log[-6:])
    system = ("You are a literary narrator closing out a survival-journey story. "
              "Write exactly 3-5 sentences of closing narration. No headers, no dialogue, "
              "no bullet points, no meta-commentary -- just prose that lands the ending, "
              "and make sure it matches the stated cause exactly.")
    prompt = (
        f"Genre: {genre.name} (\"{genre.tagline}\").\n"
        f"Ending type: {ending_def['title']} (tier: {tier}).\n"
        f"Destination: {destination}. Origin: {genre.origin}.\n"
        f"Party started with {len(state.party)} people; survivors now: {len(survivors)}.\n"
        f"Names lost along the way: {', '.join(lost) if lost else 'none'}.\n"
        f"Cause of this ending: {cause_note if cause_note else 'a successful arrival.'}\n"
        f"Recent events: {recent_log if recent_log else 'a quiet final stretch'}.\n"
        f"Write the closing narration now."
    )
    text = ai.generate(prompt, system=system, fallback=fallback, max_tokens=180)
    return ending_def["title"], text


def finalize(state, genre, ai):
    tier = determine_tier(state, genre)
    title, text = narrate_ending(state, genre, ai, tier)
    state.ended = True
    state.ending_key = tier
    state.ending_text = text
    return tier, title, text
