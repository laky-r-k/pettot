from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
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

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", foreign_keys=[owner_id], back_populates="subscriptions_as_owner")
    doctor = relationship("User", foreign_keys=[doctor_id], back_populates="subscriptions_as_doctor")