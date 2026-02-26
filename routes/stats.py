from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, jsonify
from models import db, Conversation
from routes.auth import login_required

stats_bp = Blueprint("stats", __name__)


@stats_bp.route("/estadisticas")
@login_required
def index():
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)
    thirty_days_ago = today_start - timedelta(days=30)

    # All KPIs + unique users in ONE query
    row = db.session.query(
        db.func.count(Conversation.id).filter(Conversation.created_at >= today_start),
        db.func.count(Conversation.id).filter(Conversation.created_at >= week_start),
        db.func.count(Conversation.id).filter(Conversation.created_at >= month_start),
        db.func.count(Conversation.id),
        db.func.count(db.func.distinct(Conversation.user_id)),
    ).filter(Conversation.role == "user").one()

    messages_today, messages_week, messages_month, messages_total, unique_users = row

    # Daily messages — 1 query with GROUP BY date
    daily_rows = (
        db.session.query(
            db.func.date(Conversation.created_at).label("day"),
            db.func.count(Conversation.id),
        )
        .filter(Conversation.role == "user", Conversation.created_at >= thirty_days_ago)
        .group_by("day")
        .all()
    )
    daily_map = {str(r[0]): r[1] for r in daily_rows}
    daily_messages = []
    for i in range(30):
        day = thirty_days_ago + timedelta(days=i)
        key = day.strftime("%Y-%m-%d")
        daily_messages.append({"date": day.strftime("%d/%m"), "count": daily_map.get(key, 0)})

    # Hourly messages — 1 query with GROUP BY hour
    hourly_rows = (
        db.session.query(
            db.extract("hour", Conversation.created_at).label("h"),
            db.func.count(Conversation.id),
        )
        .filter(Conversation.role == "user")
        .group_by("h")
        .all()
    )
    hourly_map = {int(r[0]): r[1] for r in hourly_rows}
    hourly_messages = [{"hour": f"{h:02d}:00", "count": hourly_map.get(h, 0)} for h in range(24)]

    # Top users — 1 query
    top_users = (
        db.session.query(
            Conversation.user_id,
            db.func.count(Conversation.id).label("count"),
        )
        .filter(Conversation.role == "user")
        .group_by(Conversation.user_id)
        .order_by(db.text("count DESC"))
        .limit(10)
        .all()
    )
    top_users_data = [{"name": u[0], "count": u[1]} for u in top_users]

    return render_template(
        "estadisticas.html",
        messages_today=messages_today,
        messages_week=messages_week,
        messages_month=messages_month,
        messages_total=messages_total,
        unique_users=unique_users,
        daily_messages=daily_messages,
        hourly_messages=hourly_messages,
        top_users_data=top_users_data,
    )


@stats_bp.route("/estadisticas/insights")
@login_required
def insights():
    """Return AI-generated insights from conversation data."""
    try:
        from services.ai_insights import get_insights
        data = get_insights()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
