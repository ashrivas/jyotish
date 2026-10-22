"""Partition uncertainty windows at angular classification boundaries.

Unlike a vote on a four-minute sample grid, weights are elapsed-time fractions of
event-delimited intervals. They are NOT probabilities that the birth time is correct.
The event finder brackets at 20 seconds, refines crossings to 0.02 seconds, and
conservatively disables ascendant certification above 65 degrees latitude. This is
a numerical certificate under the stated bracketing assumptions, not exact algebra.
Dasha timing is deliberately not certified by this angular boundary procedure.
"""

from bisect import bisect_left, bisect_right
from collections import defaultdict
from datetime import datetime, timedelta
from fractions import Fraction
import json
from app.astro.constants import VARGAS, PLANETS
from app.astro.ephemeris import snapshot, longitude_at, speed_at
from app.astro.vargas import all_vargas
from app.models import ChartRequest

BOUNDARIES = sorted(
    {float(Fraction(s * 30) + Fraction(30 * k, d)) for s in range(12) for d in VARGAS for k in range(d)}
    | {float(Fraction(360 * k, 108)) for k in range(108)}
)
EXTENDED = [b + cycle * 360 for cycle in (-1, 0, 1, 2) for b in BOUNDARIES]


def angular_events(fn, start: datetime, end: datetime) -> list[datetime]:
    if start == end:
        return []
    events = []
    left = start
    angle = fn(left)
    while left < end:
        right = min(left + timedelta(seconds=20), end)
        right_angle = fn(right)
        delta = (right_angle - angle + 180) % 360 - 180
        target = angle + delta
        lo, hi = sorted((angle, target))
        thresholds = EXTENDED[bisect_right(EXTENDED, lo) : bisect_left(EXTENDED, hi)]
        for boundary in thresholds:
            a, b = left, right
            for _ in range(20):
                if (b - a).total_seconds() <= 0.02:
                    break
                middle = a + (b - a) / 2
                value = angle + (fn(middle) - angle + 180) % 360 - 180
                if (value < boundary) == (delta > 0):
                    a = middle
                else:
                    b = middle
            events.append(a + (b - a) / 2)
        # Include a crossing exactly at a scan endpoint; this is significant for synthetic tests.
        if delta and bisect_left(BOUNDARIES, right_angle) < len(BOUNDARIES) and right_angle in BOUNDARIES:
            events.append(right)
        left, angle = right, right_angle
    return events


def geometric_facts(snap: dict) -> dict:
    out = {}
    for name, body in {**snap["planets"], **({"lagna": snap["lagna"]} if snap["lagna"] else {})}.items():
        for field in ("sign_index", "nakshatra_index", "pada"):
            out[f"{name}.{field}"] = body[field]
        if name != "lagna":
            out[f"{name}.house"] = body["house"]
            out[f"{name}.retrograde"] = body["retrograde"]
        for division, sign in all_vargas(body["longitude"]).items():
            out[f"{name}.{division}.sign_index"] = sign
    return out


def station_events(speed, start: datetime, end: datetime) -> list[datetime]:
    """Bracket physical longitude-speed sign changes before looking for angular crossings."""
    events = []
    a, va = start, speed(start)
    while a < end:
        b = min(a + timedelta(seconds=20), end)
        vb = speed(b)
        if va * vb < 0:
            lo, hi = a, b
            for _ in range(20):
                if (hi - lo).total_seconds() <= 0.02:
                    break
                mid = lo + (hi - lo) / 2
                if (speed(mid) < 0) == (va < 0):
                    lo = mid
                else:
                    hi = mid
            events.append(lo + (hi - lo) / 2)
        elif vb == 0:
            events.append(b)
        a, va = b, vb
    return events


def robustness(request: ChartRequest, start: datetime, end: datetime, nominal: dict) -> dict:
    b, c = request.birth, request.conventions
    nominal_facts = geometric_facts(nominal)
    if start == end:
        return {
            "method": "single supplied instant",
            "event_count": 0,
            "window_start": start.isoformat(),
            "window_end": end.isoformat(),
            "coverage_complete": True,
            "facts": {
                k: {
                    "value": v,
                    "stability": "stable",
                    "nominal_duration_fraction": 1.0,
                    "alternatives": [{"value": v, "duration_fraction": 1.0}],
                }
                for k, v in nominal_facts.items()
            },
        }
    include_lagna = b.confidence != "unknown"
    high_latitude = abs(b.latitude) > 65 and include_lagna
    bodies = list(PLANETS[:-1]) + (["lagna"] if include_lagna and not high_latitude else [])
    events = [start, end]
    for name in bodies:
        fn = lambda instant, name=name: longitude_at(instant, name, b.latitude, b.longitude, c)
        stations = (
            []
            if name == "lagna"
            else station_events(lambda instant, name=name: speed_at(instant, name, c), start, end)
        )
        events.extend(stations)
        boundaries = [start, *stations, end]
        for a, z in zip(boundaries, boundaries[1:]):
            events.extend(angular_events(fn, a, z))
    cuts = sorted(set(events))
    totals = defaultdict(lambda: defaultdict(float))
    duration = (end - start).total_seconds()
    for a, z in zip(cuts, cuts[1:]):
        if a == z:
            continue
        sample = snapshot(a + (z - a) / 2, b.latitude, b.longitude, c, include_lagna)
        weight = (z - a).total_seconds() / duration
        for key, value in geometric_facts(sample).items():
            totals[key][json.dumps(value)] += weight
    facts = {}
    for key, value in nominal_facts.items():
        alternatives = [
            {"value": json.loads(v), "duration_fraction": round(w, 9)} for v, w in totals[key].items()
        ]
        fraction = totals[key].get(json.dumps(value), 0)
        uncertified = high_latitude and (key.startswith("lagna.") or key.endswith(".house"))
        unanimous = not uncertified and len(alternatives) == 1
        facts[key] = {
            "value": value,
            "stability": "stable" if unanimous else "not_certified" if uncertified else "time_sensitive",
            "nominal_duration_fraction": round(fraction, 9),
            "at_least_95_percent": fraction >= 0.95,
            "alternatives": alternatives,
        }
    return {
        "method": "angular boundary bracketing (20 s), bisection (0.02 s), duration-weighted intervals",
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "event_count": len(cuts) - 2,
        "coverage_complete": not high_latitude,
        "facts": facts,
        "limitations": [
            "Duration fractions assume a uniform time window; they are not calibrated probabilities.",
            "Stable requires unanimity, a stricter rule than the spec's 95% threshold.",
            "Planetary speed-zero events are included; dasha dates and strength thresholds are not certified by this geometric test.",
        ]
        + (
            ["Ascendant and house stability is not certified above 65 degrees latitude."]
            if high_latitude
            else []
        ),
    }
