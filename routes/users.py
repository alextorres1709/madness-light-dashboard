from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from models import db, User, ROLES
from routes.auth import admin_required

users_bp = Blueprint("users", __name__)


@users_bp.route("/usuarios")
@admin_required
def index():
    search = request.args.get("search", "").strip()
    role_filter = request.args.get("role", "").strip()

    query = User.query

    if search:
        query = query.filter(
            db.or_(
                User.email.ilike(f"%{search}%"),
                User.name.ilike(f"%{search}%"),
            )
        )

    if role_filter and role_filter in ROLES:
        query = query.filter_by(role=role_filter)

    users = query.order_by(User.created_at.desc()).all()

    return render_template(
        "usuarios.html",
        users=users,
        roles=ROLES,
        search=search,
        selected_role=role_filter,
    )


@users_bp.route("/usuarios/create", methods=["POST"])
@admin_required
def create():
    try:
        email = request.form.get("email", "").strip().lower()
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "viewer")

        if not email or not password:
            flash("Email y contraseña son obligatorios", "error")
            return redirect(url_for("users.index"))

        if User.query.filter_by(email=email).first():
            flash("Ya existe un usuario con ese email", "error")
            return redirect(url_for("users.index"))

        if role not in ROLES:
            role = "viewer"

        user = User(email=email, name=name, role=role, active=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash(f"Usuario {email} creado correctamente", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al crear usuario: {str(e)}", "error")

    return redirect(url_for("users.index"))


@users_bp.route("/usuarios/<int:user_id>/update", methods=["POST"])
@admin_required
def update(user_id):
    user = User.query.get_or_404(user_id)
    try:
        user.name = request.form.get("name", user.name).strip()
        user.email = request.form.get("email", user.email).strip().lower()
        role = request.form.get("role", user.role)
        if role in ROLES:
            user.role = role

        password = request.form.get("password", "").strip()
        if password:
            user.set_password(password)

        db.session.commit()
        flash("Usuario actualizado correctamente", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar: {str(e)}", "error")

    return redirect(url_for("users.index"))


@users_bp.route("/usuarios/<int:user_id>/toggle", methods=["POST"])
@admin_required
def toggle(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == g.user.id:
        flash("No puedes desactivarte a ti mismo", "error")
        return redirect(url_for("users.index"))

    user.active = not user.active
    db.session.commit()
    status = "activado" if user.active else "desactivado"
    flash(f"Usuario {status}", "success")
    return redirect(url_for("users.index"))


@users_bp.route("/usuarios/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == g.user.id:
        flash("No puedes eliminarte a ti mismo", "error")
        return redirect(url_for("users.index"))

    try:
        db.session.delete(user)
        db.session.commit()
        flash("Usuario eliminado", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar: {str(e)}", "error")

    return redirect(url_for("users.index"))
