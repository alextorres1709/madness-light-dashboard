from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Venue
from routes.auth import admin_required
from services.activity import log_activity

venues_bp = Blueprint("venues", __name__)


@venues_bp.route("/salas")
@admin_required
def index():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()

    query = Venue.query
    if search:
        query = query.filter(
            db.or_(
                Venue.name.ilike(f"%{search}%"),
                Venue.address.ilike(f"%{search}%"),
            )
        )
    if status == "active":
        query = query.filter_by(active=True)
    elif status == "inactive":
        query = query.filter_by(active=False)

    venues = query.order_by(Venue.name.asc()).all()
    return render_template("salas.html", venues=venues, search=search, selected_status=status)


@venues_bp.route("/salas/create", methods=["POST"])
@admin_required
def create():
    try:
        venue = Venue(
            name=request.form.get("name", "").strip(),
            address=request.form.get("address", "").strip(),
            capacity=int(request.form.get("capacity", 0) or 0),
            image_url=request.form.get("image_url", "").strip(),
            active=request.form.get("active") == "on",
        )
        db.session.add(venue)
        log_activity("create", "venue", details=f"Created venue: {venue.name}")
        db.session.commit()
        flash("Sala creada correctamente", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al crear la sala: {str(e)}", "error")
    return redirect(url_for("venues.index"))


@venues_bp.route("/salas/<int:venue_id>/update", methods=["POST"])
@admin_required
def update(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    try:
        venue.name = request.form.get("name", venue.name).strip()
        venue.address = request.form.get("address", venue.address).strip()
        venue.capacity = int(request.form.get("capacity", venue.capacity) or 0)
        venue.image_url = request.form.get("image_url", venue.image_url).strip()
        venue.active = request.form.get("active") == "on"
        log_activity("update", "venue", venue.id, f"Updated venue: {venue.name}")
        db.session.commit()
        flash("Sala actualizada correctamente", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar: {str(e)}", "error")
    return redirect(url_for("venues.index"))


@venues_bp.route("/salas/<int:venue_id>/toggle", methods=["POST"])
@admin_required
def toggle(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    venue.active = not venue.active
    log_activity("toggle", "venue", venue.id, f"Toggled venue: {venue.name}")
    db.session.commit()
    flash(f"Sala {'activada' if venue.active else 'desactivada'}", "success")
    return redirect(url_for("venues.index"))


@venues_bp.route("/salas/<int:venue_id>/delete", methods=["POST"])
@admin_required
def delete(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    try:
        log_activity("delete", "venue", venue_id, f"Deleted venue: {venue.name}")
        db.session.delete(venue)
        db.session.commit()
        flash("Sala eliminada", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar: {str(e)}", "error")
    return redirect(url_for("venues.index"))
