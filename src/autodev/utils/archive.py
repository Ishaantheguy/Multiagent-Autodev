from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def create_project_zip(project_dir: Path, output_zip: Path) -> Path:
    """
    Package a generated project directory into a ZIP archive.
    """

    project_dir = project_dir.resolve()
    output_zip = output_zip.resolve()

    if not project_dir.is_dir():
        raise FileNotFoundError(
            f"Project directory does not exist: {project_dir}"
        )

    if output_zip.is_relative_to(project_dir):
        raise ValueError(
            "The ZIP archive must be outside the project directory."
        )

    output_zip.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(output_zip, "w", compression=ZIP_DEFLATED) as archive:
        for file_path in project_dir.rglob("*"):
            if not file_path.is_file():
                continue

            # Skip common generated files.
            if any(
                part in {".git", ".venv", "__pycache__", ".pytest_cache"}
                for part in file_path.parts
            ):
                continue

            archive.write(
                file_path,
                arcname=file_path.relative_to(project_dir),
            )

    return output_zip
