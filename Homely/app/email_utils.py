from email.message import EmailMessage
import smtplib


def email_reminders_configured(app):
    """Return whether SMTP settings are present for real email delivery."""
    required_values = [
        app.config.get("MAIL_SERVER"),
        app.config.get("MAIL_USERNAME"),
        app.config.get("MAIL_PASSWORD"),
        app.config.get("MAIL_DEFAULT_SENDER"),
    ]
    return all(required_values)


def send_email(app, recipient, subject, body):
    """Send an email if SMTP is configured, otherwise run in safe dry-run mode.

    Dry-run mode is enabled by default so the app can be demonstrated and tested
    without committing real email credentials to the repository.
    """
    dry_run = app.config.get("EMAIL_REMINDERS_DRY_RUN", True)
    enabled = app.config.get("EMAIL_REMINDERS_ENABLED", False)

    if dry_run:
        print("[Email reminder dry-run]")
        print(f"To: {recipient}")
        print(f"Subject: {subject}")
        print(body)
        return True

    if not enabled:
        print("[Email reminders disabled]")
        return False

    if not email_reminders_configured(app):
        print("[Email reminders not sent: SMTP settings missing]")
        return False

    message = EmailMessage()
    message["From"] = app.config["MAIL_DEFAULT_SENDER"]
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]) as server:
        if app.config.get("MAIL_USE_TLS", True):
            server.starttls()
        server.login(app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
        server.send_message(message)

    return True
