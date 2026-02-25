from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template
from models import db, Event, Message
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

    # KPI counts
    messages_today = Message.query.filter(Message.timestamp >= today_start).count()
    messages_week = Message.query.filter(Message.timestamp >= week_start).count()
    messages_month = Message.query.filter(Message.timestamp >= month_start).count()
    messages_total = Message.query.count()
    active_events = Event.query.filter_by(active=True).count()

    # Recent messages
    recent_messages = (
        Message.query.order_by(Message.timestamp.desc()).limit(20).all()
    )

    # Messages per day (last 30 days) for chart
    thirty_days_ago = today_start - timedelta(days=30)
    daily_messages = []
    for i in range(30):
        day = thirty_days_ago + timedelta(days=i)
        next_day = day + timedelta(days=1)
        count = Message.query.filter(
            Message.timestamp >= day, Message.timestamp < next_day
        ).count()
        daily_messages.append(
            {"date": day.strftime("%d/%m"), "count": count}
        )

    # Messages per hour for chart
    hourly_messages = []
    for h in range(24):
        count = Message.query.filter(
            db.extract("hour", Message.timestamp) == h
        ).count()
        hourly_messages.append({"hour": f"{h:02d}:00", "count": count})

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
