from datetime import datetime, date
from typing import Literal, Optional
from pydantic import BaseModel


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


class SubscriptionCreate(BaseModel):
    doctor_id: int


class SubscriptionResponse(BaseModel):
    id: int
    owner_id: int
    doctor_id: int

    class Config:
        from_attributes = True


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