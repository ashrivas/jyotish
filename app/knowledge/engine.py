from pathlib import Path
from typing import Literal
import yaml
from pydantic import Field, model_validator
from app.models import StrictModel

DIRECTORY = Path(__file__).parent


class Condition(StrictModel):
    op: Literal["eq", "sign_distance_in"]
    left: str
    right: str
    values: list[int] = Field(default_factory=list)


class Rule(StrictModel):
    id: str
    source_id: str
    locator: str
    review_status: Literal["draft", "approved"]
    category: Literal["technical_configuration"]
    name: str
    when: Condition
    requires: list[str]
    caveat: str
    approvals: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_review(self):
        if self.review_status == "approved" and len(set(self.approvals)) < 2:
            raise ValueError("Approved rules need two distinct reviewer attestations.")
        if set(self.requires) != {self.when.left, self.when.right}:
            raise ValueError("Rule dependency declaration does not match its operands.")
        if any(not 0 <= x <= 11 for x in self.when.values):
            raise ValueError("Invalid sign distance.")
        return self


def catalog() -> dict:
    return yaml.safe_load((DIRECTORY / "sources.yaml").read_text())


def rules() -> tuple[str, list[Rule]]:
    data = yaml.safe_load((DIRECTORY / "rules.yaml").read_text())
    items = [Rule.model_validate(r) for r in data["rules"]]
    sources = {s["id"] for s in catalog()["sources"]}
    if len({r.id for r in items}) != len(items) or any(r.source_id not in sources for r in items):
        raise ValueError("Duplicate rule ID or missing source.")
    return data["version"], items


def evaluate(facts: dict, stability: dict) -> dict:
    version, items = rules()
    rows = []
    for rule in items:
        missing = [k for k in rule.requires if k not in facts]
        if missing:
            state = "blocked_missing_fact"
        else:
            a, b = facts[rule.when.left], facts[rule.when.right]
            fires = a == b if rule.when.op == "eq" else (b - a) % 12 in rule.when.values
            state = "fires" if fires else "silent"
        stable = all(stability.get(k, {}).get("stability") == "stable" for k in rule.requires)
        rows.append(
            {
                **rule.model_dump(),
                "state": state,
                "stable": stable,
                "eligible_for_prediction": False,
                "evidence": [
                    {
                        "fact_id": k,
                        "value": facts.get(k),
                        "stability": stability.get(k, {}).get("stability", "not_checked"),
                    }
                    for k in rule.requires
                ],
            }
        )
    return {
        "version": version,
        "rules": rows,
        "approved_predictive_rules": 0,
        "interpretation_status": "blocked_pending_reviewed_classical_rules",
        "message": "The lab exposes calculations and source-linked technical drafts. It does not fabricate a classical reading from an empty approved rule base.",
    }
