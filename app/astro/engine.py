from datetime import timedelta, timezone
from hashlib import sha256
import json
import tzdata
import swisseph as swe
from app.models import ChartRequest
from app.astro.ephemeris import snapshot, kernel_manifest
from app.astro.time import birth_window, zone
from app.astro.vargas import all_vargas
from app.astro.attributes import attributes
from app.astro.ashtakavarga import ashtakavarga
from app.astro.dasha import vimshottari
from app.astro.panchang import panchang
from app.astro.robustness import robustness, geometric_facts
from app.knowledge.engine import evaluate


def digest(value) -> str:
    return (
        "sha256:"
        + sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
    )


def compute(request: ChartRequest) -> dict:
    birth, conv = request.birth, request.conventions
    center, start, end = birth_window(birth)
    provenance = {
        "engine": "pyswisseph",
        "swiss_ephemeris_version": swe.version,
        "binding_version": "2.10.3.2",
        "tzdata": tzdata.__version__,
        "kernels": kernel_manifest(),
        "coordinate_frame": "apparent geocentric ecliptic of date, sidereal Lahiri",
        "ephemeris": "SWIEPH, no fallback",
    }
    # Place labels cannot affect calculations. UTC, coordinates, conventions and kernel versions can.
    natal_identity = {
        "utc": center.isoformat(),
        "window": [start.isoformat(), end.isoformat()],
        "latitude": birth.latitude,
        "longitude": birth.longitude,
        "timezone": birth.timezone,
        "civil_offset_seconds": birth.civil_offset_seconds,
        "unknown_time": birth.confidence == "unknown",
        "conventions": conv.model_dump(),
        "provenance": provenance,
    }
    chart_hash = digest(natal_identity)
    snap = snapshot(center, birth.latitude, birth.longitude, conv, birth.confidence != "unknown")
    vargas = {n: all_vargas(p["longitude"]) for n, p in snap["planets"].items()}
    if snap["lagna"]:
        vargas["lagna"] = all_vargas(snap["lagna"]["longitude"])
    dasha = vimshottari(center, snap["planets"]["moon"]["longitude"], request.as_of, conv.dasha_year_days)
    robust = (
        robustness(request, start, end, snap)
        if request.include_robustness
        else {
            "method": "disabled",
            "coverage_complete": False,
            "facts": {},
            "limitations": ["Birth-time robustness was not calculated."],
        }
    )
    if start != end:
        # These are explicitly endpoint scenarios, not certified extrema over the birth window.
        scenarios = []
        for instant in (start, end):
            sample = snapshot(instant, birth.latitude, birth.longitude, conv, False)
            scenarios.append(
                {
                    "birth_utc": instant.isoformat(),
                    "current": vimshottari(
                        instant, sample["planets"]["moon"]["longitude"], request.as_of, conv.dasha_year_days
                    )["current"],
                }
            )
        dasha["uncertainty"] = {
            "status": "not_certified",
            "endpoint_scenarios": scenarios,
            "note": "Nominal dates are not exact predictions. Endpoint scenarios are not asserted to be extrema. Continuous dasha-boundary certification remains pending.",
        }
    else:
        dasha["uncertainty"] = {"status": "single_supplied_instant"}
    current = snapshot(request.as_of, birth.latitude, birth.longitude, conv, False)
    moon_sign = snap["planets"]["moon"]["sign_index"]
    transits = {
        n: {**p, "house_from_natal_moon": (p["sign_index"] - moon_sign) % 12 + 1}
        for n, p in current["planets"].items()
    }
    saturn_house = transits["saturn"]["house_from_natal_moon"]
    flags = {
        "manglik_basis": {
            basis: {
                "mars_house": (snap["planets"]["mars"]["sign_index"] - origin) % 12 + 1,
                "in_listed_house": (snap["planets"]["mars"]["sign_index"] - origin) % 12 + 1
                in (1, 2, 4, 7, 8, 12),
            }
            for basis, origin in {
                "moon": moon_sign,
                "venus": snap["planets"]["venus"]["sign_index"],
                **({"lagna": snap["lagna"]["sign_index"]} if snap["lagna"] else {}),
            }.items()
        },
        "sade_sati": {
            "active_at_as_of": saturn_house in (12, 1, 2),
            "saturn_house_from_moon": saturn_house,
            "ingress_dates": "not_implemented",
            "note": "Geometric status only, no severity judgment or forecast.",
        },
        "note": "Cancellation rules and interpretive effects are pending source review.",
    }
    evidence = evaluate(geometric_facts(snap), robust["facts"])
    warnings = [
        "Research build: reference-software golden validation and expert review are incomplete.",
        "A precise calculation is not evidence that an astrological prediction is true.",
        "Dignity, Ashtakavarga and dasha outputs have separate validation states; no combined confidence score is fabricated.",
    ]
    if birth.date.year < 1970:
        warnings.append(
            "Historical timezone records before 1970 can be incomplete; confirm the actual civil-time convention used on the birth record."
        )
    if birth.confidence == "unknown":
        warnings.append(
            "Unknown birth time: the central instant is a computation anchor only. No ascendant is emitted; houses are counted from the Moon and may vary over the day."
        )
    if abs(birth.latitude) > 65:
        warnings.append("High latitude: sunrise may not occur and ascendant robustness is not certified.")
    output = {
        "chart_hash": chart_hash,
        "run_hash": digest(
            {
                "chart": chart_hash,
                "as_of": request.as_of.isoformat(),
                "robustness": request.include_robustness,
            }
        ),
        "input": request.model_dump(mode="json"),
        "resolved_time": {
            "utc": center.isoformat(),
            "local": center.astimezone(
                timezone(timedelta(seconds=birth.civil_offset_seconds))
                if birth.civil_offset_seconds is not None
                else zone(birth.timezone)
            ).isoformat(),
            "civil_time_source": birth.civil_offset_source or ("IANA tzdata " + tzdata.__version__),
            "window_start_utc": start.isoformat(),
            "window_end_utc": end.isoformat(),
        },
        "conventions": conv.model_dump(),
        "provenance": provenance,
        "chart": snap,
        "vargas": vargas,
        "attributes": attributes(snap["planets"], snap["lagna"]),
        "ashtakavarga": ashtakavarga(snap["planets"], snap["lagna"]),
        "dasha": dasha,
        "panchang": panchang(birth, conv),
        "transits": transits,
        "flags": flags,
        "robustness": robust,
        "evidence": evidence,
        "warnings": warnings,
        "not_implemented": [
            "full_shadbala",
            "bhava_bala",
            "vimshopaka_bala",
            "combustion_and_planetary_war",
            "functional_nature_table",
            "guna_milan",
            "sade_sati_ingress_search",
            "vedha",
            "varshaphala",
            "prashna",
            "muhurta",
            "birth_time_rectification",
            "reviewed_predictive_corpus",
            "llm_dossier_and_verification",
        ],
    }
    return output
