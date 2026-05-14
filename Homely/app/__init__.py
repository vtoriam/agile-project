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


def create_app(config_class=Config):
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    csrf.init_app(flask_app)
    login.init_app(flask_app)
    login.login_view = 'login'

    # Register blueprints and import models
    from app.blueprints import main
    from app import routes, models

    flask_app.register_blueprint(main)

    # Start scheduler if not in testing mode
    if not flask_app.config.get("TESTING"):
        from app.scheduler import start_scheduler
        start_scheduler(flask_app)

    return flask_app
