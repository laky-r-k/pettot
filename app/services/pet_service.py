"""
app/services/pet_service.py
----------------------------
Pet access-control helper shared by pet, status-update, and media routers.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.db import Pet, Subscription, User


def get_pet_for_user(
    pet_id: int, user: User, db: Session, owner_only: bool = False
) -> Pet:
    """
    Fetch a pet, enforcing role-based access control:
    - Owners can only access their own pets.
    - Doctors can access a pet if they are subscribed to the pet's owner
      (unless owner_only=True, e.g. for write operations).
    Raises 404 if not found, 403 if unauthorized.
    """
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")

    if user.role == "owner" and pet.owner_id == user.id:
        return pet

    if user.role == "doctor" and not owner_only:
        subscribed = (
            db.query(Subscription)
            .filter(
                Subscription.doctor_id == user.id,
                Subscription.owner_id == pet.owner_id,
            )
            .first()
        )
        if subscribed:
            return pet

    raise HTTPException(status_code=403, detail="You don't have access to this pet")
