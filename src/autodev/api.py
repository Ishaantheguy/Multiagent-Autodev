from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from autodev.crew import Autodev
from fastapi import HTTPException
from fastapi.responses import FileResponse

from autodev.utils.archive import create_project_zip
from autodev.utils.workspaces import get_job_workspace

from pathlib import Path

app = FastAPI(
    title="AutoDev API",
    description="Autonomous software engineering multi-agent system",
    version="0.1.0",
)

executor = ThreadPoolExecutor(max_workers=1)

jobs = {}
jobs_lock = Lock()


class DevelopmentRequest(BaseModel):
    request: str = Field(
        min_length=10,
        max_length=10000,
        description="Description of the software to build",
    )


def execute_job(job_id: str, request: str, job_workspace: str):
    try:
        with jobs_lock:
            jobs[job_id]["status"] = "running"

        autodev_class = Autodev(workspace_path = job_workspace)
        result = autodev_class.crew().kickoff(
            inputs={
                "user_request": request,
                "workspace_path": str(job_workspace),
            }
        )

        with jobs_lock:
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["result"] = str(result)

    except Exception as exc:
        with jobs_lock:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = str(exc)


@app.get("/health")
def health():
    print(jobs)
    return {"status": "ok", "service": "autodev"}


@app.post("/jobs", status_code=202)
def create_job(payload: DevelopmentRequest):
    job_id = str(uuid4())
    workspace = get_job_workspace(job_id)

    with jobs_lock:
        jobs[job_id] = {
            "status": "queued",
            "request": payload.request,
            "workspace_path": str(workspace),
        }

    executor.submit(
        execute_job,
        job_id,
        payload.request,
        str(workspace),
    )

    return {
        "job_id": job_id,
        "status": "queued",
    }

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Job not found",
            )

        return {"job_id": job_id, **job}

@app.get("/jobs/{job_id}/download")
def download_job(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Job not found",
            )

        if job.get("status") != "completed":
            raise HTTPException(
                status_code=409,
                detail=f"Job is not completed. Current status: {job.get('status')}",
            )

        workspace_path = job.get("workspace_path")

    if not workspace_path:
        raise HTTPException(
            status_code=500,
            detail="Workspace path is missing from the job record.",
        )

    project_dir = Path(workspace_path).resolve()

    if not project_dir.is_dir():
        raise HTTPException(
            status_code=404,
            detail=f"Workspace does not exist: {project_dir}",
        )

    output_dir = project_dir.parent / "artifacts"
    output_zip = output_dir / f"autodev-{job_id}.zip"

    try:
        create_project_zip(project_dir, output_zip)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create project ZIP: {exc}",
        ) from exc

    return FileResponse(
        path=output_zip,
        media_type="application/zip",
        filename=f"autodev-{job_id}.zip",
    )

@app.post("/generate")
def generate_project(payload: DevelopmentRequest):
    job_id = str(uuid4())
    workspace = get_job_workspace(job_id)

    try:
        # Run the agents and wait for completion.
        Autodev(workspace_path=workspace).crew().kickoff(
            inputs={
                "user_request": payload.request,
                "workspace_path": str(workspace),
            }
        )

        # Create the ZIP archive.
        output_dir = workspace.parent / "artifacts"
        output_zip = output_dir / f"autodev-{job_id}.zip"

        create_project_zip(workspace, output_zip)

        # Return the ZIP directly to the client.
        return FileResponse(
            path=output_zip,
            media_type="application/zip",
            filename=f"autodev-{job_id}.zip",
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Project generation failed: {exc}",
        ) from exc
