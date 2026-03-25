from flask import Blueprint, jsonify, request
from models import db, Notification

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


@notifications_bp.route("/api", methods=["GET"])
def get_notifications():
    """Return recent notifications. Supports ?unread=true and ?since_id=N."""
    unread_only = request.args.get("unread", "false").lower() == "true"
    since_id = request.args.get("since_id", 0, type=int)
    limit = request.args.get("limit", 30, type=int)

    query = Notification.query
    if unread_only:
        query = query.filter_by(read=False)
    if since_id:
        query = query.filter(Notification.id > since_id)

    items = query.order_by(Notification.created_at.desc()).limit(limit).all()
    unread_count = Notification.query.filter_by(read=False).count()

    return jsonify({
        "notifications": [n.to_dict() for n in items],
        "unread_count": unread_count,
    })


@notifications_bp.route("/api/read/<int:notif_id>", methods=["POST"])
def mark_read(notif_id):
    """Mark a single notification as read."""
    n = Notification.query.get_or_404(notif_id)
    n.read = True
    db.session.commit()
    return jsonify({"ok": True})


@notifications_bp.route("/api/read-all", methods=["POST"])
def mark_all_read():
    """Mark all notifications as read."""
    Notification.query.filter_by(read=False).update({"read": True})
    db.session.commit()
    return jsonify({"ok": True})
