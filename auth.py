import os
from typing import Dict, Any
from dotenv import load_dotenv
from fastapi import HTTPException, status
import firebase_admin
from firebase_admin import auth as fb_auth, credentials

load_dotenv()

CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-credentials.json")

# Initialize Firebase Admin app singleton
if not firebase_admin._apps:
    cred = credentials.Certificate(CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)


def verify_firebase_token(token: str) -> Dict[str, Any]:
    """
    Verifies a Firebase ID token sent from client applications (React Web / React Native).
    Returns the decoded token claims dictionary containing:
    - 'uid': The unique Firebase user ID
    - 'email': The user's email address
    """
    try:
        decoded_token = fb_auth.verify_id_token(token)
        return decoded_token
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