import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///madness.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@madnesslight.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    API_KEY = os.getenv("API_KEY", "ml-api-key-change-me")
