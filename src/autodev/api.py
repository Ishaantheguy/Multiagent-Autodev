from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from autodev.crew import Autodev


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


def execute_job(job_id: str, request: str):
    try:
        with jobs_lock:
            jobs[job_id]["status"] = "running"

        result = Autodev().crew().kickoff(
            inputs={"user_request": request}
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

    with jobs_lock:
        jobs[job_id] = {
            "status": "queued",
            "request": payload.request,
        }

    executor.submit(execute_job, job_id, payload.request)

    print(jobs)
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
