# main.py
from fastapi import FastAPI, Depends, HTTPException

from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Pet , User , Subscription
from schemas import PetCreate, PetResponse, UserCreate, UserResponse ,SubscriptionCreate, SubscriptionResponse
from typing import Optional
# this actually creates the "items" table in test.db, if it doesn't exist
Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

"""Endpoints to implement:

Method	Route	Does what
POST	/pets/	Create a pet
GET	/pets/	List all pets
GET	/pets/{pet_id}	Get one pet
PUT	/pets/{pet_id}	Update a pet (new — you haven't done this yet)
DELETE	/pets/{pet_id}	Delete a pet (new too)"""

@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user.model_dump())
    db.add(db_user)
    db.commit()
    return db_user
@app.get("/users/", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users    

@app.post("/pets/",response_model=PetResponse)
def create_pet(pet: PetCreate, db: Session = Depends(get_db)):
    db_pet = Pet(**pet.model_dump())
    db.add(db_pet)
    db.commit()
    return db_pet

@app.get("/pets/", response_model=list[PetResponse])
def list_pets(species: Optional[str] = None, is_adopted: Optional[bool] = None, db: Session = Depends(get_db)):
    pets = db.query(Pet)
    if species:
        pets = pets.filter(Pet.species == species)
    if is_adopted is not None:
        pets = pets.filter(Pet.is_adopted == is_adopted)
    return pets.all()

@app.get("/pets/{pet_id}", response_model=PetResponse)
def get_pet(pet_id: int, db: Session = Depends(get_db)):
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    return pet
@app.put("/pets/{pet_id}", response_model=PetResponse)
def update_pet(pet_id: int, updated_pet: PetCreate, db: Session = Depends(get_db)):
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    
    pet.name = updated_pet.name
    pet.species = updated_pet.species
    pet.age = updated_pet.age
    pet.is_adopted = updated_pet.is_adopted
    
    db.commit()
    return pet

@app.delete("/pets/{pet_id}")
def delete_pet(pet_id: int, db: Session = Depends(get_db)):
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    
    db.delete(pet)
    db.commit()
    return {"message": "Pet deleted successfully"}


@app.post("/subscriptions/", response_model=SubscriptionResponse)
def create_subscription(sub: SubscriptionCreate, db: Session = Depends(get_db)):
    db_sub = Subscription(**sub.model_dump())
    db.add(db_sub)
    db.commit()
    db.refresh(db_sub)
    return db_sub

@app.get("/doctors/{doctor_id}/subscriptions/")
def list_subscriptions_for_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(User).filter(User.id == doctor_id, User.role == "doctor").first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found") 
    result =[]

    for sub in doctor.subscriptions_as_doctor:
        owner = sub.owner
        result.append({
            "subscription_id": sub.id,
            "owner_id": owner.id,
            "owner_name": owner.name,
            "pets": [{"id": pet.id, "name": pet.name, "species": pet.species, "age": pet.age, "is_adopted": pet.is_adopted} for pet in owner.pets]
        })
    return result