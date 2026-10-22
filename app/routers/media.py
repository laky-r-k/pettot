"""
app/routers/media.py
---------------------
Permission-checked media download/streaming endpoint.
Serves directly from local disk (dev) or redirects to a secure signed URL (Supabase/cloud).
"""
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.db import MediaFile, User
from app.services.media_service import resolve_abs_path, get_signed_media_url, is_cloud_storage_enabled
from app.services.pet_service import get_pet_for_user

router = APIRouter(tags=["Media"])


@router.get("/media/{media_id}")
def get_media_file(
    media_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Permission-checked media download/streaming route.
    Validates that the authenticated user is either the pet's owner or a subscribed doctor.
    Never exposes raw storage paths to the internet.
    """
    media = db.query(MediaFile).filter(MediaFile.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media file not found")

    # Enforce permission check on the associated pet
    get_pet_for_user(media.status_update.pet_id, current_user, db)

    # If Supabase cloud storage is enabled, redirect to temporary signed URL
    if is_cloud_storage_enabled():
        signed_url = get_signed_media_url(media.file_path, expiry_seconds=3600)
        if signed_url:
            return RedirectResponse(url=signed_url)

    # Local disk fallback
    abs_path = resolve_abs_path(media.file_path)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File not found on storage")

    return FileResponse(
        path=abs_path,
        media_type=media.content_type,
        filename=media.original_filename,
    )
