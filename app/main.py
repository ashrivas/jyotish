from pathlib import Path
from time import perf_counter
import os
import json
import subprocess
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.models import ChartRequest
from app.astro.engine import compute
from app.astro.ephemeris import ROOT
from app.knowledge.engine import catalog
from app.interpret.plans import technical_summary
from app.evaluation import (
    ReferenceCase,
    compare_reference,
    start_eval_job,
    eval_job,
    latest_report,
    suite_status,
)

app = FastAPI(
    title="Jyoti Accuracy Lab",
    version="0.1.0",
    description="Local research workbench. No predictive model is certified.",
)


@app.middleware("http")
async def local_safety(request: Request, call_next):
    if request.method == "POST":
        origin = request.headers.get("origin")
        # Browser writes are same-origin only; no wildcard CORS or third-party write access.
        if origin and origin != f"{request.url.scheme}://{request.headers.get('host')}":
            return JSONResponse({"error": "Cross-origin writes are disabled."}, status_code=403)
        try:
            if int(request.headers.get("content-length", 0)) > 2_000_000:
                return JSONResponse({"error": "Input exceeds 2 MB."}, status_code=413)
        except ValueError:
            return JSONResponse({"error": "Invalid content length."}, status_code=400)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"
    )
    return response


@app.get("/api/status")
def status():
    return {
        "mode": "local_research",
        "release_ready": False,
        "version": "0.1.0",
        "model": {
            "status": "disabled_until_computation_and_knowledge_gates_pass",
            "preferred": "claude-opus-5-5",
            "configured_credential_available": any(
                os.environ.get(k) for k in ("ANTHROPIC_API_KEY", "AI_GATEWAY_API_KEY", "OPENAI_API_KEY")
            ),
            "note": "This assistant's model session is not a reusable product API credential.",
        },
        "privacy": "Chart inputs are processed in memory and not saved by the application. Browser exports are explicit.",
        "spec_suites": suite_status(),
    }


@app.post("/api/chart")
def chart(request: ChartRequest):
    start = perf_counter()
    try:
        output = compute(request)
        output["technical_summary"] = technical_summary(output)
        output["runtime_ms"] = round((perf_counter() - start) * 1000, 2)
        return output
    except (ValueError, ArithmeticError) as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/sources")
def sources():
    return {**catalog(), "triage": json.loads((ROOT / "refdata/TRIAGE.json").read_text())}


@app.get("/api/fixtures")
def fixtures():
    return json.loads((ROOT / "tests/fixtures/input_matrix.json").read_text())


@app.get("/api/evals")
def evals():
    return latest_report()


@app.post("/api/evals/run")
def run_evals():
    try:
        return JSONResponse(start_eval_job(), status_code=202)
    except RuntimeError as exc:
        raise HTTPException(409, str(exc)) from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise HTTPException(503, "The local evaluation process could not finish: " + str(exc)) from exc


@app.get("/api/evals/jobs/{job_id}")
def get_eval_job(job_id: str):
    result = eval_job(job_id)
    if result is None:
        raise HTTPException(404, "Evaluation job not found; local jobs do not survive a server restart.")
    return result


@app.post("/api/compare")
def compare(reference: ReferenceCase):
    try:
        return compare_reference(reference)
    except (ValueError, ArithmeticError) as exc:
        raise HTTPException(422, str(exc)) from exc


app.mount("/static", StaticFiles(directory=ROOT / "web"), name="static")


@app.get("/")
def index():
    return FileResponse(ROOT / "web/index.html")
