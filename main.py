# main.py
from typing import Optional

import jwt
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi import UploadFile, File
from auth import hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from database import SessionLocal, engine, Base
from models import Pet, User, Subscription
from schemas import (
    PetCreate, PetResponse,
    UserCreate, UserResponse,
    SubscriptionCreate, SubscriptionResponse,
    Token,
)

Base.metadata.create_all(bind=engine)

app = FastAPI()


# ---------- dependencies ----------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
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


# ---------- auth & users ----------

@app.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()

    if not user or not verify_password(form.password, user.password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(
        username=user.username,
        name=user.name,
        email=user.email,
        password=hash_password(user.password),
        role=user.role,
        license_number=user.license_number,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/users/", response_model=list[UserResponse])
def list_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Now requires login. Still lists everyone, so treat as temporary.
    return db.query(User).all()


# ---------- pets ----------

@app.post("/pets/", response_model=PetResponse)
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


@app.get("/pets/", response_model=list[PetResponse])
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


@app.get("/pets/{pet_id}", response_model=PetResponse)
def get_pet(
    pet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_pet_for_user(pet_id, current_user, db)


@app.put("/pets/{pet_id}", response_model=PetResponse)
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


@app.delete("/pets/{pet_id}")
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

@app.post("/subscriptions/", response_model=SubscriptionResponse)
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


@app.get("/doctors/me/subscriptions/")
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



# file upload endpoint


from fastapi import Form
from models import Pet, User, Subscription, StatusUpdate, MediaFile
from schemas import StatusUpdateResponse      # add to your existing schemas import
from storage import save_upload, UPLOAD_DIR
from fastapi.responses import FileResponse

@app.post("/pets/{pet_id}/upload")
def upload_pet_file(
    pet_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pet = get_pet_for_user(pet_id, current_user, db, owner_only=True)
    path = save_upload(file, pet.id)
    return {"path": path, "original_name": file.filename}

MAX_FILES_PER_UPDATE = 5


@app.post("/pets/{pet_id}/updates", response_model=StatusUpdateResponse)
def create_status_update(
    pet_id: int,
    notes: str = Form(""),
    files: list[UploadFile] = File(
    default=[],
    json_schema_extra={"items": {"type": "string", "format": "binary"}},
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pet = get_pet_for_user(pet_id, current_user, db, owner_only=True)

    files = [f for f in (files or []) if f.filename]   # ignore empty file slots

    if not notes.strip() and not files:
        raise HTTPException(status_code=400, detail="Add notes or at least one photo/video")
    if len(files) > MAX_FILES_PER_UPDATE:
        raise HTTPException(status_code=400, detail=f"At most {MAX_FILES_PER_UPDATE} files per update")

    saved_paths = []
    try:
        update = StatusUpdate(pet_id=pet.id, notes=notes.strip())
        for f in files:
            path = save_upload(f, pet.id)
            saved_paths.append(path)
            update.media.append(
                MediaFile(path=path, content_type=f.content_type, original_name=f.filename)
            )
        db.add(update)
        db.commit()
        db.refresh(update)
    except Exception:
        db.rollback()
        for p in saved_paths:                          # undo files saved before the failure
            (UPLOAD_DIR / p).unlink(missing_ok=True)
        raise

    return update


@app.get("/pets/{pet_id}/updates", response_model=list[StatusUpdateResponse])
def list_status_updates(
    pet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pet = get_pet_for_user(pet_id, current_user, db)   # owners and subscribed doctors
    return (
        db.query(StatusUpdate)
        .filter(StatusUpdate.pet_id == pet.id)
        .order_by(StatusUpdate.created_at.desc())
        .all()
    )

@app.get("/media/{media_id}")
def get_media(
    media_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    media = db.query(MediaFile).filter(MediaFile.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="File not found")

    # same rule as viewing the pet: its owner, or a doctor the owner subscribed to
    get_pet_for_user(media.status_update.pet_id, current_user, db)

    upload_root = UPLOAD_DIR.resolve()
    file_path = (UPLOAD_DIR / media.path).resolve()
    if not file_path.is_relative_to(upload_root) or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, media_type=media.content_type)