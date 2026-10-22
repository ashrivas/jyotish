"""Explicit, inspectable definitions; disputed node dignities are intentionally absent."""

from app.astro.angles import separation
from app.astro.constants import SIGN_LORDS

EXALT = {
    "sun": (0, 10),
    "moon": (1, 3),
    "mars": (9, 28),
    "mercury": (5, 15),
    "jupiter": (3, 5),
    "venus": (11, 27),
    "saturn": (6, 20),
}
MOOLA = {
    "sun": (4, 0, 20),
    "moon": (1, 3, 30),
    "mars": (0, 0, 12),
    "mercury": (5, 15, 20),
    "jupiter": (8, 0, 10),
    "venus": (6, 0, 15),
    "saturn": (10, 0, 20),
}
FRIENDS = {
    "sun": ("moon", "mars", "jupiter"),
    "moon": ("sun", "mercury"),
    "mars": ("sun", "moon", "jupiter"),
    "mercury": ("sun", "venus"),
    "jupiter": ("sun", "moon", "mars"),
    "venus": ("mercury", "saturn"),
    "saturn": ("mercury", "venus"),
}
ENEMIES = {
    "sun": ("venus", "saturn"),
    "moon": (),
    "mars": ("mercury",),
    "mercury": ("moon",),
    "jupiter": ("mercury", "venus"),
    "venus": ("sun", "moon"),
    "saturn": ("sun", "moon", "mars"),
}


def compound(a: str, b: str, positions: dict) -> str:
    natural = 1 if b in FRIENDS[a] else -1 if b in ENEMIES[a] else 0
    house = (positions[b]["sign_index"] - positions[a]["sign_index"]) % 12 + 1
    temporary = 1 if house in (2, 3, 4, 10, 11, 12) else -1
    return {-2: "great_enemy", -1: "enemy", 0: "neutral", 1: "friend", 2: "great_friend"}[natural + temporary]


def attributes(positions: dict, lagna: dict | None) -> dict:
    out = {}
    for name, p in positions.items():
        if name not in EXALT:
            out[name] = {
                "dignity": "not_adopted_for_nodes",
                "aspects": [],
                "reason": "Node dignities and aspects require an explicit school decision.",
            }
            continue
        s, degree = p["sign_index"], p["degree_in_sign"]
        exalt, deep = EXALT[name]
        m_sign, low, high = MOOLA[name]
        dignity = (
            "moolatrikona"
            if s == m_sign and low <= degree < high
            else "exalted"
            if s == exalt
            else "debilitated"
            if s == (exalt + 6) % 12
            else "own"
            if SIGN_LORDS[s] == name
            else "other"
        )
        aspect_houses = {"mars": (4, 7, 8), "jupiter": (5, 7, 9), "saturn": (3, 7, 10)}.get(name, (7,))
        out[name] = {
            "dignity": dignity,
            "sign_lord": SIGN_LORDS[s],
            "compound_relationship_to_sign_lord": "self"
            if SIGN_LORDS[s] == name
            else compound(name, SIGN_LORDS[s], positions),
            "deep_exaltation_longitude": exalt * 30 + deep,
            "uchcha_bala_virupas": separation(p["longitude"], ((exalt + 6) % 12) * 30 + deep) / 3,
            "owns_houses": [
                (i - lagna["sign_index"]) % 12 + 1 for i, lord in enumerate(SIGN_LORDS) if lord == name
            ]
            if lagna
            else [],
            "aspects": [{"sign_index": (s + h - 1) % 12, "aspect_number": h} for h in aspect_houses],
            "aspects_definition": "full sign-based graha drishti; not continuous drik bala",
        }
    return out
