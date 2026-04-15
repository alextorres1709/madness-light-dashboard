from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, Client
from routes.auth import login_required
from services.activity import log_activity

clients_bp = Blueprint("clients", __name__)


@clients_bp.route("/clientes")
@login_required
def index():
    search = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip()

    query = Client.query

    if search:
        query = query.filter(
            db.or_(
                Client.name.ilike(f"%{search}%"),
                Client.phone.ilike(f"%{search}%"),
                Client.chat_id.ilike(f"%{search}%"),
            )
        )

    if status_filter:
        query = query.filter_by(status=status_filter)

    clients = query.order_by(Client.name.asc()).all()

    total = Client.query.count()
    active = Client.query.filter_by(status="active").count()
    opted_in = Client.query.filter_by(whatsapp_opt_in=True).count()

    return render_template(
        "clientes.html",
        clients=clients,
        search=search,
        selected_status=status_filter,
        total=total,
        active=active,
        opted_in=opted_in,
    )


@clients_bp.route("/clientes/<int:client_id>/toggle-optin", methods=["POST"])
@login_required
def toggle_optin(client_id):
    client = Client.query.get_or_404(client_id)
    client.whatsapp_opt_in = not client.whatsapp_opt_in
    db.session.commit()
    log_activity(
        action="update",
        target_type="client",
        target_id=client.id,
        details=f"WhatsApp opt-in {'activado' if client.whatsapp_opt_in else 'desactivado'} para {client.name}",
    )
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True, "opt_in": client.whatsapp_opt_in})
    flash(f"WhatsApp opt-in {'activado' if client.whatsapp_opt_in else 'desactivado'} para {client.name}", "success")
    return redirect(url_for("clients.index"))


@clients_bp.route("/clientes/<int:client_id>/toggle-status", methods=["POST"])
@login_required
def toggle_status(client_id):
    client = Client.query.get_or_404(client_id)
    client.status = "inactive" if client.status == "active" else "active"
    db.session.commit()
    log_activity(
        action="update",
        target_type="client",
        target_id=client.id,
        details=f"Estado cambiado a {client.status} para {client.name}",
    )
    flash(f"Cliente {client.name} marcado como {client.status}", "success")
    return redirect(url_for("clients.index"))
