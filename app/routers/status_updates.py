"""
app/routers/status_updates.py
------------------------------
Daily post-op check-in upload and retrieval endpoints.
Heavy lifting (file save, video validation) is delegated to services.
"""
import os
from datetime import date
from typing import Optional

import cv2
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.db import MediaFile, StatusUpdate, User
from app.schemas.api import StatusUpdateResponse
from app.services.media_service import save_upload_file, resolve_abs_path
from app.services.pet_service import get_pet_for_user

router = APIRouter(tags=["Status Updates"])


@router.post("/pets/{pet_id}/status-updates/", response_model=StatusUpdateResponse)
def create_status_update(
    pet_id: int,
    face_file: UploadFile = File(..., description="Pet facial photograph"),
    incision_file: UploadFile = File(..., description="Surgical incision site photograph"),
    video_file: UploadFile = File(..., description="10-second walking video"),
    notes: Optional[str] = Form(None, description="Daily observations on appetite, mood, or energy"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Daily post-op check-in upload:
    - Stores 3 files on disk using collision-proof random UUID names
    - Stores paths as relative paths (no public URLs)
    - Validates walking video duration <= 10s
    - Inserts StatusUpdate with processing_status='pending' for future background AI processing
    """
    # 1. Enforce owner-only authorization
    pet = get_pet_for_user(pet_id, current_user, db, owner_only=True)

    # 2. Validate MIME types
    if not (face_file.content_type and face_file.content_type.startswith("image/")):
        raise HTTPException(status_code=400, detail="face_file must be an image.")
    if not (incision_file.content_type and incision_file.content_type.startswith("image/")):
        raise HTTPException(status_code=400, detail="incision_file must be an image.")

    is_video = (video_file.content_type and video_file.content_type.startswith("video/")) or (
        video_file.filename
        and video_file.filename.lower().endswith((".mp4", ".mov", ".avi", ".mkv"))
    )
    if not is_video:
        raise HTTPException(status_code=400, detail="video_file must be a video.")

    # 3. Save files with collision-proof UUID filenames & relative paths
    face_rel_path, face_mime, face_size = save_upload_file(face_file, pet_id)
    inc_rel_path, inc_mime, inc_size = save_upload_file(incision_file, pet_id)
    vid_rel_path, vid_mime, vid_size = save_upload_file(video_file, pet_id)

    # 4. Check video duration via OpenCV
    abs_vid_path = resolve_abs_path(vid_rel_path)
    duration = 0.0
    try:
        cap = cv2.VideoCapture(abs_vid_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        if fps > 0:
            duration = round(float(frame_count / fps), 2)
        cap.release()
    except Exception:
        duration = 0.0

    # Allow slight buffer for codec metadata overhead (up to 10.5 seconds)
    if duration > 10.5:
        for p in [face_rel_path, inc_rel_path, vid_rel_path]:
            abs_p = resolve_abs_path(p)
            if os.path.exists(abs_p):
                os.remove(abs_p)
        raise HTTPException(
            status_code=400,
            detail=f"Walking video exceeds 10-second limit ({duration}s detected). Maximum duration is 10.0 seconds.",
        )

    # 5. Compute day_number based on previous updates count
    prev_count = db.query(StatusUpdate).filter(StatusUpdate.pet_id == pet.id).count()
    day_number = prev_count + 1

    # 6. Create StatusUpdate parent record
    status_update = StatusUpdate(
        pet_id=pet.id,
        day_number=day_number,
        update_date=date.today(),
        notes=notes,
        processing_status="pending",
    )
    db.add(status_update)
    db.commit()
    db.refresh(status_update)

    # 7. Create MediaFile children records
    media_records = [
        MediaFile(
            status_update_id=status_update.id,
            media_type="face_image",
            file_path=face_rel_path,
            original_filename=face_file.filename or "face.jpg",
            content_type=face_mime,
            file_size_bytes=face_size,
        ),
        MediaFile(
            status_update_id=status_update.id,
            media_type="incision_image",
            file_path=inc_rel_path,
            original_filename=incision_file.filename or "incision.jpg",
            content_type=inc_mime,
            file_size_bytes=inc_size,
        ),
        MediaFile(
            status_update_id=status_update.id,
            media_type="walking_video",
            file_path=vid_rel_path,
            original_filename=video_file.filename or "walking.mp4",
            content_type=vid_mime,
            file_size_bytes=vid_size,
            duration_seconds=duration,
        ),
    ]
    db.add_all(media_records)
    db.commit()
    db.refresh(status_update)

    return status_update


@router.get("/pets/{pet_id}/status-updates/", response_model=list[StatusUpdateResponse])
def list_status_updates(
    pet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns full chronological daily status update history for a pet.
    Accessible to pet owner and subscribed veterinarians.
    """
    get_pet_for_user(pet_id, current_user, db)
    return (
        db.query(StatusUpdate)
        .filter(StatusUpdate.pet_id == pet_id)
        .order_by(StatusUpdate.created_at.desc())
        .all()
    )


@router.get("/pets/{pet_id}/status-updates/{update_id}", response_model=StatusUpdateResponse)
def get_status_update(
    pet_id: int,
    update_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns a specific daily status update record."""
    get_pet_for_user(pet_id, current_user, db)
    update = (
        db.query(StatusUpdate)
        .filter(StatusUpdate.id == update_id, StatusUpdate.pet_id == pet_id)
        .first()
    )
    if not update:
        raise HTTPException(status_code=404, detail="Status update not found")
    return update


@router.get("/status-updates/pending/", response_model=list[StatusUpdateResponse])
def list_pending_status_updates(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Background worker hook: Retrieves unanalyzed status updates for background AI batch processing.
    """
    return (
        db.query(StatusUpdate)
        .filter(StatusUpdate.processing_status == "pending")
        .order_by(StatusUpdate.created_at.asc())
        .limit(limit)
        .all()
    )
