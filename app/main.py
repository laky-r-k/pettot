"""
app/main.py
-----------
FastAPI application factory.
This file's only job: create the app, add middleware, and mount routers.
Business logic lives in routers/ and services/.
"""
import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.core.security import get_current_user
from app.schemas.api import UserResponse

# Import models so SQLAlchemy registers them with Base before create_all
import app.models.db  # noqa: F401

from app.routers import users, pets, subscriptions, doctors, status_updates, media

# Ensure tables exist (create_all is idempotent — safe to run on every startup)
Base.metadata.create_all(bind=engine)

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title="PetTot Practice Management API",
    description=(
        "Backend API with Firebase Authentication, Role-Based Access Control, "
        "and Daily Post-Op Recovery Media"
    ),
    version="2.0.0",
)

# Enable CORS for Web and Mobile clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Standalone endpoints ───────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "online", "service": "PetTot Backend API", "auth": "Firebase"}


@app.get("/me", response_model=UserResponse, tags=["Users"])
def read_me(current_user=Depends(get_current_user)):
    return current_user


# ── Mount all domain routers ───────────────────────────────────────────────────
app.include_router(users.router)
app.include_router(pets.router)
app.include_router(subscriptions.router)
app.include_router(doctors.router)
app.include_router(status_updates.router)
app.include_router(media.router)
