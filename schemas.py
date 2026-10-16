from pydantic import BaseModel


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