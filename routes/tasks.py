from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, Task, REMINDER_CHOICES
from routes.auth import login_required, editor_required
from services.activity import log_activity
from services.notifications import push, NOTIF_SYSTEM

tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.route("/tareas")
@login_required
def index():
    status = request.args.get("status", "pending")
    if status == "done":
        tasks = Task.query.filter_by(done=True).order_by(Task.created_at.desc()).all()
    else:
        tasks = Task.query.filter_by(done=False).order_by(Task.created_at.asc()).all()

    pending_count = Task.query.filter_by(done=False).count()
    done_count = Task.query.filter_by(done=True).count()

    return render_template(
        "tareas.html",
        tasks=tasks,
        status=status,
        pending_count=pending_count,
        done_count=done_count,
        reminder_choices=REMINDER_CHOICES,
    )


@tasks_bp.route("/tareas/create", methods=["POST"])
@editor_required
def create():
    title = request.form.get("title", "").strip()
    if not title:
        flash("El titulo no puede estar vacio", "error")
        return redirect(url_for("tasks.index"))

    task = Task(
        title=title,
        description=request.form.get("description", "").strip(),
        reminder_minutes=int(request.form.get("reminder_minutes", 60) or 60),
    )
    db.session.add(task)
    push(
        title="Nueva tarea creada",
        body=title,
        category=NOTIF_SYSTEM,
        icon="task",
    )
    log_activity("create", "task", details=f"Created task: {title}")
    db.session.commit()
    flash("Tarea creada", "success")
    return redirect(url_for("tasks.index"))


@tasks_bp.route("/tareas/<int:task_id>/done", methods=["POST"])
@editor_required
def mark_done(task_id):
    task = Task.query.get_or_404(task_id)
    task.done = True
    log_activity("complete", "task", task.id, f"Completed task: {task.title}")
    db.session.commit()
    flash("Tarea completada", "success")
    return redirect(url_for("tasks.index"))


@tasks_bp.route("/tareas/<int:task_id>/reopen", methods=["POST"])
@editor_required
def reopen(task_id):
    task = Task.query.get_or_404(task_id)
    task.done = False
    task.last_notified_at = None
    db.session.commit()
    flash("Tarea reabierta", "success")
    return redirect(url_for("tasks.index", status="pending"))


@tasks_bp.route("/tareas/<int:task_id>/delete", methods=["POST"])
@editor_required
def delete(task_id):
    task = Task.query.get_or_404(task_id)
    log_activity("delete", "task", task_id, f"Deleted task: {task.title}")
    db.session.delete(task)
    db.session.commit()
    flash("Tarea eliminada", "success")
    return redirect(url_for("tasks.index"))


@tasks_bp.route("/tareas/<int:task_id>/reminder", methods=["POST"])
@editor_required
def update_reminder(task_id):
    task = Task.query.get_or_404(task_id)
    task.reminder_minutes = int(request.form.get("reminder_minutes", 60) or 60)
    task.last_notified_at = None  # reset so next cycle picks it up
    db.session.commit()
    flash("Recordatorio actualizado", "success")
    return redirect(url_for("tasks.index"))


# ── API for JS polling ────────────────────────────────────

@tasks_bp.route("/tareas/api/due-reminders")
@login_required
def due_reminders():
    """Return pending tasks whose reminder is due (for native OS notifications)."""
    now = datetime.now(timezone.utc)
    pending = Task.query.filter_by(done=False).filter(Task.reminder_minutes > 0).all()

    due = []
    for t in pending:
        if t.last_notified_at is None:
            due.append(t)
        else:
            elapsed = (now - t.last_notified_at).total_seconds() / 60
            if elapsed >= t.reminder_minutes:
                due.append(t)

    # Mark them as notified
    for t in due:
        t.last_notified_at = now
    if due:
        db.session.commit()

    return jsonify({
        "due": [t.to_dict() for t in due],
        "pending_count": Task.query.filter_by(done=False).count(),
    })
