from flask import Blueprint, render_template, request
from models import db, ActivityLog
from routes.auth import admin_required

activity_bp = Blueprint("activity", __name__)


@activity_bp.route("/actividad")
@admin_required
def index():
    page = request.args.get("page", 1, type=int)
    per_page = 50
    action_filter = request.args.get("action", "").strip()
    target_filter = request.args.get("target_type", "").strip()

    query = ActivityLog.query

    if action_filter:
        query = query.filter_by(action=action_filter)
    if target_filter:
        query = query.filter_by(target_type=target_filter)

    total = query.count()
    logs = (
        query.order_by(ActivityLog.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "actividad.html",
        logs=logs,
        page=page,
        total_pages=total_pages,
        action_filter=action_filter,
        target_filter=target_filter,
    )
