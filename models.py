from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
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
    status_updates = relationship(
        "StatusUpdate", 
        back_populates="pet", 
        cascade="all, delete-orphan", 
        order_by="StatusUpdate.created_at.desc()"
    )


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
    day_number = Column(Integer, nullable=False, default=1)
    update_date = Column(Date, nullable=False, default=date.today)
    notes = Column(String, nullable=True)
    
    # State flag for future background processing jobs
    processing_status = Column(String, default="pending", index=True)  # pending | processing | completed | failed
    analysis_results = Column(String, nullable=True)  # Nullable JSON string for future AI findings
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    pet = relationship("Pet", back_populates="status_updates")
    media_files = relationship(
        "MediaFile", 
        back_populates="status_update", 
        cascade="all, delete-orphan",
        order_by="MediaFile.id.asc()"
    )


class MediaFile(Base):
    __tablename__ = "media_files"

    id = Column(Integer, primary_key=True, index=True)
    status_update_id = Column(Integer, ForeignKey("status_updates.id"), nullable=False, index=True)
    
    media_type = Column(String, nullable=False)        # "face_image" | "incision_image" | "walking_video"
    file_path = Column(String, nullable=False)         # Relative storage path: "pets/{pet_id}/{uuid}.ext"
    original_filename = Column(String, nullable=False) # e.g. "front_face.jpg"
    content_type = Column(String, nullable=False)      # e.g. "image/jpeg", "video/mp4"
    file_size_bytes = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)    # Video duration (validated <= 10.0s)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    status_update = relationship("StatusUpdate", back_populates="media_files")