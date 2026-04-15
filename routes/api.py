from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from models import db, Event, Message, CompanyInfo, Client
from services.notifications import notify_birthday_greeted, notify_new_client

api_bp = Blueprint("api", __name__, url_prefix="/api")


def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("X-API-Key", "")
        if api_key != current_app.config["API_KEY"]:
            return jsonify({"error": "Invalid API key"}), 401
        return f(*args, **kwargs)

    return decorated


# ─── Events ──────────────────────────────────────────

@api_bp.route("/events", methods=["GET"])
@require_api_key
def get_events():
    show_all = request.args.get("all", "false").lower() == "true"

    if show_all:
        events = Event.query.order_by(Event.date.desc()).all()
    else:
        events = (
            Event.query.filter_by(active=True)
            .order_by(Event.date.asc())
            .all()
        )

    return jsonify([e.to_dict() for e in events])


@api_bp.route("/events", methods=["POST"])
@require_api_key
def create_event():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        event = Event(
            name=data.get("name", ""),
            date=datetime.fromisoformat(data["date"]),
            venue=data.get("venue", ""),
            theme=data.get("theme", "Normal"),
            description=data.get("description", ""),
            dj_info=data.get("dj_info", ""),
            capacity=int(data.get("capacity", 0)),
            entry_price=data.get("entry_price", ""),
            entry_link=data.get("entry_link", ""),
            image_url=data.get("image_url", ""),
            active=data.get("active", True),
        )
        db.session.add(event)
        db.session.commit()
        return jsonify(event.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# ─── Messages ────────────────────────────────────────

@api_bp.route("/messages", methods=["POST"])
@require_api_key
def log_message():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        msg = Message(
            user_id=data.get("user_id", "unknown"),
            user_name=data.get("user_name", "Unknown"),
            message=data.get("message", ""),
            response=data.get("response", ""),
            platform=data.get("platform", "whatsapp"),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if data.get("timestamp")
            else datetime.now(timezone.utc),
        )
        db.session.add(msg)
        db.session.commit()
        return jsonify(msg.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@api_bp.route("/messages", methods=["GET"])
@require_api_key
def get_messages():
    limit = request.args.get("limit", 50, type=int)
    from_date = request.args.get("from")
    to_date = request.args.get("to")

    query = Message.query

    if from_date:
        query = query.filter(Message.timestamp >= datetime.fromisoformat(from_date))
    if to_date:
        query = query.filter(Message.timestamp <= datetime.fromisoformat(to_date))

    messages = query.order_by(Message.timestamp.desc()).limit(limit).all()
    return jsonify([m.to_dict() for m in messages])


@api_bp.route("/messages/stats", methods=["GET"])
@require_api_key
def message_stats():
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)

    return jsonify(
        {
            "today": Message.query.filter(Message.timestamp >= today_start).count(),
            "this_week": Message.query.filter(Message.timestamp >= week_start).count(),
            "this_month": Message.query.filter(
                Message.timestamp >= month_start
            ).count(),
            "total": Message.query.count(),
        }
    )


# ─── Company Info ────────────────────────────────────

@api_bp.route("/company-info", methods=["GET"])
@require_api_key
def get_company_info():
    company = CompanyInfo.query.first()
    if not company:
        return jsonify({"error": "No company info found"}), 404
    return jsonify(company.to_dict())


@api_bp.route("/company-info", methods=["PUT"])
@require_api_key
def update_company_info():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    company = CompanyInfo.query.first()
    if not company:
        company = CompanyInfo()
        db.session.add(company)

    for field in ["name", "description", "phone", "email", "address", "hours", "extra_info"]:
        if field in data:
            setattr(company, field, data[field])

    db.session.commit()
    return jsonify(company.to_dict())


# ─── Birthdays (n8n automation) ─────────────────────

@api_bp.route("/birthdays/today", methods=["GET"])
@require_api_key
def birthdays_today():
    """Returns active, opted-in clients whose birthday is today and haven't been greeted this year."""
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%d/%m")  # matches dob format "dd/mm/yyyy"

    # WhatsApp Business compliance: only contact opted-in users for marketing/birthday templates
    clients = Client.query.filter(
        Client.status == "active",
        Client.whatsapp_opt_in == True,
        Client.dob.ilike(f"{today_str}%"),
    ).all()

    # Filter out already greeted this year
    ungreeted = [
        c for c in clients
        if not c.birthday_greeted_at or c.birthday_greeted_at.year < now.year
    ]

    return jsonify([c.to_dict() for c in ungreeted])


@api_bp.route("/birthdays/tomorrow", methods=["GET"])
@require_api_key
def birthdays_tomorrow():
    """Returns active, opted-in clients whose birthday is tomorrow and haven't been pre-greeted this year.

    Re-uses ``birthday_greeted_at`` as a deduplication marker: if it was set in
    the last 48h we assume the pre-notice (or full greeting) already went out,
    avoiding double sends if the n8n schedule is more aggressive than daily.
    """
    now = datetime.now(timezone.utc)
    tomorrow = now + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%d/%m")

    clients = Client.query.filter(
        Client.status == "active",
        Client.whatsapp_opt_in == True,
        Client.dob.ilike(f"{tomorrow_str}%"),
    ).all()

    cutoff = now - timedelta(hours=48)
    pending = [
        c for c in clients
        if not c.birthday_greeted_at or c.birthday_greeted_at < cutoff
    ]

    return jsonify([c.to_dict() for c in pending])


@api_bp.route("/birthdays/greeted/<int:client_id>", methods=["POST"])
@require_api_key
def mark_greeted(client_id):
    """Marks a client as birthday-greeted for this year."""
    client = Client.query.get_or_404(client_id)
    client.birthday_greeted_at = datetime.now(timezone.utc)
    notify_birthday_greeted(client.name)
    db.session.commit()
    return jsonify({"ok": True, "client": client.to_dict()})
