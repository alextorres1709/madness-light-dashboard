from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models import db, CompanyInfo
from routes.auth import admin_required

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings")
@admin_required
def index():
    company = CompanyInfo.query.first()
    if not company:
        company = CompanyInfo()
        db.session.add(company)
        db.session.commit()

    api_key = current_app.config["API_KEY"]
    return render_template("settings.html", company=company, api_key=api_key)


@settings_bp.route("/settings/update", methods=["POST"])
@admin_required
def update():
    company = CompanyInfo.query.first()
    if not company:
        company = CompanyInfo()
        db.session.add(company)

    try:
        company.name = request.form.get("name", company.name).strip()
        company.description = request.form.get("description", company.description).strip()
        company.phone = request.form.get("phone", company.phone).strip()
        company.email = request.form.get("email", company.email).strip()
        company.address = request.form.get("address", company.address).strip()
        company.hours = request.form.get("hours", company.hours).strip()
        company.extra_info = request.form.get("extra_info", company.extra_info).strip()
        db.session.commit()
        flash("Información actualizada correctamente", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar: {str(e)}", "error")

    return redirect(url_for("settings.index"))
