"""Deployment metadata, separate from numerical calculation conventions."""

import os

SOURCE_URL = "https://github.com/ashrivas/jyotish"
CHECKS_URL = SOURCE_URL + "/actions/workflows/accuracy.yml"


def is_hosted() -> bool:
    return os.environ.get("VERCEL") == "1"


def evaluation_execution() -> dict:
    return {
        "mode": "build_report" if is_hosted() else "local_jobs",
        "can_run_here": not is_hosted(),
        "checks_url": CHECKS_URL,
        "commit": os.environ.get("VERCEL_GIT_COMMIT_SHA"),
        "note": (
            "These checks ran while building this deployment. Refresh reloads the bundled report; "
            "it does not launch a new evaluation. New checks run in GitHub Actions and on the next build."
            if is_hosted()
            else "Evaluations run on this computer; jobs do not survive a server restart."
        ),
    }
