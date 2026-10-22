from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.evaluation import run_local_evals

if __name__ == "__main__":
    result = run_local_evals()
    print(
        json.dumps(
            {
                "status": result["status"],
                "code_tests_passed": result["local_checks"]["passed"],
                "dual_engine": result["dual_engine"],
                "release_ready": result["release_ready"],
            },
            indent=2,
        )
    )
    raise SystemExit(0 if result["status"] == "local_checks_passed" else 1)
