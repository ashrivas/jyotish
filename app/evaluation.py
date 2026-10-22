from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Literal, Any
import json
import subprocess
import os
import sys
import re
import tempfile
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from pydantic import Field, model_validator
from app.models import StrictModel, ChartRequest, Conventions
from app.astro.engine import compute
from app.astro.angles import separation
from app.astro.ephemeris import ROOT

EVAL_LOCK = Lock()
RESULTS = Path(os.environ.get("JYOTI_EVAL_DIR", str(ROOT / "var/evals")))
_LAST_REPORT = None
JOB_LOCK = Lock()
JOBS = {}
EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="jyoti-eval")


class ExpectedMetric(StrictModel):
    path: str = Field(min_length=3, max_length=120)
    kind: Literal["angle_degrees", "exact", "datetime"]
    value: str | int | float | bool


class ReferenceCase(StrictModel):
    fixture_id: str = Field(min_length=1, max_length=100)
    program: Literal["Jagannatha Hora", "AstroSage", "PAC", "published_worked_example"]
    program_version: str = Field(min_length=1, max_length=100)
    source_locator: str = Field(min_length=3, max_length=500)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    conventions: Conventions
    input: ChartRequest
    expected: list[ExpectedMetric] = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def validate_conventions(self):
        if self.conventions != self.input.conventions:
            raise ValueError(
                "Reference settings differ from the requested conventions. Triage the disagreement before comparison."
            )
        if "as_of" not in self.input.model_fields_set:
            raise ValueError("Reference cases must freeze the as_of epoch.")
        if len({m.path for m in self.expected}) != len(self.expected):
            raise ValueError("Duplicate expected metric paths.")
        return self


def read_path(output: dict, path: str):
    value = output
    for component in path.split("."):
        value = value[int(component)] if isinstance(value, list) else value[component]
    return value


def compare_reference(case: ReferenceCase) -> dict:
    output = compute(case.input)
    rows = []
    for metric in case.expected:
        try:
            actual = read_path(output, metric.path)
        except (KeyError, ValueError, IndexError, TypeError):
            rows.append({"path": metric.path, "status": "unavailable", "expected": metric.value})
            continue
        if metric.kind == "angle_degrees":
            if (
                not metric.path.endswith(".longitude")
                or not isinstance(metric.value, (int, float))
                or isinstance(metric.value, bool)
            ):
                raise ValueError("Angular metrics must target a longitude and provide numeric degrees.")
            tolerance = 1 / 60  # Spec's reference-program tolerance; callers cannot relax it.
            delta = separation(float(actual), float(metric.value))
            unit = "degrees"
            passed = delta <= tolerance
        elif metric.kind == "datetime":
            a, b = datetime.fromisoformat(str(actual)), datetime.fromisoformat(str(metric.value))
            if a.tzinfo is None or b.tzinfo is None:
                raise ValueError("Reference datetimes require explicit UTC offsets.")
            tolerance, unit = (60, "seconds") if metric.path.startswith("panchang.") else (86400, "seconds")
            delta = abs((a - b).total_seconds())
            passed = delta <= tolerance
        else:
            tolerance, unit, delta = 0, "exact", None
            passed = type(actual) is type(metric.value) and actual == metric.value
        rows.append(
            {
                "path": metric.path,
                "status": "matched" if passed else "mismatch",
                "expected": metric.value,
                "actual": actual,
                "difference": delta,
                "tolerance": tolerance,
                "unit": unit,
            }
        )
    return {
        "fixture_id": case.fixture_id,
        "program": case.program,
        "source_locator": case.source_locator,
        "source_sha256": case.source_sha256,
        "chart_hash": output["chart_hash"],
        "status": "matched" if all(r["status"] == "matched" for r in rows) else "mismatch_or_unavailable",
        "metrics": rows,
        "note": "This compares only the supplied fields from one user-provided reference. It does not certify an entire chart or satisfy the two-program release gate.",
    }


def latest_report() -> dict:
    path = RESULTS / "latest.json"
    return _LAST_REPORT or (
        json.loads(path.read_text()) if path.exists() else {"status": "not_run", "release_ready": False}
    )


def suite_status(dual: dict | None = None) -> list[dict]:
    definitions = [
        (
            1,
            "30 golden charts against two reference programs",
            "blocked",
            "External JHora and AstroSage exports are not supplied; zero approved golden charts.",
        ),
        (
            2,
            "Independent astronomy on 1,000 epochs",
            (dual or {}).get("status", "not_run"),
            "Skyfield/DE440s compares seven physical grahas in the apparent tropical frame; scope is explicitly limited.",
        ),
        (
            3,
            "Birth-time robustness",
            "partial",
            "Angular transitions, planetary stations, DST cases and unknown time tested; dasha/strength certification remains incomplete.",
        ),
        (
            4,
            "Fact firewall mutations",
            "partial",
            "Closed technical templates reject injected facts and prose; the full dossier firewall is pending.",
        ),
        (
            5,
            "Safety covenant",
            "not_implemented",
            "No conversational model path is enabled in this milestone.",
        ),
        (
            6,
            "Knowledge lint and approvals",
            "blocked",
            "Source registry and draft rules exist; no approved predictive corpus.",
        ),
        (
            7,
            "Dossier validity",
            "blocked",
            "Requires approved corpus and completed computation dependencies.",
        ),
        (
            8,
            "Interpretive faithfulness",
            "blocked",
            "Requires reviewed entries, live verifier and expert checks.",
        ),
        (
            9,
            "Cross-language consistency",
            "blocked",
            "Technical facts are deterministic; interpretation-language suite not implemented.",
        ),
        (10, "Covenant red team", "blocked", "No conversational model path is enabled."),
        (
            11,
            "Specificity",
            "not_run",
            "Rarity of a chart fact alone does not establish that an interpretation is specific or valid.",
        ),
        (12, "User jury", "requires_people", "User study has not run."),
        (
            13,
            "Latency and cost",
            "partial",
            "Local numerical latency is measurable; model latency/cost not measured.",
        ),
        (
            14,
            "Blind expert concordance",
            "requires_people",
            "No expert panel or consented real-chart set yet.",
        ),
        (
            15,
            "Independent rule extraction agreement",
            "requires_people",
            "No independent scholar encodings or kappa estimates yet.",
        ),
        (16, "Verifier seeded errors", "blocked", "No live model verifier is enabled."),
        (
            17,
            "Blind birth-time rectification",
            "not_implemented",
            "Feature stays unavailable until its controlled evaluation passes.",
        ),
        (
            18,
            "Optional-input incremental value",
            "not_implemented",
            "No claim that additional inputs improve predictions.",
        ),
        (
            19,
            "Prospective outcome calibration",
            "not_started",
            "Requires consent, preregistration and held-out/shuffled controls; not a release gate.",
        ),
    ]
    return [
        {"id": n, "name": name, "status": state, "detail": detail} for n, name, state, detail in definitions
    ]


def run_local_evals(include_dual=True) -> dict:
    global _LAST_REPORT
    if not EVAL_LOCK.acquire(blocking=False):
        raise RuntimeError("An evaluation is already running.")
    try:
        # A fixed command only; no user input is interpolated into commands or test selection.
        with tempfile.TemporaryDirectory(prefix="jyoti-test-cache-") as cache:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "-o", f"cache_dir={cache}/pytest"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=180,
                env={
                    **os.environ,
                    "PYTHONHASHSEED": "0",
                    "HYPOTHESIS_STORAGE_DIRECTORY": f"{cache}/hypothesis",
                },
            )
        dual = None
        if include_dual:
            try:
                from tools.dual_engine import run

                dual = run(1000)
            except (FileNotFoundError, ImportError) as exc:
                dual = {"status": "blocked", "reason": str(exc)}
        count = re.search(r"(\d+) passed", result.stdout)
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "release_ready": False,
            "status": "local_checks_passed"
            if result.returncode == 0 and (not dual or dual["status"] == "passed")
            else "checks_failed_or_blocked",
            "local_checks": {
                "exit_code": result.returncode,
                "passed": int(count.group(1)) if count else 0,
                "output": (result.stdout + result.stderr)[-16000:],
            },
            "dual_engine": dual,
            "spec_suites": suite_status(dual),
            "source_triage": json.loads((ROOT / "refdata/TRIAGE.json").read_text()),
        }
        try:
            RESULTS.mkdir(parents=True, exist_ok=True)
            temporary = RESULTS / "latest.partial.json"
            temporary.write_text(json.dumps(report, indent=2) + "\n")
            temporary.replace(RESULTS / "latest.json")
            report["persistence"] = "saved"
        except OSError:
            report["persistence"] = "memory_only; the report directory is not writable"
        _LAST_REPORT = report
        return report
    finally:
        EVAL_LOCK.release()


def start_eval_job() -> dict:
    """Local in-process jobs avoid tying a potentially long eval to a proxy request timeout."""
    with JOB_LOCK:
        if any(j["state"] in ("queued", "running") for j in JOBS.values()):
            raise RuntimeError("An evaluation is already running.")
        job_id = uuid4().hex
        JOBS[job_id] = {"job_id": job_id, "state": "queued"}
        if len(JOBS) > 5:
            del JOBS[next(iter(JOBS))]
    EXECUTOR.submit(_execute_job, job_id)
    return {"job_id": job_id, "state": "queued"}


def _execute_job(job_id: str):
    with JOB_LOCK:
        JOBS[job_id] = {"job_id": job_id, "state": "running"}
    try:
        report = run_local_evals()
        result = {"job_id": job_id, "state": "completed", "report": report}
    except Exception as exc:
        # This is the top-level job boundary, not a suppression of numerical failures.
        # Errors are visible and cannot turn into a passing report.
        result = {"job_id": job_id, "state": "failed", "error": f"{type(exc).__name__}: {exc}"}
    with JOB_LOCK:
        JOBS[job_id] = result


def eval_job(job_id: str) -> dict | None:
    with JOB_LOCK:
        return JOBS.get(job_id)
