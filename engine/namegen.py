"""
Small procedural naming toolkit. Genres supply a noun bank + a handful of
patterns; this module combines them randomly so every run has fresh
landmark, destination, and character names.
"""
import random

FIRST_NAMES = [
    "Asa", "Bea", "Cass", "Dov", "Elin", "Farid", "Greta", "Hale", "Ines",
    "Jael", "Kian", "Lior", "Marta", "Noor", "Otis", "Priya", "Quinn",
    "Rhea", "Soren", "Tala", "Ulla", "Vik", "Wren", "Xu", "Yara", "Zeke",
    "Amos", "Birdie", "Cleo", "Dax", "Esme", "Finn", "Goldie", "Hux",
    "Iris", "Jonas", "Kira", "Lux", "Moss", "Nadia",
]


def make_name(rng: random.Random, patterns: list, noun_bank: list) -> str:
    pattern = rng.choice(patterns)
    noun = rng.choice(noun_bank)
    return pattern.format(n=noun)


def make_unique_names(rng: random.Random, patterns: list, noun_bank: list, count: int) -> list:
    seen = set()
    out = []
    attempts = 0
    while len(out) < count and attempts < count * 20:
        attempts += 1
        name = make_name(rng, patterns, noun_bank)
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


def make_party_names(rng: random.Random, count: int) -> list:
    pool = FIRST_NAMES.copy()
    rng.shuffle(pool)
    return pool[:count]
