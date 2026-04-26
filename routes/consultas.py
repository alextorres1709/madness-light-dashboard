from flask import Blueprint, render_template, request
from models import db, Conversation
from routes.auth import login_required
from datetime import datetime, timezone

consultas_bp = Blueprint("consultas", __name__)


@consultas_bp.route("/consultas")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    per_page = 20

    # Fetch user messages with their paired bot responses
    # Get user messages ordered newest first
    user_msgs = (
        Conversation.query.filter_by(role="user")
        .order_by(Conversation.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    total = Conversation.query.filter_by(role="user").count()
    total_pages = (total + per_page - 1) // per_page

    # For each user message, find the next bot response
    pairs = []
    for msg in user_msgs:
        bot_reply = (
            Conversation.query.filter(
                Conversation.user_id == msg.user_id,
                Conversation.role == "assistant",
                Conversation.created_at > msg.created_at,
            )
            .order_by(Conversation.created_at.asc())
            .first()
        )
        now = datetime.now(timezone.utc)
        if msg.created_at and msg.created_at.tzinfo:
            diff = now - msg.created_at
        elif msg.created_at:
            diff = now.replace(tzinfo=None) - msg.created_at
        else:
            diff = None

        ago = ""
        if diff is not None:
            s = int(diff.total_seconds())
            if s < 60:
                ago = f"{s}s"
            elif s < 3600:
                ago = f"{s // 60}m"
            elif s < 86400:
                ago = f"{s // 3600}h"
            else:
                ago = f"{diff.days}d"

        pairs.append({
            "user_id": msg.user_id,
            "question": msg.content,
            "answer": bot_reply.content if bot_reply else None,
            "ago": ago,
            "ts": msg.created_at.strftime("%d/%m %H:%M") if msg.created_at else "",
        })

    return render_template(
        "consultas.html",
        pairs=pairs,
        page=page,
        total_pages=total_pages,
        total=total,
    )
