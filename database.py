# database.py (root shim)
# Kept for backward compatibility. Import from app.core.database instead.
from app.core.database import Base, SessionLocal, engine, get_db  # noqa: F401