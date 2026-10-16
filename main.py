# main.py
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from auth import verify_firebase_token
from database import SessionLocal, engine, Base
from models import Pet, User, Subscription
from schemas import (
    PetCreate, PetResponse,
    UserCreate, UserResponse,
    SubscriptionCreate, SubscriptionResponse,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PetTot Practice Management API",
    description="Backend API with Firebase Authentication and Role-Based Access Control",
    version="1.0.0"
)

# Enable CORS for Web and Mobile clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- dependencies ----------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


bearer_scheme = HTTPBearer()


def get_firebase_user_claims(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """Verifies Firebase ID token from Authorization: Bearer <token> header."""
    token = credentials.credentials
    return verify_firebase_token(token)


def get_current_user(claims: dict = Depends(get_firebase_user_claims), db: Session = Depends(get_db)) -> User:
    """Extracts user from DB mapped by verified Firebase UID."""
    firebase_uid = claims.get("uid")
    if not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing uid in claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not registered. Please complete profile registration at POST /users/",
        )
    return user


def require_role(role: str):
    def checker(current_user: User = Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(status_code=403, detail=f"Only users with role '{role}' can do this")
        return current_user
    return checker


def get_pet_for_user(pet_id: int, user: User, db: Session, owner_only: bool = False) -> Pet:
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")

    if user.role == "owner" and pet.owner_id == user.id:
        return pet

    if user.role == "doctor" and not owner_only:
        subscribed = db.query(Subscription).filter(
            Subscription.doctor_id == user.id,
            Subscription.owner_id == pet.owner_id,
        ).first()
        if subscribed:
            return pet

    raise HTTPException(status_code=403, detail="You don't have access to this pet")


# ---------- health ----------

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "online", "service": "PetTot Backend API", "auth": "Firebase"}


# ---------- users & profile ----------

@app.post("/users/", response_model=UserResponse, tags=["Users"])
def register_user(
    user: UserCreate,
    claims: dict = Depends(get_firebase_user_claims),
    db: Session = Depends(get_db),
):
    """
    Onboarding endpoint: Call this after Firebase sign-up to complete local profile registration.
    """
    firebase_uid = claims.get("uid")
    email = claims.get("email") or user.email
    if not email:
        raise HTTPException(status_code=400, detail="Email is required from token or request body")

    # Check if already registered
    existing_user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already registered with this Firebase account")

    # Check username uniqueness
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username is already taken")

    db_user = User(
        firebase_uid=firebase_uid,
        username=user.username,
        name=user.name,
        email=email,
        role=user.role,
        license_number=user.license_number,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/me", response_model=UserResponse, tags=["Users"])
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/users/", response_model=list[UserResponse], tags=["Users"])
def list_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(User).all()


# ---------- pets ----------

@app.post("/pets/", response_model=PetResponse, tags=["Pets"])
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


@app.get("/pets/", response_model=list[PetResponse], tags=["Pets"])
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


@app.get("/pets/{pet_id}", response_model=PetResponse, tags=["Pets"])
def get_pet(
    pet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_pet_for_user(pet_id, current_user, db)


@app.put("/pets/{pet_id}", response_model=PetResponse, tags=["Pets"])
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


@app.delete("/pets/{pet_id}", tags=["Pets"])
def delete_pet(
    pet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pet = get_pet_for_user(pet_id, current_user, db, owner_only=True)
    db.delete(pet)
    db.commit()
    return {"message": "Pet deleted successfully"}


# ---------- subscriptions ----------

@app.post("/subscriptions/", response_model=SubscriptionResponse, tags=["Subscriptions"])
def create_subscription(
    sub: SubscriptionCreate,
    owner: User = Depends(require_role("owner")),
    db: Session = Depends(get_db),
):
    doctor = db.query(User).filter(User.id == sub.doctor_id).first()
    if not doctor or doctor.role != "doctor":
        raise HTTPException(status_code=400, detail="doctor_id must belong to a user with role 'doctor'")

    db_sub = Subscription(owner_id=owner.id, doctor_id=doctor.id)
    db.add(db_sub)
    db.commit()
    db.refresh(db_sub)
    return db_sub


@app.get("/doctors/me/subscriptions/", tags=["Subscriptions"])
def list_my_subscriptions(doctor: User = Depends(require_role("doctor"))):
    result = []
    for sub in doctor.subscriptions_as_doctor:
        owner = sub.owner
        result.append({
            "subscription_id": sub.id,
            "owner_id": owner.id,
            "owner_name": owner.name,
            "pets": [
                {"id": p.id, "name": p.name, "species": p.species, "age": p.age, "is_adopted": p.is_adopted}
                for p in owner.pets
            ],
        })
    return result