import csv
import io
import calendar as cal_module
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from models import db, Event, Venue, Conversation, VENUES, THEMES
from routes.auth import login_required, editor_required
from services.activity import log_activity

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

    # Load venues from DB, fall back to hardcoded list
    db_venues = Venue.query.filter_by(active=True).order_by(Venue.name).all()
    venue_names = [v.name for v in db_venues] if db_venues else VENUES

    return render_template(
        "events.html",
        events=events,
        venues=venue_names,
        themes=THEMES,
        search=search,
        selected_venue=venue_filter,
        selected_theme=theme_filter,
        selected_status=status,
    )


@events_bp.route("/events/create", methods=["POST"])
@editor_required
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
        log_activity("create", "event", details=f"Created event: {event.name}")
        db.session.commit()
        flash("Fiesta creada correctamente", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al crear la fiesta: {str(e)}", "error")

    return redirect(url_for("events.index"))


@events_bp.route("/events/<int:event_id>/update", methods=["POST"])
@editor_required
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
        log_activity("update", "event", event.id, f"Updated event: {event.name}")
        db.session.commit()
        flash("Fiesta actualizada correctamente", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar: {str(e)}", "error")

    return redirect(url_for("events.index"))


@events_bp.route("/events/<int:event_id>/delete", methods=["POST"])
@editor_required
def delete(event_id):
    event = Event.query.get_or_404(event_id)
    try:
        log_activity("delete", "event", event_id, f"Deleted event: {event.name}")
        db.session.delete(event)
        db.session.commit()
        flash("Fiesta eliminada", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar: {str(e)}", "error")

    return redirect(url_for("events.index"))


@events_bp.route("/events/<int:event_id>/toggle", methods=["POST"])
@editor_required
def toggle(event_id):
    event = Event.query.get_or_404(event_id)
    event.active = not event.active
    log_activity("toggle", "event", event.id, f"Toggled event: {event.name}")
    db.session.commit()
    status = "activada" if event.active else "desactivada"
    flash(f"Fiesta {status}", "success")
    return redirect(url_for("events.index"))


# ── CSV Export ─────────────────────────────────────────────

@events_bp.route("/events/export/csv")
@login_required
def export_csv():
    events = Event.query.order_by(Event.date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Nombre", "Fecha", "Sala", "Tematica", "Aforo", "Precio", "Estado", "Creado"])

    for e in events:
        writer.writerow([
            e.name,
            e.date.strftime("%Y-%m-%d %H:%M") if e.date else "",
            e.venue,
            e.theme,
            e.capacity,
            e.entry_price,
            "Activa" if e.active else "Inactiva",
            e.created_at.strftime("%Y-%m-%d") if e.created_at else "",
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=fiestas_export.csv"},
    )


# ── Calendar View ──────────────────────────────────────────

@events_bp.route("/events/calendario")
@login_required
def calendario():
    now = datetime.now()
    year = request.args.get("year", now.year, type=int)
    month = request.args.get("month", now.month, type=int)

    if month < 1:
        month, year = 12, year - 1
    if month > 12:
        month, year = 1, year + 1

    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1)
    else:
        last_day = datetime(year, month + 1, 1)

    events = (
        Event.query
        .filter(Event.date >= first_day, Event.date < last_day)
        .order_by(Event.date.asc())
        .all()
    )

    events_by_day = {}
    for e in events:
        day = e.date.day
        events_by_day.setdefault(day, []).append(e)

    month_cal = cal_module.monthcalendar(year, month)
    month_names = [
        "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    return render_template(
        "calendario.html",
        month_cal=month_cal,
        month_name=month_names[month],
        year=year,
        month=month,
        events_by_day=events_by_day,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
        today=now.day if now.year == year and now.month == month else None,
    )


# ── Event Analytics ────────────────────────────────────────

@events_bp.route("/events/<int:event_id>/analytics")
@login_required
def analytics(event_id):
    event = Event.query.get_or_404(event_id)

    mentions = (
        Conversation.query
        .filter(
            Conversation.role == "user",
            Conversation.content.ilike(f"%{event.name}%"),
        )
        .order_by(Conversation.created_at.asc())
        .all()
    )

    mention_count = len(mentions)
    unique_users = len(set(m.user_id for m in mentions))

    daily_mentions = {}
    for m in mentions:
        day_key = m.created_at.strftime("%Y-%m-%d") if m.created_at else "unknown"
        daily_mentions[day_key] = daily_mentions.get(day_key, 0) + 1

    timeline = [{"date": k, "count": v} for k, v in sorted(daily_mentions.items())]

    return jsonify({
        "event_id": event.id,
        "event_name": event.name,
        "mention_count": mention_count,
        "unique_users": unique_users,
        "timeline": timeline,
    })
