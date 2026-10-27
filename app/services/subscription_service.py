"""
app/services/subscription_service.py
-------------------------------------
Pure business logic for subscriptions.
No FastAPI imports — testable with just a DB session.
"""
from sqlalchemy.orm import Session

from app.models.db import Subscription, User


class DuplicateSubscriptionError(Exception):
    """Raised when an owner tries to subscribe to a doctor they already follow."""
    pass


class InvalidDoctorError(Exception):
    """Raised when the target user is not a doctor."""
    pass


def get_subscription(db: Session, subscription_id: int, owner_id: int) -> Subscription | None:
    """Fetch a subscription by ID, scoped to the given owner."""
    return (
        db.query(Subscription)
        .filter(Subscription.id == subscription_id, Subscription.owner_id == owner_id)
        .first()
    )


def list_subscriptions_for_owner(db: Session, owner_id: int) -> list[Subscription]:
    """Return all subscriptions for an owner, with doctor relationship pre-loaded."""
    return db.query(Subscription).filter(Subscription.owner_id == owner_id).all()


def create_subscription(db: Session, owner_id: int, doctor_id: int) -> Subscription:
    """
    Create a new owner→doctor subscription.
    Raises DuplicateSubscriptionError if already subscribed.
    Raises InvalidDoctorError if doctor_id doesn't belong to a doctor-role user.
    """
    doctor = db.query(User).filter(User.id == doctor_id).first()
    if not doctor or doctor.role != "doctor":
        raise InvalidDoctorError(f"User {doctor_id} is not a registered veterinarian.")

    existing = (
        db.query(Subscription)
        .filter(Subscription.owner_id == owner_id, Subscription.doctor_id == doctor_id)
        .first()
    )
    if existing:
        raise DuplicateSubscriptionError(
            f"You are already subscribed to Dr. {doctor.name}."
        )

    sub = Subscription(owner_id=owner_id, doctor_id=doctor_id)
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def delete_subscription(db: Session, subscription_id: int, owner_id: int) -> bool:
    """
    Delete a subscription owned by owner_id.
    Returns True if deleted, False if not found.
    """
    sub = get_subscription(db, subscription_id, owner_id)
    if not sub:
        return False
    db.delete(sub)
    db.commit()
    return True
