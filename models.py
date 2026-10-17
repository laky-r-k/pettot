from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone
from sqlalchemy import DateTime, Text

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    license_number = Column(String, nullable=True)

    pets = relationship("Pet", back_populates="owner")
    subscriptions_as_owner = relationship("Subscription", foreign_keys="Subscription.owner_id", back_populates="owner")
    subscriptions_as_doctor = relationship("Subscription", foreign_keys="Subscription.doctor_id", back_populates="doctor")


class Pet(Base):
    __tablename__ = "pets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    species = Column(String)
    age = Column(Integer)
    is_adopted = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="pets")
    updates = relationship("StatusUpdate", back_populates="pet", cascade="all, delete-orphan")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", foreign_keys=[owner_id], back_populates="subscriptions_as_owner")
    doctor = relationship("User", foreign_keys=[doctor_id], back_populates="subscriptions_as_doctor")

class StatusUpdate(Base):
    __tablename__ = "status_updates"

    id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False, index=True)
    notes = Column(Text, nullable=False, default="")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    pet = relationship("Pet", back_populates="updates")
    media = relationship(
        "MediaFile", back_populates="status_update", cascade="all, delete-orphan"
    )


class MediaFile(Base):
    __tablename__ = "media_files"

    id = Column(Integer, primary_key=True, index=True)
    status_update_id = Column(Integer, ForeignKey("status_updates.id"), nullable=False, index=True)
    path = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    original_name = Column(String, nullable=True)

    status_update = relationship("StatusUpdate", back_populates="media")