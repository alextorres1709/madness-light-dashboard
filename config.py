import os
from dotenv import load_dotenv

load_dotenv()

# Vercel has a read-only filesystem except /tmp
_is_vercel = os.getenv("VERCEL", "")
_default_db = "sqlite:////tmp/madness.db" if _is_vercel else "sqlite:///madness.db"

_db_url = os.getenv("DATABASE_URL", _default_db)
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif _db_url.startswith("postgresql://") and not _db_url.startswith("postgresql+psycopg://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+psycopg://", 1)


from sqlalchemy.pool import NullPool

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": NullPool,
        "pool_pre_ping": True,
        "connect_args": {
            "prepare_threshold": None,
            "connect_timeout": 8,
        },
    } if "postgresql" in _db_url else {}
    SEND_FILE_MAX_AGE_DEFAULT = 3600  # 1h cache for static files
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@madnesslight.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    API_KEY = os.getenv("API_KEY", "ml-api-key-change-me")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
    WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "")
    WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
