from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = (PROJECT_ROOT / "workspace").resolve()


class WriteFileInput(BaseModel):
    path: str = Field(
        description="Relative file path inside the workspace."
    )
    content: str = Field(
        description="Complete text content of the file."
    )


class WriteWorkspaceFile(BaseTool):
    name: str = "write_workspace_file"
    description: str = (
        "Create or replace a text file inside the designated "
        "workspace. The path must be relative to the workspace."
    )
    args_schema: type[BaseModel] = WriteFileInput

    def _run(self, path: str, content: str) -> str:
        relative = Path(path)

        if relative.is_absolute():
            return "Error: absolute paths are not allowed."

        if ".." in relative.parts:
            return "Error: parent-directory traversal is not allowed."

        target = (WORKSPACE_ROOT / relative).resolve()

        if not target.is_relative_to(WORKSPACE_ROOT):
            return "Error: path escapes the workspace."

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

        return f"Created or updated: {relative.as_posix()}"
