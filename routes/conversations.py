from datetime import datetime
from flask import Blueprint, render_template, request
from models import db, Conversation
from routes.auth import login_required

conversations_bp = Blueprint("conversations", __name__)


@conversations_bp.route("/conversaciones")
@login_required
def index():
    search = request.args.get("search", "").strip()

    base_query = (
        db.session.query(
            Conversation.user_id,
            db.func.count(Conversation.id).label("msg_count"),
            db.func.max(Conversation.created_at).label("last_active"),
            db.func.min(Conversation.created_at).label("first_seen"),
        )
        .filter(Conversation.role == "user")
        .group_by(Conversation.user_id)
    )

    if search:
        user_ids_with_content = (
            db.session.query(Conversation.user_id)
            .filter(
                Conversation.role == "user",
                Conversation.content.ilike(f"%{search}%"),
            )
            .distinct()
            .subquery()
        )
        base_query = base_query.filter(
            db.or_(
                Conversation.user_id.ilike(f"%{search}%"),
                Conversation.user_id.in_(db.select(user_ids_with_content.c.user_id)),
            )
        )

    users = base_query.order_by(db.text("last_active DESC")).all()

    return render_template("conversaciones.html", users=users, search=search)


@conversations_bp.route("/conversaciones/<user_id>")
@login_required
def detail(user_id):
    date_from = request.args.get("from", "").strip()
    date_to = request.args.get("to", "").strip()

    query = Conversation.query.filter_by(user_id=user_id)

    if date_from:
        try:
            query = query.filter(Conversation.created_at >= datetime.fromisoformat(date_from))
        except ValueError:
            pass
    if date_to:
        try:
            query = query.filter(Conversation.created_at <= datetime.fromisoformat(date_to + "T23:59:59"))
        except ValueError:
            pass

    messages = query.order_by(Conversation.created_at.asc()).all()
    msg_count = sum(1 for m in messages if m.role == "user")

    return render_template(
        "conversacion_detalle.html",
        user_id=user_id,
        messages=messages,
        msg_count=msg_count,
        date_from=date_from,
        date_to=date_to,
    )
