from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, Event, VENUES, THEMES
from routes.auth import login_required

events_bp = Blueprint("events", __name__)


@events_bp.route("/events")
@login_required
def index():
    search = request.args.get("search", "").strip()
    venue_filter = request.args.get("venue", "").strip()
    theme_filter = request.args.get("theme", "").strip()
    status = request.args.get("status", "").strip()

    query = Event.query

    if search:
        query = query.filter(
            db.or_(
                Event.name.ilike(f"%{search}%"),
                Event.venue.ilike(f"%{search}%"),
                Event.description.ilike(f"%{search}%"),
            )
        )

    if venue_filter:
        query = query.filter_by(venue=venue_filter)

    if theme_filter:
        query = query.filter_by(theme=theme_filter)

    if status == "active":
        query = query.filter_by(active=True)
    elif status == "inactive":
        query = query.filter_by(active=False)

    events = query.order_by(Event.date.desc()).all()

    return render_template(
        "events.html",
        events=events,
        venues=VENUES,
        themes=THEMES,
        search=search,
        selected_venue=venue_filter,
        selected_theme=theme_filter,
        selected_status=status,
    )


@events_bp.route("/events/create", methods=["POST"])
@login_required
def create():
    try:
        event = Event(
            name=request.form.get("name", "").strip(),
            date=datetime.fromisoformat(request.form.get("date", "")),
            venue=request.form.get("venue", "").strip(),
            theme=request.form.get("theme", "Normal"),
            description=request.form.get("description", "").strip(),
            dj_info=request.form.get("dj_info", "").strip(),
            capacity=int(request.form.get("capacity", 0) or 0),
            entry_price=request.form.get("entry_price", "").strip(),
            entry_link=request.form.get("entry_link", "").strip(),
            image_url=request.form.get("image_url", "").strip(),
            active=request.form.get("active") == "on",
        )
        db.session.add(event)
        db.session.commit()
        flash("Fiesta creada correctamente", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al crear la fiesta: {str(e)}", "error")

    return redirect(url_for("events.index"))


@events_bp.route("/events/<int:event_id>/update", methods=["POST"])
@login_required
def update(event_id):
    event = Event.query.get_or_404(event_id)
    try:
        event.name = request.form.get("name", event.name).strip()
        event.date = datetime.fromisoformat(request.form.get("date", event.date.isoformat()))
        event.venue = request.form.get("venue", event.venue).strip()
        event.theme = request.form.get("theme", event.theme)
        event.description = request.form.get("description", event.description).strip()
        event.dj_info = request.form.get("dj_info", event.dj_info).strip()
        event.capacity = int(request.form.get("capacity", event.capacity) or 0)
        event.entry_price = request.form.get("entry_price", event.entry_price).strip()
        event.entry_link = request.form.get("entry_link", event.entry_link).strip()
        event.image_url = request.form.get("image_url", event.image_url).strip()
        event.active = request.form.get("active") == "on"
        db.session.commit()
        flash("Fiesta actualizada correctamente", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar: {str(e)}", "error")

    return redirect(url_for("events.index"))


@events_bp.route("/events/<int:event_id>/delete", methods=["POST"])
@login_required
def delete(event_id):
    event = Event.query.get_or_404(event_id)
    try:
        db.session.delete(event)
        db.session.commit()
        flash("Fiesta eliminada", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar: {str(e)}", "error")

    return redirect(url_for("events.index"))


@events_bp.route("/events/<int:event_id>/toggle", methods=["POST"])
@login_required
def toggle(event_id):
    event = Event.query.get_or_404(event_id)
    event.active = not event.active
    db.session.commit()
    status = "activada" if event.active else "desactivada"
    flash(f"Fiesta {status}", "success")
    return redirect(url_for("events.index"))
