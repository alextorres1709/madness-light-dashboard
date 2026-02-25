from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template
from models import db, Message
from routes.auth import login_required

stats_bp = Blueprint("stats", __name__)


@stats_bp.route("/estadisticas")
@login_required
def index():
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)

    # KPI counts
    messages_today = Message.query.filter(Message.timestamp >= today_start).count()
    messages_week = Message.query.filter(Message.timestamp >= week_start).count()
    messages_month = Message.query.filter(Message.timestamp >= month_start).count()
    messages_total = Message.query.count()

    # Unique users
    unique_users = db.session.query(
        db.func.count(db.func.distinct(Message.user_name))
    ).scalar() or 0

    # Messages per day (last 30 days)
    thirty_days_ago = today_start - timedelta(days=30)
    daily_messages = []
    for i in range(30):
        day = thirty_days_ago + timedelta(days=i)
        next_day = day + timedelta(days=1)
        count = Message.query.filter(
            Message.timestamp >= day, Message.timestamp < next_day
        ).count()
        daily_messages.append({"date": day.strftime("%d/%m"), "count": count})

    # Messages per hour
    hourly_messages = []
    for h in range(24):
        count = Message.query.filter(
            db.extract("hour", Message.timestamp) == h
        ).count()
        hourly_messages.append({"hour": f"{h:02d}:00", "count": count})

    # Platform breakdown
    platforms = db.session.query(
        Message.platform,
        db.func.count(Message.id)
    ).group_by(Message.platform).all()
    platform_data = [{"platform": p[0] or "Desconocido", "count": p[1]} for p in platforms]

    # Top users
    top_users = db.session.query(
        Message.user_name,
        db.func.count(Message.id).label("count")
    ).group_by(Message.user_name).order_by(db.text("count DESC")).limit(10).all()
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
        platform_data=platform_data,
        top_users_data=top_users_data,
    )
