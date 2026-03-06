from flask import Blueprint, render_template
from models import db, CompanyInfo, Conversation, Event, Venue
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

    # Data for interactive capability items
    active_events = Event.query.filter_by(active=True).order_by(Event.date).all()
    active_venues = Venue.query.filter_by(active=True).order_by(Venue.name).all()
    unique_users = db.session.query(
        db.func.count(db.func.distinct(Conversation.user_id))
    ).scalar() or 0
    events_with_links = [e for e in active_events if e.entry_link]

    return render_template(
        "agente.html",
        company=company,
        messages_total=messages_total,
        recent_messages=recent_messages,
        active_events=active_events,
        active_venues=active_venues,
        unique_users=unique_users,
        events_with_links=events_with_links,
    )
