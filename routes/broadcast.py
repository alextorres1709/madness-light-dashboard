"""
WhatsApp Broadcast — compliant with WhatsApp Business API rules.

Rules enforced:
 1. Only pre-approved Message Templates (no free-form business-initiated messages)
 2. Only sends to clients with whatsapp_opt_in = True and a valid phone number
 3. Rate-limited sending with delays between messages
 4. Logs every broadcast for audit trail
"""
from datetime import datetime, timedelta, timezone
import time
import threading
import requests as http_requests
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app, jsonify,
)
from models import db, Client
from routes.auth import admin_required
from services.activity import log_activity
from services.notifications import notify_broadcast_sent

broadcast_bp = Blueprint("broadcast", __name__)

# WhatsApp Cloud API base
WA_API = "https://graph.facebook.com/v21.0"

# Max messages per broadcast (WhatsApp tier safety — start conservative)
MAX_PER_BROADCAST = 200

# Delay between individual API calls (seconds) to avoid throttling
SEND_DELAY = 0.15


def _wa_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _send_template(phone_id: str, token: str, to: str, template_name: str,
                    language: str, variables: list[str]) -> dict:
    """Send a single WhatsApp template message. Returns API response dict."""
    body = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language},
        },
    }
    # Add body parameters if variables provided
    if variables:
        body["template"]["components"] = [{
            "type": "body",
            "parameters": [
                {"type": "text", "text": v} for v in variables
            ],
        }]

    resp = http_requests.post(
        f"{WA_API}/{phone_id}/messages",
        headers=_wa_headers(token),
        json=body,
        timeout=10,
    )
    return resp.json()


def _fetch_templates(phone_id: str, token: str) -> list[dict]:
    """Fetch approved message templates from Meta API."""
    # We need the WABA ID, but we can get templates via the phone number's WABA
    # The business phone endpoint gives us the waba_id
    try:
        resp = http_requests.get(
            f"{WA_API}/{phone_id}/message_templates",
            headers=_wa_headers(token),
            params={"limit": 100},
            timeout=10,
        )
        data = resp.json()
        if "data" in data:
            return [
                t for t in data["data"]
                if t.get("status") == "APPROVED"
            ]
    except Exception:
        pass

    # Fallback: try via whatsapp_business_account
    try:
        resp = http_requests.get(
            f"{WA_API}/{phone_id}",
            headers=_wa_headers(token),
            params={"fields": "whatsapp_business_account"},
            timeout=10,
        )
        waba_id = resp.json().get("whatsapp_business_account", "")
        if waba_id:
            resp2 = http_requests.get(
                f"{WA_API}/{waba_id}/message_templates",
                headers=_wa_headers(token),
                params={"limit": 100, "status": "APPROVED"},
                timeout=10,
            )
            data2 = resp2.json()
            if "data" in data2:
                return data2["data"]
    except Exception:
        pass

    return []


@broadcast_bp.route("/mensajes")
@admin_required
def index():
    token = current_app.config.get("WHATSAPP_TOKEN")
    phone_id = current_app.config.get("WHATSAPP_PHONE_ID")
    has_wa = bool(token and phone_id)

    # Audience stats (only clients with opt-in AND phone number)
    base_q = Client.query.filter(
        Client.whatsapp_opt_in == True,  # noqa: E712
        Client.phone != "",
        Client.phone.isnot(None),
        Client.status == "active",
    )
    total_opted_in = base_q.count()
    total_clients = Client.query.filter(Client.status == "active").count()

    # Fetch available templates from Meta
    templates = []
    if has_wa:
        templates = _fetch_templates(phone_id, token)

    return render_template(
        "mensajes.html",
        has_wa=has_wa,
        total_opted_in=total_opted_in,
        total_clients=total_clients,
        templates=templates,
    )


@broadcast_bp.route("/mensajes/send", methods=["POST"])
@admin_required
def send():
    token = current_app.config.get("WHATSAPP_TOKEN")
    phone_id = current_app.config.get("WHATSAPP_PHONE_ID")
    if not token or not phone_id:
        flash("WhatsApp no configurado (WHATSAPP_TOKEN / WHATSAPP_PHONE_ID)", "error")
        return redirect(url_for("broadcast.index"))

    template_name = request.form.get("template_name", "").strip()
    language = request.form.get("language", "es").strip()

    if not template_name:
        flash("Debes seleccionar una plantilla aprobada", "error")
        return redirect(url_for("broadcast.index"))

    # Collect template variables ({{1}}, {{2}}, etc.)
    variables = []
    for i in range(1, 11):
        val = request.form.get(f"var_{i}", "").strip()
        if val:
            variables.append(val)
        else:
            break

    # Query ONLY opted-in clients with phone numbers
    clients = Client.query.filter(
        Client.whatsapp_opt_in == True,  # noqa: E712
        Client.phone != "",
        Client.phone.isnot(None),
        Client.status == "active",
    ).limit(MAX_PER_BROADCAST).all()

    if not clients:
        flash("No hay clientes con opt-in activo y numero de telefono", "error")
        return redirect(url_for("broadcast.index"))

    sent = 0
    failed = 0
    errors = []

    for client in clients:
        # Clean phone number (remove spaces, dashes, keep + prefix)
        phone = client.phone.replace(" ", "").replace("-", "")
        if not phone:
            continue

        # Replace {{name}} variable if used
        client_vars = []
        for v in variables:
            client_vars.append(v.replace("{{name}}", client.name or ""))

        try:
            result = _send_template(phone_id, token, phone, template_name,
                                    language, client_vars)
            if "messages" in result:
                sent += 1
            else:
                failed += 1
                error_msg = result.get("error", {}).get("message", str(result))
                if error_msg not in errors:
                    errors.append(error_msg)
        except Exception as e:
            failed += 1
            err = str(e)
            if err not in errors:
                errors.append(err)

        # Rate limiting — respect WhatsApp API throughput
        time.sleep(SEND_DELAY)

    log_activity(
        "broadcast", "broadcast", None,
        f"WhatsApp template '{template_name}' enviado a {sent}/{len(clients)} "
        f"clientes. Errores: {failed}"
    )
    notify_broadcast_sent(sent)
    db.session.commit()

    msg = f"Plantilla '{template_name}' enviada a {sent} clientes"
    if failed:
        msg += f" ({failed} errores)"
    if errors:
        msg += f". Detalle: {errors[0][:100]}"
    flash(msg, "success" if failed == 0 else "error")
    return redirect(url_for("broadcast.index"))


# ── API: fetch templates (for dynamic UI) ──

@broadcast_bp.route("/api/broadcast/templates")
@admin_required
def api_templates():
    """Return available WhatsApp templates as JSON."""
    token = current_app.config.get("WHATSAPP_TOKEN")
    phone_id = current_app.config.get("WHATSAPP_PHONE_ID")
    if not token or not phone_id:
        return jsonify({"templates": [], "error": "WhatsApp not configured"}), 200

    templates = _fetch_templates(phone_id, token)
    # Simplify for frontend
    result = []
    for t in templates:
        components = t.get("components", [])
        body_text = ""
        for c in components:
            if c.get("type") == "BODY":
                body_text = c.get("text", "")
        result.append({
            "name": t.get("name", ""),
            "language": t.get("language", "es"),
            "category": t.get("category", ""),
            "body": body_text,
        })
    return jsonify({"templates": result})
