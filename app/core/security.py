"""
app/core/security.py
--------------------
Firebase token verification and FastAPI auth dependencies.
Moved from root auth.py — all auth logic lives here.
"""
import firebase_admin
from firebase_admin import auth as fb_auth, credentials
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.config import settings
from app.core.database import get_db

# Initialize Firebase Admin app singleton (safe to call multiple times)
if not firebase_admin._apps:
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)

bearer_scheme = HTTPBearer()


def verify_firebase_token(token: str) -> Dict[str, Any]:
    """
    Verifies a Firebase ID token sent from client applications (React Web / React Native).
    Returns the decoded token claims dictionary containing:
    - 'uid': The unique Firebase user ID
    - 'email': The user's email address
    """
    try:
        return fb_auth.verify_id_token(token)
    except fb_auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (fb_auth.InvalidIdTokenError, Exception):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_firebase_user_claims(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Dict[str, Any]:
    """FastAPI dependency: verifies Bearer token and returns Firebase claims."""
    return verify_firebase_token(credentials.credentials)


def get_current_user(
    claims: dict = Depends(get_firebase_user_claims),
    db: Session = Depends(get_db),
):
    """FastAPI dependency: maps verified Firebase UID to local User record."""
    # Import here to avoid circular import at module load time
    from app.models.db import User

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
    """FastAPI dependency factory: enforces that the current user has the given role."""
    def checker(current_user=Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(
                status_code=403,
                detail=f"Only users with role '{role}' can do this",
            )
        return current_user
    return checker
