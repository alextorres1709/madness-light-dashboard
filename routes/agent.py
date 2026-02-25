from flask import Blueprint, render_template
from models import db, CompanyInfo, Message
from routes.auth import login_required

agent_bp = Blueprint("agent", __name__)


@agent_bp.route("/agente")
@login_required
def index():
    company = CompanyInfo.query.first()
    messages_total = Message.query.count()

    # Recent messages for the agent feed
    recent_messages = (
        Message.query.order_by(Message.timestamp.desc()).limit(20).all()
    )

    return render_template(
        "agente.html",
        company=company,
        messages_total=messages_total,
        recent_messages=recent_messages,
    )
