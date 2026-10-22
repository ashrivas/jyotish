"""Full nine-lord cycle with three levels; adjacent periods use shared endpoints."""

from datetime import datetime, timedelta
from app.astro.constants import DASHA_LORDS, DASHA_YEARS
from app.astro.angles import units, NAKSHATRA


def children(start: datetime, end: datetime, lord_index: int, depth: int) -> list[dict]:
    result = []
    cursor = start
    total_seconds = (end - start).total_seconds()
    for n in range(9):
        i = (lord_index + n) % 9
        stop = end if n == 8 else cursor + timedelta(seconds=total_seconds * DASHA_YEARS[i] / 120)
        row = {"lord": DASHA_LORDS[i], "start": cursor.isoformat(), "end": stop.isoformat()}
        if depth > 1:
            row["children"] = children(cursor, stop, i, depth - 1)
        result.append(row)
        cursor = stop
    return result


def vimshottari(birth: datetime, moon: float, as_of: datetime, year_days: float) -> dict:
    u = units(moon)
    first = (u // NAKSHATRA) % 9
    elapsed = (u % NAKSHATRA) / NAKSHATRA
    start = birth - timedelta(days=elapsed * DASHA_YEARS[first] * year_days)
    anchor = start
    result = []
    # Cover the birth and the requested epoch even when they fall in different 120-year cycles.
    while as_of < start:
        start -= timedelta(days=120 * year_days)
    while as_of >= start + timedelta(days=120 * year_days):
        start += timedelta(days=120 * year_days)
    cycle_starts = []
    cycle = min(anchor, start)
    while cycle <= max(anchor, start):
        cycle_starts.append(cycle)
        cycle += timedelta(days=120 * year_days)
    for cycle_start in cycle_starts:
        cursor = cycle_start
        for n in range(9):
            i = (first + n) % 9
            end = cursor + timedelta(days=DASHA_YEARS[i] * year_days)
            result.append(
                {
                    "lord": DASHA_LORDS[i],
                    "start": cursor.isoformat(),
                    "end": end.isoformat(),
                    "children": children(cursor, end, i, 2),
                }
            )
            cursor = end
    active = []
    rows = result
    for _ in range(3):
        row = next(
            (
                r
                for r in rows
                if datetime.fromisoformat(r["start"]) <= as_of < datetime.fromisoformat(r["end"])
            ),
            None,
        )
        if row is None:
            raise ValueError("No active dasha for requested epoch")
        active.append({k: row[k] for k in ("lord", "start", "end")})
        rows = row.get("children", [])
    return {
        "year_days": year_days,
        "birth_balance_years": (1 - elapsed) * DASHA_YEARS[first],
        "current": active,
        "periods": result,
        "interval_convention": "start inclusive, end exclusive",
    }
