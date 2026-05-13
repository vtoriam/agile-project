from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from app.config import Config
from flask_login import LoginManager
from flask_wtf import CSRFProtect

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Enable CSRF protection for the app
csrf = CSRFProtect(app)

login = LoginManager(app)
login.login_view = 'login'

from app import routes, models

from app.scheduler import start_scheduler
scheduler = start_scheduler(app)