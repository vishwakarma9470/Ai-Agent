from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.config import get_settings
from src.pipeline import IndustryDataReasoningPipeline
from src.security import CurrentUser, resolve_user, require_roles
from src.storage import RunRegistry
from src.observability import configure_logging, get_logger


settings = get_settings()
configure_logging(str(Path(settings.runs_dir) / "api.log"))
logger = get_logger("src.api")

app = FastAPI(title=settings.app_name, version="2.0.0")
registry = RunRegistry(settings.registry_db)


class RunRequest(BaseModel):
    data_path: str = Field(..., description="Local dataset path or SQLite URI, e.g. data/sample_sales.csv")
    query: str = Field(..., description="Natural-language analytics question")
    model: Optional[str] = Field(default=None, description="OpenAI model override")


class ApprovalRequest(BaseModel):
    note: str = ""


def _execute_job(job_id: str, req: RunRequest) -> None:
    try:
        registry.update_job(job_id, "running")
        pipeline = IndustryDataReasoningPipeline(model=req.model, runs_dir=settings.runs_dir)
        output = pipeline.run(req.data_path, req.query)
        registry.save_run(output, job_id=job_id)
        registry.update_job(job_id, "completed", run_id=output["run_id"])
        logger.info("job_completed job_id=%s run_id=%s", job_id, output["run_id"])
    except Exception as exc:
        registry.update_job(job_id, "failed", error=str(exc))
        logger.exception("job_failed job_id=%s", job_id)


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}


@app.post("/runs")
def run_sync(req: RunRequest, user: CurrentUser = Depends(resolve_user)):
    require_roles(user, {"admin", "analyst"})
    pipeline = IndustryDataReasoningPipeline(model=req.model, runs_dir=settings.runs_dir)
    output = pipeline.run(req.data_path, req.query)
    registry.save_run(output)
    return output


@app.post("/jobs")
def submit_job(req: RunRequest, background_tasks: BackgroundTasks, user: CurrentUser = Depends(resolve_user)):
    require_roles(user, {"admin", "analyst"})
    job_id = str(uuid.uuid4())[:10]
    registry.create_job(job_id)
    background_tasks.add_task(_execute_job, job_id, req)
    return {"job_id": job_id, "status": "queued"}


@app.get("/jobs/{job_id}")
def get_job(job_id: str, user: CurrentUser = Depends(resolve_user)):
    require_roles(user, {"admin", "analyst", "viewer"})
    job = registry.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/runs")
def list_runs(limit: int = 25, user: CurrentUser = Depends(resolve_user)):
    require_roles(user, {"admin", "analyst", "viewer"})
    return {"runs": registry.list_runs(limit=limit)}


@app.get("/runs/{run_id}")
def get_run(run_id: str, user: CurrentUser = Depends(resolve_user)):
    require_roles(user, {"admin", "analyst", "viewer"})
    run = registry.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@app.get("/runs/{run_id}/report")
def download_report(run_id: str, user: CurrentUser = Depends(resolve_user)):
    require_roles(user, {"admin", "analyst", "viewer"})
    run = registry.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    report_path = run.get("report_path")
    if not report_path or not Path(report_path).exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    return FileResponse(report_path, filename=f"report_{run_id}.md")


@app.post("/runs/{run_id}/approve")
def approve_run(run_id: str, req: ApprovalRequest, user: CurrentUser = Depends(resolve_user)):
    require_roles(user, {"admin"})
    ok = registry.approve_run(run_id, "approved", req.note)
    if not ok:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"run_id": run_id, "approval_status": "approved", "note": req.note}


@app.post("/runs/{run_id}/reject")
def reject_run(run_id: str, req: ApprovalRequest, user: CurrentUser = Depends(resolve_user)):
    require_roles(user, {"admin"})
    ok = registry.approve_run(run_id, "rejected", req.note)
    if not ok:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"run_id": run_id, "approval_status": "rejected", "note": req.note}
