from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect

from app.config import Config

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login = LoginManager()
from flask_socketio import SocketIO

socketio = SocketIO()


def create_app(config_class=Config):
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    csrf.init_app(flask_app)
    login.init_app(flask_app)
    login.login_view = 'main.login'

    # Register blueprints and import models
    from app.blueprints import main
    from app import routes, models

    flask_app.register_blueprint(main)

    # Exempt login and logout from CSRF protection
    # Pass the view functions so CSRFProtect can match them correctly
    try:
        csrf.exempt(routes.login)
        csrf.exempt(routes.logout)
    except Exception:
        # Fallback: exempt the whole blueprint if functions aren't available
        csrf.exempt(main)

    # Start scheduler if not in testing mode
    if not flask_app.config.get("TESTING"):
        from app.scheduler import start_scheduler
        start_scheduler(flask_app)

    # Initialize Socket.IO
    socketio.init_app(flask_app, cors_allowed_origins="*")

    return flask_app
