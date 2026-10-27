"""
app/routers/doctors.py
-----------------------
Doctor-facing endpoints (subscription roster view).
"""
from fastapi import APIRouter, Depends

from app.core.security import require_role
from app.models.db import User

router = APIRouter(prefix="/doctors", tags=["Subscriptions"])


@router.get("/me/subscriptions/")
def list_my_subscriptions(doctor: User = Depends(require_role("doctor"))):
    """Doctor sees all owners linked to them and their pets."""
    result = []
    for sub in doctor.subscriptions_as_doctor:
        owner = sub.owner
        result.append({
            "subscription_id": sub.id,
            "owner_id": owner.id,
            "owner_name": owner.name,
            "pets": [
                {
                    "id": p.id,
                    "name": p.name,
                    "species": p.species,
                    "age": p.age,
                    "is_adopted": p.is_adopted,
                }
                for p in owner.pets
            ],
        })
    return result
