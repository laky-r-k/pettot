"""
app/core/config.py
------------------
Central settings loaded from environment variables / .env file.
Import `settings` everywhere instead of reading os.getenv() directly.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")

    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = os.getenv(
        "FIREBASE_CREDENTIALS_PATH", "./firebase-credentials.json"
    )

    # File storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")

    # Supabase (Optional in local dev, used in production for Postgres & Storage)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_BUCKET: str = os.getenv("SUPABASE_BUCKET", "media")

    # Firebase raw credentials JSON string (for cloud hosting without file mounts)
    FIREBASE_CREDENTIALS_JSON: str = os.getenv("FIREBASE_CREDENTIALS_JSON", "")


settings = Settings()
