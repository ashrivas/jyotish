"""Hosted boundaries: no ephemeral jobs, no stale test evidence, same numerical core."""

import copy
import json
from fastapi.testclient import TestClient
import pytest
from app.main import app
from app import evaluation
from tools.build_hosted import validate_report

client = TestClient(app)


def test_hosted_does_not_launch_background_evaluations(monkeypatch):
    import app.main as main

    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setattr(main, "start_eval_job", lambda: pytest.fail("Hosted evaluation job started"))
    assert client.post("/api/evals/run", json={}).status_code == 409
    assert client.get("/api/evals/jobs/unused").status_code == 404
    status = client.get("/api/status").json()
    assert status["mode"] == "private_hosted_research"
    assert status["evaluation_execution"]["can_run_here"] is False
    assert status["release_ready"] is False


def test_https_origin_behind_platform_proxy_is_validated(monkeypatch, request_data):
    monkeypatch.setenv("VERCEL", "1")
    # The internal ASGI request is HTTP; the browser uses HTTPS to the platform.
    body = {**request_data, "include_robustness": False}
    assert client.post("/api/chart", json=body, headers={"origin": "https://testserver"}).status_code == 200
    for origin in ("https://unrelated.example", "http://testserver", "https://testserver.attacker.example"):
        assert client.post("/api/chart", json=body, headers={"origin": origin}).status_code == 403


def test_hosted_reads_only_report_for_its_exact_commit(monkeypatch, tmp_path):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VERCEL_GIT_COMMIT_SHA", "a" * 40)
    monkeypatch.setattr(evaluation, "ROOT", tmp_path)
    monkeypatch.setattr(evaluation, "_LAST_REPORT", {"status": "local_checks_passed"})
    assert evaluation.latest_report()["status"] == "missing_build_report"
    path = tmp_path / "data/hosted/report.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"build": {"commit": "b" * 40}, "status": "local_checks_passed"}))
    assert evaluation.latest_report()["status"] == "build_report_commit_mismatch"
    path.write_text(json.dumps({"build": {"commit": "a" * 40}, "status": "test-evidence"}))
    assert evaluation.latest_report()["status"] == "test-evidence"
    monkeypatch.delenv("VERCEL_GIT_COMMIT_SHA")
    assert evaluation.latest_report()["status"] == "build_report_commit_mismatch"


def test_platform_mode_does_not_change_calculation_or_hash(monkeypatch, request_data):
    body = {**request_data, "include_robustness": False}
    monkeypatch.delenv("VERCEL", raising=False)
    local = client.post("/api/chart", json=body).json()
    monkeypatch.setenv("VERCEL", "1")
    hosted = client.post("/api/chart", json=body).json()
    del local["runtime_ms"], hosted["runtime_ms"]
    assert hosted == local


def test_build_gate_rejects_failed_or_reduced_evaluations():
    report = {
        "status": "local_checks_passed",
        "release_ready": False,
        "local_checks": {"exit_code": 0, "passed": 133},
        "dual_engine": {
            "status": "passed",
            "epochs": 1000,
            "comparisons": 7000,
            "failure_count": 0,
            "tolerance_arcseconds": 1.0,
        },
    }
    validate_report(report)
    for path, value in (
        (("local_checks", "exit_code"), 1),
        (("local_checks", "passed"), 0),
        (("dual_engine", "comparisons"), 7),
        (("dual_engine", "failure_count"), 1),
        (("dual_engine", "tolerance_arcseconds"), 60.0),
        (("dual_engine", "status"), "blocked"),
        (("release_ready",), True),
    ):
        bad = copy.deepcopy(report)
        target = bad
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        with pytest.raises(ValueError, match="full passing"):
            validate_report(bad)
