from flask import Flask, redirect, url_for, g
from config import Config
from models import db, CompanyInfo, User, Venue, Client, Notification, Task, VENUES


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database
    db.init_app(app)

    with app.app_context():
        try:
            db.create_all()

            # Seed company info if empty
            if not CompanyInfo.query.first():
                company = CompanyInfo(
                    name="Madness Light",
                    description=(
                        "Madness Light es una empresa de organización de fiestas light para jóvenes en Madrid. "
                        "Se centra en eventos de tarde, con temáticas especiales, DJs y animación, "
                        "ofreciendo una experiencia de ocio segura y organizada. "
                        "Trabaja con salas reconocidas de la ciudad y utiliza plataformas digitales "
                        "para la gestión de entradas y control de acceso."
                    ),
                    phone="",
                    email="info@madnesslight.com",
                    address="Madrid, España",
                    hours="Fiestas de tarde, cada 1-2 semanas",
                    extra_info=(
                        "COMPRA DE ENTRADAS:\n"
                        "Las entradas se compran exclusivamente a través de la app de Elite Events. "
                        "Desde la app se puede: comprar entradas, introducir códigos de RRPP y ver info del evento. "
                        "El acceso se controla mediante la entrada digital de la app.\n\n"
                        "TIPO DE FIESTAS:\n"
                        "Fiestas light (sin alcohol). Horario habitual de tarde. "
                        "Fiestas cada 1 o 2 semanas. Temáticas especiales (Halloween, Carnaval, Hawaiana, etc.). "
                        "DJs y animación. Eventos puntuales 'fiestas tochas' (Halloween, Carnaval, etc.).\n\n"
                        "SALAS ACTIVAS:\n"
                        "Lab (Madrid), Shôko Madrid, Jowke (Madrid), Nazca (Madrid), Tiffany's (Madrid). "
                        "Teatro Barceló ya no se utiliza (cerrado). "
                        "Las salas pueden variar según la temporada.\n\n"
                        "PROGRAMA RRPP:\n"
                        "Madness Light dispone de un programa de RRPP orientado a la promoción de sus eventos. "
                        "Info secundaria, solo se explica si el usuario pregunta específicamente."
                    ),
                )
                db.session.add(company)
                db.session.commit()

            # Seed admin user if no users exist
            if not User.query.first():
                admin = User(
                    email=app.config["ADMIN_EMAIL"].lower(),
                    name="Administrador",
                    role="admin",
                    active=True,
                )
                admin.set_password(app.config["ADMIN_PASSWORD"])
                db.session.add(admin)
                db.session.commit()

            # Seed venues from hardcoded list if empty
            if not Venue.query.first():
                for v_name in VENUES:
                    db.session.add(Venue(name=v_name, active=True))
                db.session.commit()

            # Seed demo clients if empty
            if not Client.query.first():
                demo_clients = [
                    Client(name="Carlos Martínez", phone="+34 612 345 678", dob="15/03/2008", chat_id="tg_892174531", events_attended=12, last_seen="22/03/2026", status="active"),
                    Client(name="Lucía Fernández", phone="+34 634 567 890", dob="28/07/2007", chat_id="tg_710382946", events_attended=8, last_seen="20/03/2026", status="active"),
                    Client(name="Pablo García", phone="+34 655 123 456", dob="02/11/2008", chat_id="tg_503928174", events_attended=5, last_seen="15/03/2026", status="active"),
                    Client(name="Elena Ruiz", phone="+34 678 901 234", dob="19/01/2009", chat_id="tg_629481057", events_attended=3, last_seen="10/03/2026", status="inactive"),
                    Client(name="Marcos López", phone="+34 691 234 567", dob="08/09/2007", chat_id="tg_384720196", events_attended=15, last_seen="23/03/2026", status="active"),
                    Client(name="Sara Jiménez", phone="+34 623 456 789", dob="14/05/2008", chat_id="tg_917305842", events_attended=7, last_seen="18/03/2026", status="active"),
                    Client(name="Alejandro Moreno", phone="+34 645 678 901", dob="30/12/2007", chat_id="tg_205839461", events_attended=1, last_seen="05/02/2026", status="inactive"),
                    Client(name="Marta Navarro", phone="+34 667 890 123", dob="22/06/2008", chat_id="tg_748291035", events_attended=10, last_seen="21/03/2026", status="active"),
                ]
                db.session.add_all(demo_clients)
                db.session.commit()
        except Exception as e:
            print(f"[WARNING] Database init skipped: {e}")

    # Load current user before each request
    @app.before_request
    def before_request():
        from routes.auth import _load_current_user
        _load_current_user()

    # Inject current_user into all templates
    @app.context_processor
    def inject_user():
        return {"current_user": g.get("user")}

    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.events import events_bp
    from routes.settings import settings_bp
    from routes.api import api_bp
    from routes.stats import stats_bp
    from routes.agent import agent_bp
    from routes.users import users_bp
    from routes.activity import activity_bp
    from routes.venues import venues_bp
    from routes.conversations import conversations_bp
    from routes.broadcast import broadcast_bp
    from routes.clients import clients_bp
    from routes.notifications import notifications_bp
    from routes.tasks import tasks_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(activity_bp)
    app.register_blueprint(venues_bp)
    app.register_blueprint(conversations_bp)
    app.register_blueprint(broadcast_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(tasks_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5050)
