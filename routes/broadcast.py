from datetime import datetime, timedelta, timezone
import requests as http_requests
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models import db, Conversation
from routes.auth import admin_required
from services.activity import log_activity

broadcast_bp = Blueprint("broadcast", __name__)

BATCH_SIZE = 50


@broadcast_bp.route("/mensajes")
@admin_required
def index():
    now = datetime.now(timezone.utc)

    all_users = (
        db.session.query(Conversation.user_id)
        .filter(Conversation.role == "user")
        .distinct()
        .count()
    )
    active_7d = (
        db.session.query(Conversation.user_id)
        .filter(Conversation.role == "user", Conversation.created_at >= now - timedelta(days=7))
        .distinct()
        .count()
    )
    active_30d = (
        db.session.query(Conversation.user_id)
        .filter(Conversation.role == "user", Conversation.created_at >= now - timedelta(days=30))
        .distinct()
        .count()
    )

    has_token = bool(current_app.config.get("TELEGRAM_BOT_TOKEN"))

    return render_template(
        "mensajes.html",
        all_users=all_users,
        active_7d=active_7d,
        active_30d=active_30d,
        has_token=has_token,
    )


@broadcast_bp.route("/mensajes/send", methods=["POST"])
@admin_required
def send():
    token = current_app.config.get("TELEGRAM_BOT_TOKEN")
    if not token:
        flash("TELEGRAM_BOT_TOKEN no configurado", "error")
        return redirect(url_for("broadcast.index"))

    message_text = request.form.get("message", "").strip()
    audience = request.form.get("audience", "all")

    if not message_text:
        flash("El mensaje no puede estar vacío", "error")
        return redirect(url_for("broadcast.index"))

    now = datetime.now(timezone.utc)
    query = (
        db.session.query(db.func.distinct(Conversation.user_id))
        .filter(Conversation.role == "user")
    )

    if audience == "7d":
        query = query.filter(Conversation.created_at >= now - timedelta(days=7))
    elif audience == "30d":
        query = query.filter(Conversation.created_at >= now - timedelta(days=30))

    chat_ids = [row[0] for row in query.all()]

    if not chat_ids:
        flash("No hay usuarios en la audiencia seleccionada", "error")
        return redirect(url_for("broadcast.index"))

    # Send in batches to stay within Vercel timeout
    sent = 0
    failed = 0
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"

    for chat_id in chat_ids[:BATCH_SIZE]:
        try:
            resp = http_requests.post(
                api_url,
                json={"chat_id": chat_id, "text": message_text, "parse_mode": "HTML"},
                timeout=5,
            )
            if resp.status_code == 200:
                sent += 1
            else:
                failed += 1
        except Exception:
            failed += 1

    remaining = max(0, len(chat_ids) - BATCH_SIZE)

    log_activity(
        "broadcast", "broadcast", None,
        f"Sent to {sent}/{len(chat_ids)} users (audience={audience}). Failed: {failed}"
    )
    db.session.commit()

    msg = f"Mensaje enviado a {sent} usuarios"
    if failed:
        msg += f" ({failed} errores)"
    if remaining:
        msg += f". Quedan {remaining} usuarios pendientes."
    flash(msg, "success" if failed == 0 else "error")
    return redirect(url_for("broadcast.index"))
