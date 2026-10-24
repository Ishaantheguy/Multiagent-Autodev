from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = PROJECT_ROOT / "workspace"


def get_job_workspace(job_id: str) -> Path:
    """
    Return a workspace path for a validated job ID.
    """

    if not re.fullmatch(r"[a-f0-9-]{36}", job_id):
        raise ValueError("Invalid job ID")

    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)

    workspace = (WORKSPACE_ROOT / job_id).resolve()

    if not workspace.is_relative_to(WORKSPACE_ROOT.resolve()):
        raise ValueError("Invalid workspace path")

    workspace.mkdir(parents=True, exist_ok=True)

    return workspace
