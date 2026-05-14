from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect

from app.config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_class)

    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    login.init_app(flask_app)

    from app.blueprints import main
    from app import routes, models

# Enable CSRF protection for the app
csrf = CSRFProtect(app)

login = LoginManager(app)
login.login_view = 'login'
    flask_app.register_blueprint(main)

    if not flask_app.config.get("TESTING"):
        from app.scheduler import start_scheduler
        start_scheduler(flask_app)

    return flask_app
