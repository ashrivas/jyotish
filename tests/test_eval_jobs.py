from concurrent.futures import Future
import subprocess
from app import evaluation
from app.main import app
from fastapi.testclient import TestClient


def test_eval_endpoint_returns_immediately_with_a_job(monkeypatch):
    import app.main as main

    monkeypatch.setattr(main, "start_eval_job", lambda: {"job_id": "test-job", "state": "queued"})
    response = TestClient(app).post("/api/evals/run", json={})
    assert response.status_code == 202
    assert response.json()["job_id"] == "test-job"


def test_job_failure_is_visible_and_never_a_passing_report(monkeypatch):
    def fail():
        raise OSError("Synthetic read-only environment failure")

    monkeypatch.setattr(evaluation, "run_local_evals", fail)
    evaluation.JOBS["test-failure"] = {"job_id": "test-failure", "state": "queued"}
    evaluation._execute_job("test-failure")
    result = evaluation.eval_job("test-failure")
    assert result["state"] == "failed"
    assert "read-only" in result["error"]
    assert "report" not in result
    del evaluation.JOBS["test-failure"]


def test_readonly_report_storage_does_not_erase_test_results(monkeypatch, tmp_path):
    monkeypatch.setattr(
        evaluation.subprocess, "run", lambda *a, **kw: subprocess.CompletedProcess(a[0], 0, "5 passed\n", "")
    )
    unwritable = tmp_path / "not-a-directory"
    unwritable.write_text("test")
    monkeypatch.setattr(evaluation, "RESULTS", unwritable / "results")
    result = evaluation.run_local_evals(include_dual=False)
    assert result["status"] == "local_checks_passed"
    assert result["persistence"].startswith("memory_only")
    assert result["release_ready"] is False
