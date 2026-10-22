"""
app/core/database.py
--------------------
SQLAlchemy engine, session factory, and declarative base.
All other modules import from here — never from the root database.py.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

db_url = settings.DATABASE_URL
# Render / Supabase sometimes provide "postgres://" which SQLAlchemy 2.x expects as "postgresql://"
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

is_sqlite = db_url.startswith("sqlite")

connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    db_url,
    connect_args=connect_args,
)

# SQLite ignores foreign key constraints unless explicitly told to enforce them
if is_sqlite:
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
