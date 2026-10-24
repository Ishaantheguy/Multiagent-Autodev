from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_WORKSPACE_ROOT = (PROJECT_ROOT / "workspace").resolve()


class WriteFileInput(BaseModel):
    path: str = Field(
        description="Relative file path inside the assigned workspace."
    )
    content: str = Field(
        description="Complete text content of the file."
    )


class WriteWorkspaceFile(BaseTool):
    name: str = "write_workspace_file"

    description: str = (
        "Create or replace a text file inside the workspace assigned "
        "to this generation job. Always use a relative file path, "
        "such as app/main.py or README.md. Do not use absolute paths."
    )

    args_schema: type[BaseModel] = WriteFileInput

    _workspace_root: Path = PrivateAttr(
        default=DEFAULT_WORKSPACE_ROOT
    )

    def __init__(self, workspace_path: str | Path | None = None, **kwargs):
        super().__init__(**kwargs)

        root = (
            Path(workspace_path)
            if workspace_path is not None
            else DEFAULT_WORKSPACE_ROOT
        )

        root.mkdir(parents=True, exist_ok=True)
        self._workspace_root = root.resolve()

    def _run(self, path: str, content: str) -> str:
        relative = Path(path)

        if relative.is_absolute():
            return "Error: absolute paths are not allowed."

        if ".." in relative.parts:
            return "Error: parent-directory traversal is not allowed."

        if not relative.parts:
            return "Error: a file path must be provided."

        target = (self._workspace_root / relative).resolve()

        if not target.is_relative_to(self._workspace_root):
            return "Error: path escapes the workspace."

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

        return (
            f"Created or updated: {relative.as_posix()} "
            f"(workspace: {self._workspace_root})"
        )
