from flask import Flask, redirect, url_for, g
from config import Config
from models import db, CompanyInfo, User, Venue, VENUES


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

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
