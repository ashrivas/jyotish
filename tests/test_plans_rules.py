import pytest
from pydantic import ValidationError
from app.interpret.plans import TechnicalClaim, render_claim
from app.astro.engine import compute
from app.knowledge.engine import evaluate, Rule


@pytest.mark.parametrize(
    "extra", [{"text": "Jupiter brings guaranteed wealth"}, {"date": "2027-01-01"}, {"sign": "Aries"}]
)
def test_plan_mutations_cannot_inject_prose_dates_or_facts(extra):
    with pytest.raises(ValidationError):
        TechnicalClaim.model_validate(
            {
                "template": "placement",
                "planet": "moon",
                "fact_ids": ["moon.sign_index", "moon.house"],
                **extra,
            }
        )


def test_claim_cannot_cite_the_wrong_planet(chart_request):
    claim = TechnicalClaim(template="placement", planet="moon", fact_ids=["sun.sign_index", "moon.house"])
    with pytest.raises(ValueError, match="wrong"):
        render_claim(claim, compute(chart_request))


@pytest.mark.parametrize("a,b,fires", [(0, 0, True), (0, 1, False), (11, 11, True), (3, 9, False)])
def test_budha_aditya_draft_fires_and_silent_cases(a, b, fires):
    facts = {"sun.sign_index": a, "mercury.sign_index": b}
    row = evaluate(facts, {})["rules"][0]
    assert (row["state"] == "fires") is fires
    assert row["eligible_for_prediction"] is False


def test_missing_facts_block_instead_of_counting_as_a_negative():
    assert evaluate({}, {})["rules"][0]["state"] == "blocked_missing_fact"


def test_unsupported_operator_and_forged_approval_rejected():
    from app.knowledge.engine import rules

    data = rules()[1][0].model_dump()
    data["when"]["op"] = "eval_python"
    with pytest.raises(ValueError):
        Rule.model_validate(data)
    data = rules()[1][0].model_dump()
    data["review_status"] = "approved"
    with pytest.raises(ValueError, match="two distinct"):
        Rule.model_validate(data)
