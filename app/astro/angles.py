"""Half-open angular bins; never round a longitude before classifying it."""

from decimal import Decimal, ROUND_FLOOR
import math

UNITS_PER_DEGREE = 3_600_000_000  # microarcseconds
CIRCLE = 360 * UNITS_PER_DEGREE
SIGN = 30 * UNITS_PER_DEGREE
NAKSHATRA = CIRCLE // 27
PADA = CIRCLE // 108


def units(longitude: float) -> int:
    if not math.isfinite(longitude):
        raise ValueError("Longitude must be finite.")
    return (
        int((Decimal(str(longitude % 360)) * UNITS_PER_DEGREE).to_integral_value(rounding=ROUND_FLOOR))
        % CIRCLE
    )


def classify(longitude: float) -> dict:
    u = units(longitude)
    return {
        "sign_index": u // SIGN,
        "degree_in_sign": (u % SIGN) / UNITS_PER_DEGREE,
        "nakshatra_index": u // NAKSHATRA,
        "pada": (u % NAKSHATRA) // PADA + 1,
    }


def separation(a: float, b: float) -> float:
    return abs((a - b + 180) % 360 - 180)
