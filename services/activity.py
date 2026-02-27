from flask import g
from models import db, ActivityLog


def log_activity(action, target_type, target_id=None, details=""):
    """Record an action in the activity log. Auto-reads g.user for user_id."""
    user = g.get("user")
    entry = ActivityLog(
        user_id=user.id if user else None,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )
    db.session.add(entry)
