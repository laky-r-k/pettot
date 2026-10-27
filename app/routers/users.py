"""
app/routers/users.py
---------------------
User registration and profile endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_firebase_user_claims, get_current_user
from app.models.db import User
from app.schemas.api import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponse)
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

    if db.query(User).filter(User.firebase_uid == firebase_uid).first():
        raise HTTPException(status_code=400, detail="User already registered with this Firebase account")

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


@router.get("/", response_model=list[UserResponse])
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(User).all()
