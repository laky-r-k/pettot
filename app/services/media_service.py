"""
app/services/media_service.py
------------------------------
File saving logic — collision-proof UUID filenames, relative storage paths.
Supports:
1. Supabase Storage bucket (in production)
2. Local disk fallback (in local development or testing)
"""
import io
import os
import uuid
from typing import Optional
from fastapi import UploadFile

from app.core.config import settings

_supabase_client = None


def get_supabase_client():
    """Lazily initializes Supabase client if credentials are provided."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        try:
            from supabase import create_client
            _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            return _supabase_client
        except Exception as e:
            print(f"[Supabase Storage] Failed to initialize client: {e}")
            return None
    return None


def is_cloud_storage_enabled() -> bool:
    """Returns True if Supabase is configured and reachable."""
    return get_supabase_client() is not None


def save_upload_file(file: UploadFile, pet_id: int) -> tuple[str, str, int]:
    """
    Saves an UploadFile with a collision-proof random UUID name.
    Uploads to Supabase Storage if configured; otherwise saves to local UPLOAD_DIR.

    Returns:
        (relative_file_path, content_type, file_size_bytes)
    """
    ext = os.path.splitext(file.filename or "")[1].lower() or ".bin"
    random_filename = f"{uuid.uuid4().hex}{ext}"
    rel_path = f"pets/{pet_id}/{random_filename}"

    # Read content into memory
    content = file.file.read()
    size = len(content)
    content_type = file.content_type or "application/octet-stream"

    supabase = get_supabase_client()
    if supabase:
        try:
            # Upload to Supabase Storage Bucket
            supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
                path=rel_path,
                file=content,
                file_options={"content-type": content_type}
            )
            return rel_path, content_type, size
        except Exception as e:
            print(f"[Supabase Storage] Upload failed, falling back to local: {e}")

    # Local disk fallback
    abs_path = os.path.join(settings.UPLOAD_DIR, rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "wb") as f:
        f.write(content)

    return rel_path, content_type, size


def delete_stored_file(rel_path: str):
    """Deletes a file from either Supabase or local storage."""
    supabase = get_supabase_client()
    if supabase:
        try:
            supabase.storage.from_(settings.SUPABASE_BUCKET).remove([rel_path])
            return
        except Exception:
            pass

    abs_path = os.path.join(settings.UPLOAD_DIR, rel_path)
    if os.path.exists(abs_path):
        os.remove(abs_path)


def get_signed_media_url(rel_path: str, expiry_seconds: int = 3600) -> Optional[str]:
    """Generates a secure, temporary signed URL from Supabase Storage."""
    supabase = get_supabase_client()
    if supabase:
        try:
            res = supabase.storage.from_(settings.SUPABASE_BUCKET).create_signed_url(
                rel_path, expiry_seconds
            )
            if isinstance(res, dict) and "signedURL" in res:
                return res["signedURL"]
            elif hasattr(res, "signed_url"):
                return res.signed_url
            elif isinstance(res, str):
                return res
        except Exception as e:
            print(f"[Supabase Storage] Failed to generate signed URL: {e}")
    return None


def resolve_abs_path(rel_path: str) -> str:
    """Convert a stored relative file_path to an absolute disk path."""
    return os.path.join(settings.UPLOAD_DIR, rel_path)
