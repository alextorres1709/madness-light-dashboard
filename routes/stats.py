import csv
import io
from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, jsonify, Response
from sqlalchemy import or_
from models import db, Conversation, Event
from routes.auth import login_required

RRPP_KEYWORDS = [
    'rrpp', 'promotor', 'promotora', 'comision', 'comisiones',
    'ganar dinero', 'equipo', 'reclutar', 'relaciones publicas',
    'codigo', 'enlace', 'rangos', 'puntos', 'ser rrpp',
    'quiero ser', 'trabajar', 'sueldo', 'beneficios'
]

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

    # ── Tasa de retención ────────────────────────────────
    returning_users = (
        db.session.query(db.func.count())
        .select_from(
            db.session.query(Conversation.user_id)
            .filter(Conversation.role == "user")
            .group_by(Conversation.user_id)
            .having(db.func.count(Conversation.id) > 1)
            .subquery()
        )
    ).scalar() or 0
    retention_rate = round((returning_users / total_users) * 100, 1) if total_users else 0

    # ── Interés RRPP ───────────────────────────────────
    keyword_filters = [Conversation.content.ilike(f'%{kw}%') for kw in RRPP_KEYWORDS]
    rrpp_users = (
        db.session.query(db.func.count(db.func.distinct(Conversation.user_id)))
        .filter(Conversation.role == "user", or_(*keyword_filters))
        .scalar()
    ) or 0
    rrpp_interest_rate = round((rrpp_users / total_users) * 100, 1) if total_users else 0

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

    # First-seen date per user (all time, not limited to 8 weeks)
    first_seen_rows = (
        db.session.query(
            Conversation.user_id,
            db.func.min(db.func.date(Conversation.created_at)).label("first_seen"),
        )
        .filter(Conversation.role == "user")
        .group_by(Conversation.user_id)
        .all()
    )
    first_seen_map = {r[0]: str(r[1]) for r in first_seen_rows}

    weekly_users = []
    new_returning_weekly = []
    for i in range(8):
        d = eight_weeks_ago + timedelta(weeks=i)
        key = d.strftime("%Y-W%W")
        label = d.strftime("%d/%m")
        users_in_week = weekly_map.get(key, set())
        weekly_users.append({"week": label, "count": len(users_in_week)})

        w_start = d.strftime("%Y-%m-%d")
        w_end = (d + timedelta(weeks=1)).strftime("%Y-%m-%d")
        new_count = sum(
            1 for uid in users_in_week
            if first_seen_map.get(uid, "") >= w_start and first_seen_map.get(uid, "") < w_end
        )
        new_returning_weekly.append({
            "week": label,
            "new": new_count,
            "returning": len(users_in_week) - new_count,
        })

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

    # ── Menciones de eventos en conversaciones ────────
    event_mentions = []
    for event in next_events:
        if event.name:
            mention_count = (
                Conversation.query
                .filter(Conversation.role == "user",
                        Conversation.content.ilike(f'%{event.name}%'))
                .count()
            )
            event_mentions.append({"name": event.name, "mentions": mention_count})
    event_mentions.sort(key=lambda x: x["mentions"], reverse=True)

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
        retention_rate=retention_rate,
        returning_users=returning_users,
        rrpp_interest_rate=rrpp_interest_rate,
        rrpp_users=rrpp_users,
        # Charts
        weekly_users=weekly_users,
        hourly_messages=hourly_messages,
        venues_data=venues_data,
        themes_data=themes_data,
        new_returning_weekly=new_returning_weekly,
        event_mentions=event_mentions,
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


@stats_bp.route("/estadisticas/rrpp-insights")
@login_required
def rrpp_insights():
    """Return RRPP-focused AI insights."""
    try:
        from services.ai_insights import get_rrpp_insights
        data = get_rrpp_insights()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@stats_bp.route("/estadisticas/topic-distribution")
@login_required
def topic_distribution():
    """Return AI-categorized topic distribution."""
    try:
        from services.ai_insights import get_topic_distribution
        data = get_topic_distribution()
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
