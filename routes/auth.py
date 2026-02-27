from functools import wraps
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    g,
)
from models import db, User

auth_bp = Blueprint("auth", __name__)


def _load_current_user():
    """Load user from session into g.user (called via before_request)."""
    g.user = None
    user_id = session.get("user_id")
    if user_id:
        g.user = db.session.get(User, user_id)
        if g.user and not g.user.active:
            session.clear()
            g.user = None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not g.get("user"):
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not g.get("user"):
            return redirect(url_for("auth.login"))
        if g.user.role != "admin":
            flash("No tienes permisos para acceder a esta sección", "error")
            return redirect(url_for("dashboard.index"))
        return f(*args, **kwargs)

    return decorated


def editor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not g.get("user"):
            return redirect(url_for("auth.login"))
        if g.user.role not in ("admin", "editor"):
            flash("No tienes permisos para realizar esta acción", "error")
            return redirect(url_for("dashboard.index"))
        return f(*args, **kwargs)

    return decorated


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.get("user"):
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and user.active and user.check_password(password):
            session["user_id"] = user.id
            return redirect(url_for("dashboard.index"))
        else:
            flash("Credenciales incorrectas", "error")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
