import os

basedir = os.path.abspath(os.path.dirname(__file__))
default_db_path = "sqlite:///" + os.path.join(basedir, "app.db")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    WTF_CSRF_ENABLED = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or default_db_path
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email reminder settings. Disabled by default for safety.
    EMAIL_REMINDERS_ENABLED = os.environ.get("EMAIL_REMINDERS_ENABLED", "false").lower() == "true"
    EMAIL_REMINDERS_DRY_RUN = os.environ.get("EMAIL_REMINDERS_DRY_RUN", "true").lower() == "true"

    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER") or os.environ.get("MAIL_USERNAME")



class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
