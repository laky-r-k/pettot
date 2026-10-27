# main.py
# --------
# Uvicorn entry point. Run with:
#   uvicorn main:app --reload
# or equivalently:
#   uvicorn app.main:app --reload

from app.main import app  # noqa: F401