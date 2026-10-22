"""Serialized Swiss Ephemeris access with fail-closed kernel verification."""

from contextlib import contextmanager
from datetime import datetime, timezone
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from threading import RLock
import swisseph as swe
from app.models import Conventions
from app.astro.angles import classify
from app.astro.constants import SIGNS, NAKSHATRAS

ROOT = Path(__file__).resolve().parents[2]
EPHE_PATH = ROOT / "data" / "ephe"
KERNELS = {
    "sepl_18.se1": "ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66",
    "semo_18.se1": "1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7",
}
LOCK = RLock()
BODIES = {
    "sun": swe.SUN,
    "moon": swe.MOON,
    "mars": swe.MARS,
    "mercury": swe.MERCURY,
    "jupiter": swe.JUPITER,
    "venus": swe.VENUS,
    "saturn": swe.SATURN,
}


class EphemerisError(ValueError):
    pass


@lru_cache(maxsize=8)
def _checked_digest(path: str, size: int, mtime_ns: int) -> str:
    return sha256(Path(path).read_bytes()).hexdigest()


def kernel_manifest() -> dict:
    result = {}
    for name, expected in KERNELS.items():
        path = EPHE_PATH / name
        if not path.is_file():
            raise EphemerisError(f"Missing {name}. Run: uv run python tools/fetch_data.py")
        stat = path.stat()
        digest = _checked_digest(str(path), stat.st_size, stat.st_mtime_ns)
        if digest != expected:
            raise EphemerisError(f"Checksum mismatch for {name}; refusing to compute.")
        result[name] = digest
    return result


@contextmanager
def context(conventions: Conventions):
    kernel_manifest()
    # Swiss settings are mutable process/thread state. Keep every API call inside this lock.
    with LOCK:
        swe.set_ephe_path(str(EPHE_PATH))
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        yield


def julian(instant: datetime) -> tuple[float, float]:
    t = instant.astimezone(timezone.utc)
    return swe.utc_to_jd(t.year, t.month, t.day, t.hour, t.minute, t.second + t.microsecond / 1e6)


def body_position(tt: float, body: int, sidereal: bool = True) -> tuple:
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED | (swe.FLG_SIDEREAL if sidereal else 0)
    values, actual = swe.calc(tt, body, flags)
    if (actual & (swe.FLG_JPLEPH | swe.FLG_SWIEPH | swe.FLG_MOSEPH)) != swe.FLG_SWIEPH:
        raise EphemerisError("Swiss Ephemeris substituted another engine; refusing silent fallback.")
    return values, actual


def named_position(longitude: float) -> dict:
    c = classify(longitude)
    return {
        "longitude": longitude % 360,
        **c,
        "sign": SIGNS[c["sign_index"]],
        "nakshatra": NAKSHATRAS[c["nakshatra_index"]],
    }


def longitude_at(instant: datetime, body: str, lat: float, lon: float, conventions: Conventions) -> float:
    with context(conventions):
        tt, ut = julian(instant)
        if body == "lagna":
            return swe.houses_ex(ut, lat, lon, b"W", swe.FLG_SIDEREAL)[1][0]
        code = (
            (swe.MEAN_NODE if conventions.nodes == "mean" else swe.TRUE_NODE)
            if body in ("rahu", "ketu")
            else BODIES[body]
        )
        angle = body_position(tt, code)[0][0]
        return (angle + (180 if body == "ketu" else 0)) % 360


def speed_at(instant: datetime, body: str, conventions: Conventions) -> float:
    with context(conventions):
        tt, _ = julian(instant)
        code = (
            (swe.MEAN_NODE if conventions.nodes == "mean" else swe.TRUE_NODE)
            if body in ("rahu", "ketu")
            else BODIES[body]
        )
        return body_position(tt, code)[0][3]


def snapshot(
    instant: datetime, lat: float, lon: float, conventions: Conventions, include_lagna: bool = True
) -> dict:
    with context(conventions):
        tt, ut = julian(instant)
        codes = {**BODIES, "rahu": swe.MEAN_NODE if conventions.nodes == "mean" else swe.TRUE_NODE}
        planets = {}
        for name, code in codes.items():
            p, actual = body_position(tt, code)
            planets[name] = {
                **named_position(p[0]),
                "latitude": p[1],
                "distance_au": p[2],
                "speed_deg_day": p[3],
                "retrograde": p[3] < 0,
                "actual_flags": actual,
            }
        r = planets["rahu"]
        planets["ketu"] = {**r, **named_position(r["longitude"] + 180), "latitude": -r["latitude"]}
        lagna = (
            named_position(swe.houses_ex(ut, lat, lon, b"W", swe.FLG_SIDEREAL)[1][0])
            if include_lagna
            else None
        )
        origin = lagna["sign_index"] if lagna else planets["moon"]["sign_index"]
        for p in planets.values():
            p["house"] = (p["sign_index"] - origin) % 12 + 1
            p["house_basis"] = "lagna" if lagna else "moon"
        return {
            "jd_tt": tt,
            "jd_ut1": ut,
            "ayanamsa_degrees": swe.get_ayanamsa_ex(tt, swe.FLG_SWIEPH)[1],
            "planets": planets,
            "lagna": lagna,
            "house_basis": "lagna" if lagna else "moon",
        }
