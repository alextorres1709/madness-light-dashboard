from flask import Blueprint, render_template
from models import db, CompanyInfo, Conversation
from routes.auth import login_required

agent_bp = Blueprint("agent", __name__)


@agent_bp.route("/agente")
@login_required
def index():
    company = CompanyInfo.query.first()
    messages_total = Conversation.query.filter_by(role="user").count()

    # Recent conversations (both user + assistant for chat view)
    recent_messages = (
        Conversation.query.order_by(Conversation.created_at.desc())
        .limit(40)
        .all()
    )
    # Reverse so oldest first (chat order)
    recent_messages = list(reversed(recent_messages))

    return render_template(
        "agente.html",
        company=company,
        messages_total=messages_total,
        recent_messages=recent_messages,
    )
