import csv
import io
from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, jsonify, Response
from models import db, Conversation, Event
from routes.auth import login_required

stats_bp = Blueprint("stats", __name__)


@stats_bp.route("/estadisticas")
@login_required
def index():
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)
    prev_month_start = (month_start - timedelta(days=1)).replace(day=1)
    thirty_days_ago = today_start - timedelta(days=30)
    eight_weeks_ago = today_start - timedelta(weeks=8)

    # ── KPIs ─────────────────────────────────────────────
    row = db.session.query(
        db.func.count(db.func.distinct(Conversation.user_id)).filter(
            Conversation.created_at >= month_start
        ),
        db.func.count(db.func.distinct(Conversation.user_id)).filter(
            Conversation.created_at >= prev_month_start,
            Conversation.created_at < month_start,
        ),
        db.func.count(db.func.distinct(Conversation.user_id)),
        db.func.count(Conversation.id),
    ).filter(Conversation.role == "user").one()

    users_this_month, users_prev_month, total_users, total_messages = row

    # Avg messages per user
    avg_per_user = round(total_messages / total_users, 1) if total_users else 0

    # User growth % (month over month)
    if users_prev_month > 0:
        user_growth = round(
            ((users_this_month - users_prev_month) / users_prev_month) * 100
        )
    else:
        user_growth = 100 if users_this_month > 0 else 0

    # Peak hour
    peak_row = (
        db.session.query(
            db.extract("hour", Conversation.created_at).label("h"),
            db.func.count(Conversation.id).label("c"),
        )
        .filter(Conversation.role == "user")
        .group_by("h")
        .order_by(db.text("c DESC"))
        .first()
    )
    peak_hour = f"{int(peak_row[0]):02d}:00" if peak_row else "--:--"

    # Events stats
    total_events = Event.query.count()
    upcoming_events = Event.query.filter(
        Event.active == True, Event.date >= now
    ).count()

    # ── Crecimiento de usuarios (últimas 8 semanas) ──────
    weekly_users_rows = (
        db.session.query(
            db.func.date(Conversation.created_at).label("day"),
            Conversation.user_id,
        )
        .filter(Conversation.role == "user", Conversation.created_at >= eight_weeks_ago)
        .distinct()
        .all()
    )
    # Group by ISO week
    weekly_map = {}
    for r in weekly_users_rows:
        d = r[0] if isinstance(r[0], datetime) else datetime.strptime(str(r[0]), "%Y-%m-%d")
        week_key = d.strftime("%Y-W%W")
        weekly_map.setdefault(week_key, set()).add(r[1])

    weekly_users = []
    for i in range(8):
        d = eight_weeks_ago + timedelta(weeks=i)
        key = d.strftime("%Y-W%W")
        label = d.strftime("%d/%m")
        weekly_users.append({"week": label, "count": len(weekly_map.get(key, set()))})

    # ── Actividad por hora ───────────────────────────────
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
    hourly_messages = [
        {"hour": f"{h:02d}:00", "count": hourly_map.get(h, 0)} for h in range(24)
    ]

    # ── Eventos por sala ─────────────────────────────────
    venue_rows = (
        db.session.query(Event.venue, db.func.count(Event.id))
        .group_by(Event.venue)
        .order_by(db.func.count(Event.id).desc())
        .all()
    )
    venues_data = [{"venue": r[0], "count": r[1]} for r in venue_rows]

    # ── Eventos por temática ─────────────────────────────
    theme_rows = (
        db.session.query(Event.theme, db.func.count(Event.id))
        .group_by(Event.theme)
        .order_by(db.func.count(Event.id).desc())
        .all()
    )
    themes_data = [{"theme": r[0], "count": r[1]} for r in theme_rows]

    # ── Usuarios más activos ─────────────────────────────
    top_users = (
        db.session.query(
            Conversation.user_id,
            db.func.count(Conversation.id).label("msg_count"),
            db.func.count(db.func.distinct(db.func.date(Conversation.created_at))).label("days_active"),
        )
        .filter(Conversation.role == "user")
        .group_by(Conversation.user_id)
        .order_by(db.text("msg_count DESC"))
        .limit(10)
        .all()
    )
    top_users_data = [
        {"name": u[0], "messages": u[1], "days": u[2]} for u in top_users
    ]

    # ── Próximos eventos ─────────────────────────────────
    next_events = (
        Event.query.filter(Event.active == True, Event.date >= now)
        .order_by(Event.date.asc())
        .limit(5)
        .all()
    )

    return render_template(
        "estadisticas.html",
        # KPIs
        users_this_month=users_this_month,
        user_growth=user_growth,
        total_users=total_users,
        avg_per_user=avg_per_user,
        peak_hour=peak_hour,
        total_events=total_events,
        upcoming_events=upcoming_events,
        total_messages=total_messages,
        # Charts
        weekly_users=weekly_users,
        hourly_messages=hourly_messages,
        venues_data=venues_data,
        themes_data=themes_data,
        # Tables
        top_users_data=top_users_data,
        next_events=next_events,
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


@stats_bp.route("/estadisticas/export/csv")
@login_required
def export_csv():
    users_data = (
        db.session.query(
            Conversation.user_id,
            db.func.count(Conversation.id).label("msg_count"),
            db.func.min(Conversation.created_at).label("first_seen"),
            db.func.max(Conversation.created_at).label("last_seen"),
            db.func.count(db.func.distinct(db.func.date(Conversation.created_at))).label("days_active"),
        )
        .filter(Conversation.role == "user")
        .group_by(Conversation.user_id)
        .order_by(db.text("msg_count DESC"))
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["User ID", "Mensajes", "Primera Vez", "Ultimo Mensaje", "Dias Activo"])

    for u in users_data:
        writer.writerow([
            u.user_id,
            u.msg_count,
            u.first_seen.strftime("%Y-%m-%d %H:%M") if u.first_seen else "",
            u.last_seen.strftime("%Y-%m-%d %H:%M") if u.last_seen else "",
            u.days_active,
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=estadisticas_usuarios_export.csv"},
    )
