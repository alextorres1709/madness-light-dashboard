from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template
from sqlalchemy import or_
from models import db, Event, Conversation
from routes.auth import login_required
import threading

RRPP_KEYWORDS = [
    'rrpp', 'promotor', 'promotora', 'comision', 'comisiones',
    'ganar dinero', 'equipo', 'reclutar', 'relaciones publicas',
    'codigo', 'enlace', 'rangos', 'puntos', 'ser rrpp',
    'quiero ser', 'trabajar', 'sueldo', 'beneficios'
]

dashboard_bp = Blueprint("dashboard", __name__)

# ── Simple TTL cache for heavy analytics (5 min) ──────────────────────────────
_cache: dict = {}
_cache_lock = threading.Lock()
_CACHE_TTL = 300  # seconds


def _cached(key, fn):
    """Run fn() and cache result for _CACHE_TTL seconds."""
    with _cache_lock:
        entry = _cache.get(key)
        if entry and (datetime.now().timestamp() - entry["ts"]) < _CACHE_TTL:
            return entry["val"]
    val = fn()
    with _cache_lock:
        _cache[key] = {"val": val, "ts": datetime.now().timestamp()}
    return val


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


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)
    thirty_days_ago = today_start - timedelta(days=30)

    # ── Fast queries (run every request) ──────────────────────────────────────

    # All message KPIs in ONE query
    row = db.session.query(
        db.func.count(Conversation.id).filter(Conversation.created_at >= today_start),
        db.func.count(Conversation.id).filter(Conversation.created_at >= week_start),
        db.func.count(Conversation.id).filter(Conversation.created_at >= month_start),
        db.func.count(Conversation.id),
    ).filter(Conversation.role == "user").one()
    messages_today, messages_week, messages_month, messages_total = row

    # Events: active count + upcoming + total — 2 queries (events table is small)
    all_active = Event.query.filter_by(active=True).order_by(Event.date.asc()).all()
    active_events = len(all_active)
    upcoming_events = [e for e in all_active if e.date and e.date >= now.replace(tzinfo=None)][:5]
    total_events = Event.query.count()

    # Recent user messages for activity feed (fast, indexed)
    recent_messages = (
        Conversation.query.filter_by(role="user")
        .order_by(Conversation.created_at.desc())
        .limit(20)
        .all()
    )

    # Daily messages chart — 1 GROUP BY query
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
    daily_messages = [
        {"date": (thirty_days_ago + timedelta(days=i)).strftime("%d/%m"),
         "count": daily_map.get((thirty_days_ago + timedelta(days=i)).strftime("%Y-%m-%d"), 0)}
        for i in range(30)
    ]

    # Hourly messages chart — 1 GROUP BY query
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

    # ── Slow/heavy analytics — cached 5 minutes ───────────────────────────────

    def _get_user_stats():
        total_u = (
            db.session.query(db.func.count(db.func.distinct(Conversation.user_id)))
            .filter(Conversation.role == "user")
            .scalar()
        ) or 0

        keyword_filters = [Conversation.content.ilike(f'%{kw}%') for kw in RRPP_KEYWORDS]
        rrpp_u = (
            db.session.query(db.func.count(db.func.distinct(Conversation.user_id)))
            .filter(Conversation.role == "user", or_(*keyword_filters))
            .scalar()
        ) or 0

        returning_u = (
            db.session.query(db.func.count())
            .select_from(
                db.session.query(Conversation.user_id)
                .filter(Conversation.role == "user")
                .group_by(Conversation.user_id)
                .having(db.func.count(Conversation.id) > 1)
                .subquery()
            )
        ).scalar() or 0

        return total_u, rrpp_u, returning_u

    total_users, rrpp_users, returning_users = _cached("user_stats", _get_user_stats)
    rrpp_interest_rate = round((rrpp_users / total_users) * 100, 1) if total_users else 0
    retention_rate = round((returning_users / total_users) * 100, 1) if total_users else 0

    # ── Activity feed ─────────────────────────────────────────────────────────
    feed_items = []
    seen_users: set = set()
    for m in recent_messages:
        if m.user_id in seen_users:
            continue
        seen_users.add(m.user_id)
        feed_items.append({
            "type": "consulta",
            "label": "Consulta resuelta",
            "desc": m.content[:70] + ("…" if len(m.content) > 70 else ""),
            "link": f"/conversaciones/{m.user_id}",
            "ago": _time_ago(m.created_at, now),
        })

    for e in all_active[:5]:
        feed_items.append({
            "type": "fiesta",
            "label": "Fiesta activa",
            "desc": f"{e.name} — {e.venue}" + (f" · {e.date.strftime('%d/%m/%Y')}" if e.date else ""),
            "link": "/fiestas",
            "ago": "",
        })

    feed_items = feed_items[:12]

    return render_template(
        "dashboard.html",
        messages_today=messages_today,
        messages_week=messages_week,
        messages_month=messages_month,
        messages_total=messages_total,
        active_events=active_events,
        total_events=total_events,
        upcoming_events=upcoming_events,
        recent_activity=feed_items,
        daily_messages=daily_messages,
        hourly_messages=hourly_messages,
        total_users=total_users,
        rrpp_users=rrpp_users,
        rrpp_interest_rate=rrpp_interest_rate,
        retention_rate=retention_rate,
        returning_users=returning_users,
    )
