"""
tests/unit/test_subscription_service.py
----------------------------------------
Unit tests for subscription_service.py.
These tests run against an in-memory DB with no HTTP layer — millisecond speed.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.db import User, Subscription
from app.services.subscription_service import (
    create_subscription,
    delete_subscription,
    list_subscriptions_for_owner,
    DuplicateSubscriptionError,
    InvalidDoctorError,
)
import app.models.db  # noqa: F401


# ── Isolated DB for unit tests ─────────────────────────────────────────────────

@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def owner(db):
    u = User(firebase_uid="owner_uid", username="owner1", name="Alice", email="alice@test.com", role="owner")
    db.add(u); db.commit(); db.refresh(u)
    return u


@pytest.fixture
def doctor(db):
    u = User(firebase_uid="doctor_uid", username="drBob", name="Dr. Bob", email="bob@test.com", role="doctor", license_number="VET-001")
    db.add(u); db.commit(); db.refresh(u)
    return u


@pytest.fixture
def non_doctor(db):
    u = User(firebase_uid="nd_uid", username="notadoc", name="Not Doc", email="notdoc@test.com", role="owner")
    db.add(u); db.commit(); db.refresh(u)
    return u


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_create_subscription_success(db, owner, doctor):
    sub = create_subscription(db, owner_id=owner.id, doctor_id=doctor.id)
    assert sub.id is not None
    assert sub.owner_id == owner.id
    assert sub.doctor_id == doctor.id


def test_create_subscription_duplicate_raises(db, owner, doctor):
    create_subscription(db, owner_id=owner.id, doctor_id=doctor.id)
    with pytest.raises(DuplicateSubscriptionError):
        create_subscription(db, owner_id=owner.id, doctor_id=doctor.id)


def test_create_subscription_invalid_doctor_raises(db, owner, non_doctor):
    with pytest.raises(InvalidDoctorError):
        create_subscription(db, owner_id=owner.id, doctor_id=non_doctor.id)


def test_create_subscription_nonexistent_user_raises(db, owner):
    with pytest.raises(InvalidDoctorError):
        create_subscription(db, owner_id=owner.id, doctor_id=9999)


def test_list_subscriptions_empty(db, owner):
    result = list_subscriptions_for_owner(db, owner.id)
    assert result == []


def test_list_subscriptions_returns_all(db, owner, doctor):
    create_subscription(db, owner_id=owner.id, doctor_id=doctor.id)
    result = list_subscriptions_for_owner(db, owner.id)
    assert len(result) == 1
    assert result[0].doctor_id == doctor.id


def test_delete_subscription_success(db, owner, doctor):
    sub = create_subscription(db, owner_id=owner.id, doctor_id=doctor.id)
    deleted = delete_subscription(db, sub.id, owner.id)
    assert deleted is True
    assert list_subscriptions_for_owner(db, owner.id) == []


def test_delete_subscription_not_found_returns_false(db, owner):
    deleted = delete_subscription(db, subscription_id=9999, owner_id=owner.id)
    assert deleted is False


def test_delete_subscription_wrong_owner_returns_false(db, owner, doctor):
    sub = create_subscription(db, owner_id=owner.id, doctor_id=doctor.id)
    # Try to delete using a different owner_id
    deleted = delete_subscription(db, sub.id, owner_id=9999)
    assert deleted is False
