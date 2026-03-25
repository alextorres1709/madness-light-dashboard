from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ── Role constants ────────────────────────────────────────
ROLE_ADMIN = "admin"
ROLE_EDITOR = "editor"
ROLE_VIEWER = "viewer"
ROLES = [ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER]


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(200), default="")
    role = db.Column(db.String(20), nullable=False, default=ROLE_VIEWER)
    active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def can_manage_events(self):
        return self.role in (ROLE_ADMIN, ROLE_EDITOR)

    @property
    def can_manage_settings(self):
        return self.role == ROLE_ADMIN

    @property
    def can_manage_users(self):
        return self.role == ROLE_ADMIN

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


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


class Venue(db.Model):
    """Managed venue (sala) for events."""
    __tablename__ = "venues"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    address = db.Column(db.String(300), default="")
    capacity = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(500), default="")
    active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "capacity": self.capacity,
            "image_url": self.image_url,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
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


class Client(db.Model):
    """Client registered via Telegram bot."""
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(50), default="")
    dob = db.Column(db.String(20), default="")  # dd/mm/yyyy
    chat_id = db.Column(db.String(100), nullable=False, unique=True, index=True)
    events_attended = db.Column(db.Integer, default=0)
    last_seen = db.Column(db.String(20), default="")
    status = db.Column(db.String(20), default="active", index=True)
    birthday_greeted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "dob": self.dob,
            "chat_id": self.chat_id,
            "events_attended": self.events_attended,
            "last_seen": self.last_seen,
            "status": self.status,
            "birthday_greeted_at": self.birthday_greeted_at.isoformat() if self.birthday_greeted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ActivityLog(db.Model):
    """Audit trail for admin-visible actions."""
    __tablename__ = "activity_log"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    action = db.Column(db.String(50), nullable=False, index=True)
    target_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, default="")
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    user = db.relationship("User", backref=db.backref("activity_logs", lazy="dynamic"))


# Notification categories
NOTIF_EVENT = "event"
NOTIF_CLIENT = "client"
NOTIF_BIRTHDAY = "birthday"
NOTIF_BROADCAST = "broadcast"
NOTIF_SYSTEM = "system"


class Notification(db.Model):
    """Mac-style notifications for the dashboard."""
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(30), nullable=False, default=NOTIF_SYSTEM, index=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, default="")
    icon = db.Column(db.String(30), default="info")  # info, party, user, heart, send
    read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "title": self.title,
            "body": self.body,
            "icon": self.icon,
            "read": self.read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# Reminder interval presets (minutes)
REMINDER_CHOICES = [
    (0, "Sin recordatorio"),
    (30, "Cada 30 min"),
    (60, "Cada hora"),
    (120, "Cada 2 horas"),
    (240, "Cada 4 horas"),
    (480, "Cada 8 horas"),
    (1440, "Cada dia"),
]


class Task(db.Model):
    """Dashboard task with configurable OS notification reminders."""
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, default="")
    done = db.Column(db.Boolean, default=False, index=True)
    reminder_minutes = db.Column(db.Integer, default=60)  # 0 = no reminder
    last_notified_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "done": self.done,
            "reminder_minutes": self.reminder_minutes,
            "last_notified_at": self.last_notified_at.isoformat() if self.last_notified_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

