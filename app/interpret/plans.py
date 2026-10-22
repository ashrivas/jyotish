"""A small closed renderer: plans cannot introduce free-text astrological claims.

This is technical chart explanation, not the future expert-approved dossier renderer.
"""

from typing import Literal
from pydantic import Field
from app.models import StrictModel
from app.astro.constants import SIGNS, NAKSHATRAS, PLANETS


class TechnicalClaim(StrictModel):
    template: Literal["placement", "nakshatra"]
    planet: Literal["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]
    fact_ids: list[str] = Field(min_length=1, max_length=3)


def render_claim(claim: TechnicalClaim, output: dict) -> dict:
    required = (
        [f"{claim.planet}.sign_index", f"{claim.planet}.house"]
        if claim.template == "placement"
        else [f"{claim.planet}.nakshatra_index", f"{claim.planet}.pada"]
    )
    if sorted(claim.fact_ids) != sorted(required):
        raise ValueError("Claim cites the wrong or incomplete fact set.")
    planet = output["chart"]["planets"][claim.planet]
    facts = output["robustness"]["facts"]
    if any(key not in facts for key in required):
        raise ValueError("Uncertainty must be calculated before a claim is rendered.")
    stable = all(facts[key]["stability"] == "stable" for key in required)
    prefix = "Across the supplied time window" if stable else "At the nominal time only"
    if claim.template == "placement":
        text = f"{prefix}, {claim.planet.title()} is in {SIGNS[planet['sign_index']]}, house {planet['house']} counted from the {output['chart']['house_basis']}."
    else:
        text = f"{prefix}, {claim.planet.title()} is in {NAKSHATRAS[planet['nakshatra_index']]}, pada {planet['pada']}."
    return {
        "text": text,
        "fact_ids": required,
        "stability": "stable" if stable else "time_sensitive",
        "kind": "computed_fact_only",
    }


def technical_summary(output: dict) -> list[dict]:
    if not output["robustness"]["facts"]:
        return []
    return [
        render_claim(TechnicalClaim(template=t, planet="moon", fact_ids=ids), output)
        for t, ids in [
            ("placement", ["moon.sign_index", "moon.house"]),
            ("nakshatra", ["moon.nakshatra_index", "moon.pada"]),
        ]
    ]
