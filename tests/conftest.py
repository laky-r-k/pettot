"""
tests/conftest.py
-----------------
Shared pytest fixtures for the whole test suite.
All tests import from here via pytest's conftest discovery.
"""
import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import get_firebase_user_claims
from app.main import app as fastapi_app
import app.models.db  # noqa: F401 — ensure all models are registered

app = fastapi_app  # alias so fixtures below can use `app` consistently


# ── In-memory test database ────────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# ── Firebase auth mock ─────────────────────────────────────────────────────────

CURRENT_MOCK_CLAIMS: dict = {}


def override_firebase_claims():
    from fastapi import HTTPException
    if not CURRENT_MOCK_CLAIMS:
        raise HTTPException(status_code=401, detail="No token provided")
    return CURRENT_MOCK_CLAIMS


@pytest.fixture
def client():
    """Returns a TestClient with auth override active."""
    app.dependency_overrides[get_firebase_user_claims] = override_firebase_claims
    yield TestClient(app)
    app.dependency_overrides.pop(get_firebase_user_claims, None)


@pytest.fixture
def set_user():
    """Helper fixture: set the active mock Firebase user claims."""
    def _set(uid: str, email: str):
        CURRENT_MOCK_CLAIMS.clear()
        CURRENT_MOCK_CLAIMS.update({"uid": uid, "email": email})
    yield _set
    CURRENT_MOCK_CLAIMS.clear()


# ── Sample file factories ──────────────────────────────────────────────────────

FAKE_JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb"
FAKE_MP4 = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42"


@pytest.fixture
def fake_upload_files():
    """Returns a dict of (name, bytes, mime) triples for a status update upload."""
    return {
        "face_file": ("front_face.jpg", io.BytesIO(FAKE_JPEG), "image/jpeg"),
        "incision_file": ("incision_day1.jpg", io.BytesIO(FAKE_JPEG), "image/jpeg"),
        "video_file": ("gait_walk.mp4", io.BytesIO(FAKE_MP4), "video/mp4"),
    }
