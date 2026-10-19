# auth.py (root shim)
# Kept for backward compatibility. Import from app.core.security instead.
from app.core.security import verify_firebase_token, get_firebase_user_claims  # noqa: F401
from fastapi import HTTPException  # noqa: F401 — re-export used by old test_api.py