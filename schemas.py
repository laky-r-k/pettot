# schemas.py (root shim)
# Kept for backward compatibility. Import from app.schemas.api instead.
from app.schemas.api import (  # noqa: F401
    PetCreate, PetResponse,
    UserCreate, UserResponse,
    SubscriptionCreate, SubscriptionResponse, OwnerDoctorSubscriptionResponse,
    StatusUpdateResponse, MediaFileResponse,
)