"""Build the private workbench with fresh numerical checks bound to its Git commit.

No personal inputs or book corpus enter the deployment. Runtime uses an immutable
report; it never depends on an in-process background job or a writable filesystem.
"""

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.fetch_data import fetch, ASSETS, ORACLE
from app.astro.ephemeris import kernel_manifest


def validate_report(report: dict) -> None:
    checks, dual = report.get("local_checks", {}), report.get("dual_engine", {})
    if (
        report.get("status") != "local_checks_passed"
        or report.get("release_ready") is not False
        or checks.get("exit_code") != 0
        or checks.get("passed", 0) < 133
        or dual.get("status") != "passed"
        or dual.get("epochs") != 1000
        or dual.get("comparisons") != 7000
        or dual.get("failure_count") != 0
        or dual.get("tolerance_arcseconds") != 1.0
    ):
        raise ValueError("Hosted build requires the full passing code and independent astronomy suites.")


def main() -> None:
    commit = os.environ.get("VERCEL_GIT_COMMIT_SHA", "")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise SystemExit("A full VERCEL_GIT_COMMIT_SHA is required to bind checks to this deployment.")
    output = ROOT / "data/hosted"
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").unlink(missing_ok=True)
    for asset in [*ASSETS, ORACLE]:
        fetch(*asset)
    # The runner is a build process, not the hosted API. Exercise both local
    # and hosted behavior in the suite without inheriting the platform mode.
    subprocess.run(
        [sys.executable, "tools/run_evals.py"],
        cwd=ROOT,
        env={**os.environ, "VERCEL": "0", "JYOTI_EVAL_DIR": str(output / "checks")},
        check=True,
        timeout=240,
    )
    raw = (output / "checks/latest.json").read_bytes()
    report = json.loads(raw)
    validate_report(report)
    report["build"] = {
        "commit": commit,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "execution": "vercel_build",
        "report_sha256": sha256(raw).hexdigest(),
        "ephemeris": kernel_manifest(),
        "source_url": f"https://github.com/ashrivas/jyotish/tree/{commit}",
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Hosted numerical checks passed for {commit}; release readiness remains blocked.")


if __name__ == "__main__":
    main()
