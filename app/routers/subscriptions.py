"""
app/routers/subscriptions.py
-----------------------------
Owner↔Doctor subscription management endpoints.
Business logic delegated to subscription_service.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.models.db import User
from app.schemas.api import (
    SubscriptionCreate,
    SubscriptionResponse,
    OwnerDoctorSubscriptionResponse,
)
from app.services import subscription_service
from app.services.subscription_service import DuplicateSubscriptionError, InvalidDoctorError

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.post("/", response_model=SubscriptionResponse)
def create_subscription(
    sub: SubscriptionCreate,
    owner: User = Depends(require_role("owner")),
    db: Session = Depends(get_db),
):
    try:
        return subscription_service.create_subscription(db, owner.id, sub.doctor_id)
    except InvalidDoctorError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DuplicateSubscriptionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me/", response_model=list[OwnerDoctorSubscriptionResponse])
def list_my_doctors(
    owner: User = Depends(require_role("owner")),
    db: Session = Depends(get_db),
):
    """Lists all veterinarians the authenticated pet owner is currently linked with."""
    subs = subscription_service.list_subscriptions_for_owner(db, owner.id)
    results = []
    for s in subs:
        doc = s.doctor
        results.append({
            "subscription_id": s.id,
            "doctor_id": doc.id,
            "doctor_name": doc.name,
            "doctor_email": doc.email,
            "doctor_username": doc.username,
            "license_number": doc.license_number,
            "created_at": s.created_at or s.id,
        })
    return results


@router.delete("/{subscription_id}")
def delete_subscription(
    subscription_id: int,
    owner: User = Depends(require_role("owner")),
    db: Session = Depends(get_db),
):
    """Allows an owner to unsubscribe / unlink from a veterinarian."""
    deleted = subscription_service.delete_subscription(db, subscription_id, owner.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return {"message": "Successfully unsubscribed from veterinarian"}
