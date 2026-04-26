from flask import Blueprint, render_template, request
from models import db, CompanyInfo, Conversation, Event, Venue
from routes.auth import login_required

agent_bp = Blueprint("agent", __name__)


@agent_bp.route("/agente")
@login_required
def index():
    company = CompanyInfo.query.first()
    messages_total = Conversation.query.filter_by(role="user").count()

    # All unique users who have spoken with the bot (for selector)
    user_ids = [
        r[0] for r in db.session.query(db.func.distinct(Conversation.user_id))
        .order_by(Conversation.user_id).all()
    ]

    # Selected user (default: most recent)
    selected_user = request.args.get("user_id")
    if not selected_user and user_ids:
        # Pick the user with the most recent message
        latest = (
            Conversation.query.filter_by(role="user")
            .order_by(Conversation.created_at.desc())
            .first()
        )
        selected_user = latest.user_id if latest else None

    # Conversation for selected user
    recent_messages = []
    if selected_user:
        recent_messages = (
            Conversation.query.filter_by(user_id=selected_user)
            .order_by(Conversation.created_at.asc())
            .limit(60)
            .all()
        )

    # Data for interactive capability items
    active_events = Event.query.filter_by(active=True).order_by(Event.date).all()
    active_venues = Venue.query.filter_by(active=True).order_by(Venue.name).all()
    unique_users = len(user_ids)
    events_with_links = [e for e in active_events if e.entry_link]

    return render_template(
        "agente.html",
        company=company,
        messages_total=messages_total,
        recent_messages=recent_messages,
        user_ids=user_ids,
        selected_user=selected_user,
        active_events=active_events,
        active_venues=active_venues,
        unique_users=unique_users,
        events_with_links=events_with_links,
    )
