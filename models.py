from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# Known venues (salas) for Madness Light
VENUES = [
    "Lab (Madrid)",
    "Shôko Madrid",
    "Jowke (Madrid)",
    "Nazca (Madrid)",
    "Tiffany's (Madrid)",
]

# Event themes
THEMES = [
    "Normal",
    "Halloween",
    "Carnaval",
    "Hawaiana",
    "Neón",
    "Reggaeton",
    "Años 80/90",
    "Otra",
]


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, nullable=False, index=True)
    venue = db.Column(db.String(300), nullable=False)  # Sala
    theme = db.Column(db.String(100), default="Normal")  # Temática
    description = db.Column(db.Text, default="")
    dj_info = db.Column(db.String(300), default="")  # DJs / animación
    capacity = db.Column(db.Integer, default=0)
    entry_price = db.Column(db.String(100), default="")  # Precio referencia
    entry_link = db.Column(db.String(500), default="")  # Link app Elite Events
    image_url = db.Column(db.String(500), default="")
    active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "date": self.date.isoformat() if self.date else None,
            "venue": self.venue,
            "theme": self.theme,
            "description": self.description,
            "dj_info": self.dj_info,
            "capacity": self.capacity,
            "entry_price": self.entry_price,
            "entry_link": self.entry_link,
            "image_url": self.image_url,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False, index=True)
    user_name = db.Column(db.String(200), default="Unknown")
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, default="")
    platform = db.Column(db.String(50), default="telegram")
    timestamp = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "message": self.message,
            "response": self.response,
            "platform": self.platform,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class CompanyInfo(db.Model):
    __tablename__ = "company_info"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), default="Madness Light")
    description = db.Column(
        db.Text,
        default="Empresa de fiestas y eventos en Madrid",
    )
    phone = db.Column(db.String(50), default="")
    email = db.Column(db.String(200), default="")
    address = db.Column(db.String(300), default="")
    hours = db.Column(db.String(200), default="")
    extra_info = db.Column(db.Text, default="")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "hours": self.hours,
            "extra_info": self.extra_info,
        }


class Conversation(db.Model):
    """Bot chat history — shared with Telegram bot (n8n)."""

    __tablename__ = "conversations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, index=True)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

