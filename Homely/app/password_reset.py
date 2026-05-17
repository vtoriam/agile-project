from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from flask import current_app

RESET_SALT = "homely-password-reset"
RESET_MAX_AGE_SECONDS = 3600


def _serializer():
    """Create a serializer using the Flask secret key."""
    secret_key = current_app.config.get("SECRET_KEY") or "dev-secret-key"
    return URLSafeTimedSerializer(secret_key)


def generate_password_reset_token(user):
    """Create a signed password reset token for a user."""
    return _serializer().dumps(
        {
            "user_id": user.id,
            "email": user.email,
        },
        salt=RESET_SALT,
    )


def verify_password_reset_token(token, max_age=RESET_MAX_AGE_SECONDS):
    """Return the matching user if the reset token is valid, otherwise None."""
    from app import db
    from app.models import User

    try:
        data = _serializer().loads(
            token,
            salt=RESET_SALT,
            max_age=max_age,
        )
    except (SignatureExpired, BadSignature):
        return None

    user = db.session.get(User, data.get("user_id"))

    if not user:
        return None

    if user.email != data.get("email"):
        return None

    return user