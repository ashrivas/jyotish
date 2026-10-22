"""The 16 Parashari sign mappings, explicitly pinned to PVR 2000, chapter 6.

Only sign placements are emitted: fractional 'varga degrees' are not silently invented.
In particular D30 is nonuniform and D60 follows this edition's sign-relative convention.
"""

from app.astro.angles import units, SIGN, UNITS_PER_DEGREE
from app.astro.constants import VARGAS


def varga_sign(longitude: float, division: int) -> int:
    if division not in VARGAS:
        raise ValueError("Unsupported varga")
    u = units(longitude)
    s, remainder = divmod(u, SIGN)
    odd = s % 2 == 0  # Aries is sign 1.
    part = remainder * division // SIGN
    match division:
        case 1:
            result = s
        case 2:
            result = 4 if (odd and part == 0) or (not odd and part == 1) else 3
        case 3:
            result = s + 4 * part
        case 4:
            result = s + 3 * part
        case 7:
            result = s + (0 if odd else 6) + part
        case 9:
            result = (0, 9, 6, 3)[s % 4] + part
        case 10:
            result = s + (0 if odd else 8) + part
        case 12 | 60:
            result = s + part
        case 16 | 45:
            result = (0, 4, 8)[s % 3] + part
        case 20:
            result = (0, 8, 4)[s % 3] + part
        case 24:
            result = (4 if odd else 3) + part
        case 27:
            result = (0, 3, 6, 9)[s % 4] + part
        case 30:
            degrees = remainder / UNITS_PER_DEGREE
            ranges = (
                ((5, 0), (10, 10), (18, 8), (25, 2), (30, 6))
                if odd
                else ((5, 1), (12, 5), (20, 11), (25, 9), (30, 7))
            )
            result = next(sign for upper, sign in ranges if degrees < upper)
        case 40:
            result = (0 if odd else 6) + part
    return result % 12


def all_vargas(longitude: float) -> dict[str, int]:
    return {f"D{d}": varga_sign(longitude, d) for d in VARGAS}
