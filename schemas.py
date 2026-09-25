from pydantic import BaseModel

class PetCreate(BaseModel):
    name: str
    species: str
    age: int
    is_adopted: bool = False
    owner_id: int   # which user this pet belongs to

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
    email: str
    password: str
    role: str  # "owner" or "doctor"
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
    owner_id: int
    doctor_id: int

class SubscriptionResponse(BaseModel):
    id: int
    owner_id: int
    doctor_id: int

    class Config:
        from_attributes = True