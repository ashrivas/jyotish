"""Independent astronomy check: Skyfield/JPL DE440s vs Swiss apparent tropical longitudes.

Coordinates, epoch and light-time/aberration conventions must match before comparing.
This does NOT independently validate sidereal conventions, nodes, houses, or predictions.
"""

from datetime import datetime, timedelta, timezone
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import random
import swisseph as swe
from app.astro.ephemeris import context, body_position, julian, ROOT, BODIES
from app.astro.angles import separation
from app.models import Conventions

KERNEL_SHA = "c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2"


@lru_cache(maxsize=1)
def oracle():
    from skyfield.api import load, load_file

    path = ROOT / "refdata/kernels/de440s.bsp"
    if not path.exists():
        raise FileNotFoundError("Run uv run python tools/fetch_data.py --oracle")
    if sha256(path.read_bytes()).hexdigest() != KERNEL_SHA:
        raise ValueError("JPL kernel checksum mismatch")
    return load.timescale(builtin=True), load_file(str(path))


def compare(instant: datetime) -> dict:
    from skyfield.framelib import ecliptic_frame

    ts, eph = oracle()
    # TT is the shared physical epoch; UT1/UTC conversion is checked separately.
    tt, _ = julian(instant)
    t = ts.tt_jd(tt)
    earth = eph["earth"].at(t)
    names = {
        "sun": "sun",
        "moon": "moon",
        "mercury": "mercury barycenter",
        "venus": "venus barycenter",
        "mars": "mars barycenter",
        "jupiter": "jupiter barycenter",
        "saturn": "saturn barycenter",
    }
    differences = {}
    with context(Conventions()):
        for name, target in names.items():
            _, lon, _ = earth.observe(eph[target]).apparent().frame_latlon(ecliptic_frame)
            swiss, _ = body_position(tt, BODIES[name], sidereal=False)
            differences[name] = separation(lon.degrees, swiss[0]) * 3600
    return differences


def run(count=1000, seed=20261022) -> dict:
    rng = random.Random(seed)
    start = datetime(1900, 1, 1, tzinfo=timezone.utc)
    span = (datetime(2100, 1, 1, tzinfo=timezone.utc) - start).total_seconds()
    worst = {name: {"arcseconds": 0, "utc": None} for name in BODIES}
    failures = []
    for _ in range(count):
        instant = start + timedelta(seconds=rng.uniform(0, span))
        for name, delta in compare(instant).items():
            if delta > worst[name]["arcseconds"]:
                worst[name] = {"arcseconds": delta, "utc": instant.isoformat()}
            if delta > 1:
                failures.append({"planet": name, "arcseconds": delta, "utc": instant.isoformat()})
    return {
        "status": "passed" if not failures else "failed",
        "epochs": count,
        "comparisons": count * 7,
        "seed": seed,
        "tolerance_arcseconds": 1.0,
        "worst_by_planet": worst,
        "failures": failures[:20],
        "failure_count": len(failures),
        "kernel_sha256": KERNEL_SHA,
        "scope": "Seven physical grahas, apparent geocentric tropical longitudes only; nodes, lagna, dashas and interpretation excluded.",
    }
