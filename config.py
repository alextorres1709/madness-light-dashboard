import os
from dotenv import load_dotenv

load_dotenv()

# Vercel has a read-only filesystem except /tmp
_is_vercel = os.getenv("VERCEL", "")
_default_db = "sqlite:////tmp/madness.db" if _is_vercel else "sqlite:///madness.db"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", _default_db)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@madnesslight.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    API_KEY = os.getenv("API_KEY", "ml-api-key-change-me")
