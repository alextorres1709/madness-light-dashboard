from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template
from models import db, Event, Conversation
from routes.auth import login_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)
    thirty_days_ago = today_start - timedelta(days=30)

    # All KPIs in ONE query
    row = db.session.query(
        db.func.count(Conversation.id).filter(Conversation.created_at >= today_start),
        db.func.count(Conversation.id).filter(Conversation.created_at >= week_start),
        db.func.count(Conversation.id).filter(Conversation.created_at >= month_start),
        db.func.count(Conversation.id),
    ).filter(Conversation.role == "user").one()

    messages_today, messages_week, messages_month, messages_total = row
    active_events = Event.query.filter_by(active=True).count()

    # Recent conversations (last 20 user messages)
    recent_messages = (
        Conversation.query.filter_by(role="user")
        .order_by(Conversation.created_at.desc())
        .limit(20)
        .all()
    )

    # Daily messages — 1 query with GROUP BY
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

    # Hourly messages — 1 query with GROUP BY
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

    # Upcoming active events (next 5)
    upcoming_events = (
        Event.query.filter(Event.active == True, Event.date >= now)
        .order_by(Event.date.asc())
        .limit(5)
        .all()
    )
    total_events = Event.query.count()

    return render_template(
        "dashboard.html",
        messages_today=messages_today,
        messages_week=messages_week,
        messages_month=messages_month,
        messages_total=messages_total,
        active_events=active_events,
        total_events=total_events,
        upcoming_events=upcoming_events,
        recent_messages=recent_messages,
        daily_messages=daily_messages,
        hourly_messages=hourly_messages,
    )
