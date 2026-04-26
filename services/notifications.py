from models import db, Notification, NOTIF_EVENT, NOTIF_CLIENT, NOTIF_BIRTHDAY, NOTIF_BROADCAST, NOTIF_SYSTEM


def push(title, body="", category=NOTIF_SYSTEM, icon="info"):
    """Create a new notification."""
    n = Notification(title=title, body=body, category=category, icon=icon)
    db.session.add(n)
    # Don't commit here — let the caller's transaction handle it.
    return n


def notify_event_created(event_name, venue):
    return push(
        title="Nueva fiesta creada",
        body=f"{event_name} — {venue}",
        category=NOTIF_EVENT,
        icon="party",
    )


def notify_event_updated(event_name):
    return push(
        title="Fiesta actualizada",
        body=event_name,
        category=NOTIF_EVENT,
        icon="party",
    )


def notify_event_deleted(event_name):
    return push(
        title="Fiesta eliminada",
        body=event_name,
        category=NOTIF_EVENT,
        icon="party",
    )


def notify_new_client(client_name):
    return push(
        title="Nuevo cliente registrado",
        body=client_name,
        category=NOTIF_CLIENT,
        icon="user",
    )


def notify_birthday_greeted(client_name):
    return push(
        title="Cumpleanos enviado",
        body=f"Felicitacion enviada a {client_name}",
        category=NOTIF_BIRTHDAY,
        icon="heart",
    )


def notify_broadcast_sent(count):
    return push(
        title="Mensaje masivo enviado",
        body=f"Enviado a {count} usuarios",
        category=NOTIF_BROADCAST,
        icon="send",
    )


def notify_optin_confirmed(client_name):
    return push(
        title="Opt-in WhatsApp confirmado",
        body=f"{client_name} ha aceptado recibir mensajes",
        category=NOTIF_CLIENT,
        icon="heart",
    )
