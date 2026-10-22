from datetime import datetime, time, timedelta, timezone
import swisseph as swe
from app.models import BirthInput, Conventions
from app.astro.ephemeris import context, julian, body_position
from app.astro.angles import classify
from app.astro.constants import NAKSHATRAS
from app.astro.time import resolve, zone


def panchang(birth: BirthInput, conventions: Conventions) -> dict:
    civil_zone = (
        timezone(timedelta(seconds=birth.civil_offset_seconds))
        if birth.civil_offset_seconds is not None
        else zone(birth.timezone)
    )
    midnight = datetime.combine(birth.date, time.min, civil_zone).astimezone(timezone.utc)
    with context(conventions):
        _, jd = julian(midnight)
        res, events = swe.rise_trans(
            jd, swe.SUN, swe.CALC_RISE, (birth.longitude, birth.latitude, 0), 1013.25, 15.0, swe.FLG_SWIEPH
        )
        if res == -2:
            return {
                "status": "no_sunrise",
                "reason": "No sunrise at this location on the local date; no arbitrary fallback.",
                "local_date": str(birth.date),
            }
        ut = events[0]
        # Convert UT1 to UTC with the library's Delta-T/leap-second model, not JD arithmetic.
        y, m, d, h, minute, sec = swe.jdut1_to_utc(ut)
        sunrise = datetime(y, m, d, h, minute, tzinfo=midnight.tzinfo) + timedelta(seconds=sec)
        local = sunrise.astimezone(civil_zone)
        if local.date() != birth.date:
            return {
                "status": "no_sunrise",
                "local_date": str(birth.date),
                "reason": "Next sunrise is on a different local date.",
            }
        tt, _ = julian(sunrise)
        sun, _ = body_position(tt, swe.SUN)
        moon, _ = body_position(tt, swe.MOON)
        elongation = (moon[0] - sun[0]) % 360
        tithi = int(elongation // 12) + 1
        nak = classify(moon[0])["nakshatra_index"]
        yoga = int(((sun[0] + moon[0]) % 360) / (360 / 27)) + 1
        return {
            "status": "computed",
            "local_date": str(birth.date),
            "sunrise_utc": sunrise.isoformat(),
            "sunrise_local": local.isoformat(),
            "tithi": tithi,
            "paksha": "shukla" if tithi <= 15 else "krishna",
            "nakshatra": NAKSHATRAS[nak],
            "nakshatra_index": nak,
            "vara": ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")[
                local.weekday()
            ],
            "nitya_yoga_number": yoga,
            "karana_half_tithi_index": int(elongation // 6),
            "definition": "Sun upper limb, standard refraction, sea level, 1013.25 hPa, 15 C; natal birthplace.",
            "validation": "awaiting PAC reference tables",
        }
