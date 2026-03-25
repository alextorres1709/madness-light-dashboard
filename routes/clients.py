from flask import Blueprint, render_template, request
from models import db, Client
from routes.auth import login_required

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

    return render_template(
        "clientes.html",
        clients=clients,
        search=search,
        selected_status=status_filter,
        total=total,
        active=active,
    )
