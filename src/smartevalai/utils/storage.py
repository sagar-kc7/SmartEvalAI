"""Helpers for saving uploaded files to disk.

For this project, uploads are stored on local disk under `uploads/`. In a
production deployment, this is the natural place to swap in S3 / GCS /
Azure Blob storage without touching any calling code, since callers only
ever see the returned path string.
"""

import uuid
from pathlib import Path

from fastapi import UploadFile

UPLOAD_DIR = Path("uploads")


def save_upload(file: UploadFile, subfolder: str) -> str:
    """Save an uploaded file to disk under a UUID-prefixed name.

    Args:
        file: The incoming FastAPI UploadFile.
        subfolder: Logical grouping, e.g. "submissions" or "question_papers".

    Returns:
        The path to the saved file, as a string, relative to the project root.
    """
    target_dir = UPLOAD_DIR / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)

    extension = Path(file.filename).suffix
    unique_name = f"{uuid.uuid4().hex}{extension}"
    destination = target_dir / unique_name

    with destination.open("wb") as buffer:
        buffer.write(file.file.read())

    return str(destination)