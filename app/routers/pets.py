"""
app/routers/pets.py
--------------------
Pet CRUD endpoints with role-based access control.
"""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.db import Pet, Subscription, User
from app.schemas.api import PetCreate, PetResponse
from app.services.pet_service import get_pet_for_user

router = APIRouter(prefix="/pets", tags=["Pets"])


@router.post("/", response_model=PetResponse)
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


@router.get("/", response_model=list[PetResponse])
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


@router.get("/{pet_id}", response_model=PetResponse)
def get_pet(
    pet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_pet_for_user(pet_id, current_user, db)


@router.put("/{pet_id}", response_model=PetResponse)
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


@router.delete("/{pet_id}")
def delete_pet(
    pet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pet = get_pet_for_user(pet_id, current_user, db, owner_only=True)
    db.delete(pet)
    db.commit()
    return {"message": "Pet deleted successfully"}
