"""
app/services/media_service.py
------------------------------
File saving logic — collision-proof UUID filenames, relative storage paths.
No FastAPI imports — testable with just a file-like object.
"""
import os
import uuid
from fastapi import UploadFile

from app.core.config import settings


def save_upload_file(file: UploadFile, pet_id: int) -> tuple[str, str, int]:
    """
    Saves an UploadFile to a pet-scoped directory with a collision-proof random UUID name.

    Design decisions:
    - Names files with uuid4 hex (not timestamp) to prevent same-second collisions.
    - Stores a *relative* path (e.g. "pets/1/abc123.jpg") — not an absolute disk path —
      so the app survives being moved to another machine.
    - The folder is never served publicly; files are accessed via permission-checked
      GET /media/{id} only.

    Returns:
        (relative_file_path, content_type, file_size_bytes)
    """
    ext = os.path.splitext(file.filename or "")[1].lower() or ".bin"
    random_filename = f"{uuid.uuid4().hex}{ext}"
    rel_dir = os.path.join("pets", str(pet_id))
    abs_dir = os.path.join(settings.UPLOAD_DIR, rel_dir)
    os.makedirs(abs_dir, exist_ok=True)

    rel_path = os.path.join(rel_dir, random_filename)
    abs_path = os.path.join(settings.UPLOAD_DIR, rel_path)

    size = 0
    with open(abs_path, "wb") as f:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            f.write(chunk)

    content_type = file.content_type or "application/octet-stream"
    return rel_path, content_type, size


def resolve_abs_path(rel_path: str) -> str:
    """Convert a stored relative file_path to an absolute disk path."""
    return os.path.join(settings.UPLOAD_DIR, rel_path)
