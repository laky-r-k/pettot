# main.py (root)
# ---------------
# Entry-point shim — kept for uvicorn compatibility.
# All actual code lives in app/
#
# Run server:   uvicorn main:app --reload
# Run new path: uvicorn app.main:app --reload  (both work)

from app.main import app  # noqa: F401 — re-export for uvicorn

# Legacy imports kept so existing test_api.py (on other branches) doesn't break
from app.core.database import get_db  # noqa: F401
from app.core.security import get_firebase_user_claims  # noqa: F401
from app.core.config import settings

UPLOAD_DIR = settings.UPLOAD_DIR