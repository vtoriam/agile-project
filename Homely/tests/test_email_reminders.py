from datetime import datetime, timedelta

from app import db
from app.models import Task
from app.scheduler import format_due_task_email, send_due_task_email_reminders
from tests.conftest import create_user, create_household_with_member


def test_format_due_task_email_includes_user_and_task(app):
    user = create_user(display_name="Aisha")
    household, _ = create_household_with_member(user)

    task = Task(
        household_id=household.id,
        assigned_user_id=user.id,
        title="Pay electricity bill",
        category="bills",
        points_value=20,
        due_date=datetime.utcnow() + timedelta(hours=3),
        is_completed=False,
    )

    body = format_due_task_email(user, [task])

    assert "Hi Aisha" in body
    assert "Pay electricity bill" in body
    assert "20 pts" in body


def test_send_due_task_email_reminders_dry_run_counts_users(app):
    app.config["EMAIL_REMINDERS_DRY_RUN"] = True
    app.config["EMAIL_REMINDERS_ENABLED"] = False

    user = create_user(email="aisha@example.com", password="password123", display_name="Aisha")
    user.email_reminders_enabled = True
    db.session.commit()
    household, _ = create_household_with_member(user)

    due_soon = Task(
        household_id=household.id,
        assigned_user_id=user.id,
        title="Clean kitchen",
        category="kitchen",
        points_value=10,
        due_date=datetime.utcnow() + timedelta(hours=2),
        is_completed=False,
    )
    due_later = Task(
        household_id=household.id,
        assigned_user_id=user.id,
        title="Clean garage",
        category="cleaning",
        points_value=15,
        due_date=datetime.utcnow() + timedelta(days=3),
        is_completed=False,
    )
    completed = Task(
        household_id=household.id,
        assigned_user_id=user.id,
        title="Already completed",
        category="cleaning",
        points_value=5,
        due_date=datetime.utcnow() + timedelta(hours=4),
        is_completed=True,
    )

    db.session.add_all([due_soon, due_later, completed])
    db.session.commit()

    sent_count = send_due_task_email_reminders(app)

    assert sent_count == 1
