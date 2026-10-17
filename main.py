# main.py
import os
import uuid
from datetime import date
from typing import Optional

import cv2
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from auth import verify_firebase_token
from database import SessionLocal, engine, Base
from models import Pet, User, Subscription, StatusUpdate, MediaFile
from schemas import (
    PetCreate, PetResponse,
    UserCreate, UserResponse,
    SubscriptionCreate, SubscriptionResponse, OwnerDoctorSubscriptionResponse,
    StatusUpdateResponse, MediaFileResponse,
)

Base.metadata.create_all(bind=engine)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title="PetTot Practice Management API",
    description="Backend API with Firebase Authentication, Role-Based Access Control, and Daily Post-Op Recovery Media",
    version="1.1.0"
)

# Enable CORS for Web and Mobile clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- helpers ----------

def save_upload_file(file: UploadFile, pet_id: int) -> tuple[str, str, int]:
    """
    Saves an UploadFile to a pet-scoped directory with a collision-proof random UUID name.
    Returns: (relative_file_path, content_type, file_size_bytes)
    """
    ext = os.path.splitext(file.filename or "")[1].lower() or ".bin"
    random_filename = f"{uuid.uuid4().hex}{ext}"
    rel_dir = os.path.join("pets", str(pet_id))
    abs_dir = os.path.join(UPLOAD_DIR, rel_dir)
    os.makedirs(abs_dir, exist_ok=True)

    rel_path = os.path.join(rel_dir, random_filename)
    abs_path = os.path.join(UPLOAD_DIR, rel_path)

    size = 0
    with open(abs_path, "wb") as f:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            f.write(chunk)

    content_type = file.content_type or "application/octet-stream"
    return rel_path, content_type, size


# ---------- dependencies ----------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


bearer_scheme = HTTPBearer()


def get_firebase_user_claims(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """Verifies Firebase ID token from Authorization: Bearer <token> header."""
    token = credentials.credentials
    return verify_firebase_token(token)


def get_current_user(claims: dict = Depends(get_firebase_user_claims), db: Session = Depends(get_db)) -> User:
    """Extracts user from DB mapped by verified Firebase UID."""
    firebase_uid = claims.get("uid")
    if not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing uid in claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not registered. Please complete profile registration at POST /users/",
        )
    return user


def require_role(role: str):
    def checker(current_user: User = Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(status_code=403, detail=f"Only users with role '{role}' can do this")
        return current_user
    return checker


def get_pet_for_user(pet_id: int, user: User, db: Session, owner_only: bool = False) -> Pet:
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")

    if user.role == "owner" and pet.owner_id == user.id:
        return pet

    if user.role == "doctor" and not owner_only:
        subscribed = db.query(Subscription).filter(
            Subscription.doctor_id == user.id,
            Subscription.owner_id == pet.owner_id,
        ).first()
        if subscribed:
            return pet

    raise HTTPException(status_code=403, detail="You don't have access to this pet")


# ---------- health ----------

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "online", "service": "PetTot Backend API", "auth": "Firebase"}


# ---------- users & profile ----------

@app.post("/users/", response_model=UserResponse, tags=["Users"])
def register_user(
    user: UserCreate,
    claims: dict = Depends(get_firebase_user_claims),
    db: Session = Depends(get_db),
):
    """
    Onboarding endpoint: Call this after Firebase sign-up to complete local profile registration.
    """
    firebase_uid = claims.get("uid")
    email = claims.get("email") or user.email
    if not email:
        raise HTTPException(status_code=400, detail="Email is required from token or request body")

    if db.query(User).filter(User.firebase_uid == firebase_uid).first():
        raise HTTPException(status_code=400, detail="User already registered with this Firebase account")

    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username is already taken")

    db_user = User(
        firebase_uid=firebase_uid,
        username=user.username,
        name=user.name,
        email=email,
        role=user.role,
        license_number=user.license_number,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/me", response_model=UserResponse, tags=["Users"])
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/users/", response_model=list[UserResponse], tags=["Users"])
def list_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(User).all()


# ---------- pets ----------

@app.post("/pets/", response_model=PetResponse, tags=["Pets"])
def create_pet(
    pet: PetCreate,
    owner: User = Depends(require_role("owner")),
    db: Session = Depends(get_db),
):
    db_pet = Pet(**pet.model_dump(), owner_id=owner.id)
    db.add(db_pet)
    db.commit()
    db.refresh(db_pet)
    return db_pet


@app.get("/pets/", response_model=list[PetResponse], tags=["Pets"])
def list_pets(
    species: Optional[str] = None,
    is_adopted: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Pet)

    if current_user.role == "owner":
        query = query.filter(Pet.owner_id == current_user.id)
    else:
        subs = db.query(Subscription).filter(Subscription.doctor_id == current_user.id).all()
        query = query.filter(Pet.owner_id.in_([s.owner_id for s in subs]))

    if species is not None:
        query = query.filter(Pet.species == species)
    if is_adopted is not None:
        query = query.filter(Pet.is_adopted == is_adopted)

    return query.all()


@app.get("/pets/{pet_id}", response_model=PetResponse, tags=["Pets"])
def get_pet(
    pet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_pet_for_user(pet_id, current_user, db)


@app.put("/pets/{pet_id}", response_model=PetResponse, tags=["Pets"])
def update_pet(
    pet_id: int,
    updated_pet: PetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pet = get_pet_for_user(pet_id, current_user, db, owner_only=True)

    pet.name = updated_pet.name
    pet.species = updated_pet.species
    pet.age = updated_pet.age
    pet.is_adopted = updated_pet.is_adopted

    db.commit()
    db.refresh(pet)
    return pet


@app.delete("/pets/{pet_id}", tags=["Pets"])
def delete_pet(
    pet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pet = get_pet_for_user(pet_id, current_user, db, owner_only=True)
    db.delete(pet)
    db.commit()
    return {"message": "Pet deleted successfully"}


# ---------- subscriptions ----------

@app.post("/subscriptions/", response_model=SubscriptionResponse, tags=["Subscriptions"])
def create_subscription(
    sub: SubscriptionCreate,
    owner: User = Depends(require_role("owner")),
    db: Session = Depends(get_db),
):
    doctor = db.query(User).filter(User.id == sub.doctor_id).first()
    if not doctor or doctor.role != "doctor":
        raise HTTPException(status_code=400, detail="doctor_id must belong to a user with role 'doctor'")

    # Prevent duplicate subscription to the same doctor
    existing_sub = db.query(Subscription).filter(
        Subscription.owner_id == owner.id,
        Subscription.doctor_id == doctor.id,
    ).first()
    if existing_sub:
        raise HTTPException(
            status_code=400,
            detail=f"You are already subscribed to Dr. {doctor.name}."
        )

    db_sub = Subscription(owner_id=owner.id, doctor_id=doctor.id)
    db.add(db_sub)
    db.commit()
    db.refresh(db_sub)
    return db_sub


@app.get("/subscriptions/me/", response_model=list[OwnerDoctorSubscriptionResponse], tags=["Subscriptions"])
def list_my_doctors(
    owner: User = Depends(require_role("owner")),
    db: Session = Depends(get_db),
):
    """Lists all veterinarians the authenticated pet owner is currently linked with."""
    subs = db.query(Subscription).filter(Subscription.owner_id == owner.id).all()
    results = []
    for s in subs:
        doc = s.doctor
        results.append({
            "subscription_id": s.id,
            "doctor_id": doc.id,
            "doctor_name": doc.name,
            "doctor_email": doc.email,
            "doctor_username": doc.username,
            "license_number": doc.license_number,
            "created_at": s.created_at or s.id,
        })
    return results


@app.delete("/subscriptions/{subscription_id}", tags=["Subscriptions"])
def delete_subscription(
    subscription_id: int,
    owner: User = Depends(require_role("owner")),
    db: Session = Depends(get_db),
):
    """Allows an owner to unsubscribe / unlink from a veterinarian."""
    sub = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.owner_id == owner.id,
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    db.delete(sub)
    db.commit()
    return {"message": "Successfully unsubscribed from veterinarian"}


@app.get("/doctors/me/subscriptions/", tags=["Subscriptions"])
def list_my_subscriptions(doctor: User = Depends(require_role("doctor"))):
    result = []
    for sub in doctor.subscriptions_as_doctor:
        owner = sub.owner
        result.append({
            "subscription_id": sub.id,
            "owner_id": owner.id,
            "owner_name": owner.name,
            "pets": [
                {"id": p.id, "name": p.name, "species": p.species, "age": p.age, "is_adopted": p.is_adopted}
                for p in owner.pets
            ],
        })
    return result


# ---------- status updates & media ----------

@app.post("/pets/{pet_id}/status-updates/", response_model=StatusUpdateResponse, tags=["Status Updates"])
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
    
    is_video = (video_file.content_type and video_file.content_type.startswith("video/")) or \
               (video_file.filename and video_file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')))
    if not is_video:
        raise HTTPException(status_code=400, detail="video_file must be a video.")

    # 3. Save files with collision-proof UUID filenames & relative paths
    face_rel_path, face_mime, face_size = save_upload_file(face_file, pet_id)
    inc_rel_path, inc_mime, inc_size = save_upload_file(incision_file, pet_id)
    vid_rel_path, vid_mime, vid_size = save_upload_file(video_file, pet_id)

    # 4. Check video duration via OpenCV
    abs_vid_path = os.path.join(UPLOAD_DIR, vid_rel_path)
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
        # Delete the stored files if duration check fails
        for p in [face_rel_path, inc_rel_path, vid_rel_path]:
            abs_p = os.path.join(UPLOAD_DIR, p)
            if os.path.exists(abs_p):
                os.remove(abs_p)
        raise HTTPException(
            status_code=400,
            detail=f"Walking video exceeds 10-second limit ({duration}s detected). Maximum duration is 10.0 seconds."
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


@app.get("/pets/{pet_id}/status-updates/", response_model=list[StatusUpdateResponse], tags=["Status Updates"])
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


@app.get("/pets/{pet_id}/status-updates/{update_id}", response_model=StatusUpdateResponse, tags=["Status Updates"])
def get_status_update(
    pet_id: int,
    update_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns a specific daily status update record.
    Accessible to pet owner and subscribed veterinarians.
    """
    get_pet_for_user(pet_id, current_user, db)
    update = (
        db.query(StatusUpdate)
        .filter(StatusUpdate.id == update_id, StatusUpdate.pet_id == pet_id)
        .first()
    )
    if not update:
        raise HTTPException(status_code=404, detail="Status update not found")
    return update


@app.get("/media/{media_id}", tags=["Media"])
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

    abs_path = os.path.join(UPLOAD_DIR, media.file_path)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File not found on storage")

    return FileResponse(
        path=abs_path,
        media_type=media.content_type,
        filename=media.original_filename
    )


@app.get("/status-updates/pending/", response_model=list[StatusUpdateResponse], tags=["Status Updates"])
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