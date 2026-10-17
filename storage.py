import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

UPLOAD_DIR = Path("uploads")
CHUNK_SIZE = 1024 * 1024            # read 1 MB at a time
MAX_BYTES = 50 * 1024 * 1024        # 50 MB limit

ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "video/mp4": ".mp4",
}


def save_upload(file: UploadFile, pet_id: int) -> str:
    ext = ALLOWED_TYPES.get(file.content_type)
    if ext is None:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG or MP4 files are allowed")

    pet_dir = UPLOAD_DIR / f"pet_{pet_id}"
    pet_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{ext}"
    dest = pet_dir / filename

    size = 0
    try:
        with open(dest, "wb") as out:
            while chunk := file.file.read(CHUNK_SIZE):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise HTTPException(status_code=413, detail="File too large (max 50 MB)")
                out.write(chunk)
    except Exception:
        dest.unlink(missing_ok=True)    # never leave a half-written file behind
        raise

    return f"pet_{pet_id}/{filename}"