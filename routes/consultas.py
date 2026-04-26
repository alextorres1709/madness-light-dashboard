from flask import Blueprint, render_template, request
from models import Conversation
from routes.auth import login_required
from datetime import datetime, timezone

consultas_bp = Blueprint("consultas", __name__)


def _time_ago(dt, now):
    if not dt:
        return ""
    diff = (now - dt) if dt.tzinfo else (now.replace(tzinfo=None) - dt)
    s = int(diff.total_seconds())
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m"
    if s < 86400:
        return f"{s // 3600}h"
    return f"{diff.days}d"


@consultas_bp.route("/consultas")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    per_page = 20
    now = datetime.now(timezone.utc)

    # 1 query: total count
    total = Conversation.query.filter_by(role="user").count()
    total_pages = (total + per_page - 1) // per_page

    # 1 query: user messages for this page
    user_msgs = (
        Conversation.query.filter_by(role="user")
        .order_by(Conversation.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    if not user_msgs:
        return render_template("consultas.html", pairs=[], page=page,
                               total_pages=total_pages, total=total)

    # 1 query: get the first bot reply after each user message
    # Uses a lateral/correlated subquery via raw SQL for efficiency
    # Fallback: fetch all assistant messages for these users in the time window
    user_ids = list({m.user_id for m in user_msgs})
    min_ts = min(m.created_at for m in user_msgs if m.created_at)

    bot_msgs = (
        Conversation.query
        .filter(
            Conversation.role == "assistant",
            Conversation.user_id.in_(user_ids),
            Conversation.created_at >= min_ts,
        )
        .order_by(Conversation.created_at.asc())
        .all()
    )

    # Index bot replies by user_id for O(1) lookup
    # Keep the first bot reply after each user message
    bot_by_user: dict[str, list] = {}
    for b in bot_msgs:
        bot_by_user.setdefault(b.user_id, []).append(b)

    pairs = []
    for msg in user_msgs:
        # Find first bot reply after this message
        answer = None
        for b in bot_by_user.get(msg.user_id, []):
            b_ts = b.created_at
            m_ts = msg.created_at
            if b_ts and m_ts:
                b_cmp = b_ts if b_ts.tzinfo else b_ts
                m_cmp = m_ts if m_ts.tzinfo else m_ts
                try:
                    if b_cmp > m_cmp:
                        answer = b.content
                        break
                except TypeError:
                    pass

        pairs.append({
            "user_id": msg.user_id,
            "question": msg.content,
            "answer": answer,
            "ago": _time_ago(msg.created_at, now),
            "ts": msg.created_at.strftime("%d/%m %H:%M") if msg.created_at else "",
        })

    return render_template(
        "consultas.html",
        pairs=pairs,
        page=page,
        total_pages=total_pages,
        total=total,
    )
