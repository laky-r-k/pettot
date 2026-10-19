"""
app/schemas/api.py
------------------
Pydantic request/response schemas.
These define the API contract — what comes in and what goes out.
"""
from datetime import datetime, date
from typing import Literal, Optional
from pydantic import BaseModel


# ── Pets ──────────────────────────────────────────────────────────────────────

class PetCreate(BaseModel):
    name: str
    species: str
    age: int
    is_adopted: bool = False


class PetResponse(BaseModel):
    id: int
    name: str
    species: str
    age: int
    is_adopted: bool
    owner_id: int

    class Config:
        from_attributes = True


# ── Users ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str
    username: str
    email: str | None = None
    role: Literal["owner", "doctor"]
    license_number: str | None = None


class UserResponse(BaseModel):
    id: int
    firebase_uid: str
    username: str
    name: str
    email: str
    role: str
    license_number: str | None = None

    class Config:
        from_attributes = True


# ── Subscriptions ─────────────────────────────────────────────────────────────

class SubscriptionCreate(BaseModel):
    doctor_id: int


class SubscriptionResponse(BaseModel):
    id: int
    owner_id: int
    doctor_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OwnerDoctorSubscriptionResponse(BaseModel):
    subscription_id: int
    doctor_id: int
    doctor_name: str
    doctor_email: str
    doctor_username: str
    license_number: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Media & Status Updates ────────────────────────────────────────────────────

class MediaFileResponse(BaseModel):
    id: int
    status_update_id: int
    media_type: str
    original_filename: str
    content_type: str
    file_size_bytes: Optional[int] = None
    duration_seconds: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class StatusUpdateResponse(BaseModel):
    id: int
    pet_id: int
    day_number: int
    update_date: date
    notes: Optional[str] = None
    processing_status: str
    analysis_results: Optional[str] = None
    created_at: datetime
    media_files: list[MediaFileResponse] = []

    class Config:
        from_attributes = True
