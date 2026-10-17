from pydantic import BaseModel , computed_field
from datetime import datetime


class PetCreate(BaseModel):
    name: str
    species: str
    age: int
    is_adopted: bool = False
    # owner_id removed: it now comes from the logged-in user


class PetResponse(BaseModel):
    id: int
    name: str
    species: str
    age: int
    is_adopted: bool
    owner_id: int

    class Config:
        from_attributes = True


from typing import Literal

class UserCreate(BaseModel):
    name: str
    username: str
    email: str
    password: str
    role: Literal["owner", "doctor"]
    license_number: str | None = None


class UserResponse(BaseModel):
    id: int
    username: str
    name: str
    email: str
    role: str
    license_number: str | None = None

    class Config:
        from_attributes = True


class SubscriptionCreate(BaseModel):
    doctor_id: int
    # owner_id removed: the logged-in owner is the one subscribing


class SubscriptionResponse(BaseModel):
    id: int
    owner_id: int
    doctor_id: int

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class MediaFileResponse(BaseModel):
    id: int
    content_type: str
    original_name: str | None = None

    @computed_field
    @property
    def url(self) -> str:
        return f"/media/{self.id}"

    class Config:
        from_attributes = True

class StatusUpdateResponse(BaseModel):
    id: int
    pet_id: int
    notes: str
    created_at: datetime
    media: list[MediaFileResponse]

    class Config:
        from_attributes = True