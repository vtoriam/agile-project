from datetime import datetime, timedelta, timezone

from app import db
from app.models import Task, Membership, RewardClaim
from tests.conftest import create_user, create_household_with_member, login


def utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def test_home_requires_login(client):
    response = client.get("/home")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_login_success_redirects_to_home(client, app):
    create_user(email="aisha@example.com", password="password123")

    response = login(client)

    assert response.status_code == 302
    assert "/home" in response.headers["Location"]


def test_login_failure_shows_error(client, app):
    create_user(email="aisha@example.com", password="password123")

    response = client.post(
        "/login",
        data={"email": "aisha@example.com", "password": "wrong"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Invalid email or password" in response.data


def test_create_task_adds_task_to_user_household(client, app):
    user = create_user()
    household, _ = create_household_with_member(user)
    login(client)

    response = client.post(
        "/tasks/create",
        json={
            "text": "Clean kitchen",
            "cat": "kitchen",
            "assignedTo": user.display_name,
            "points": 20,
            "due": (utcnow_naive() + timedelta(days=1)).isoformat(),
        },
    )

    assert response.status_code == 201

    task = Task.query.filter_by(title="Clean kitchen").first()
    assert task is not None
    assert task.household_id == household.id
    assert task.assigned_user_id == user.id
    assert task.points_value == 20


def test_toggle_task_marks_task_complete_and_adds_points(client, app):
    user = create_user()
    household, membership = create_household_with_member(user, points=0)

    task = Task(
        household_id=household.id,
        assigned_user_id=user.id,
        title="Take out bins",
        category="trash",
        points_value=10,
        is_completed=False,
    )
    db.session.add(task)
    db.session.commit()

    login(client)
    response = client.post(f"/tasks/{task.id}/toggle")

    assert response.status_code == 200

    db.session.refresh(task)
    db.session.refresh(membership)

    assert task.is_completed
    assert membership.points == 10


def test_toggle_task_steals_points_from_assignee_when_completed_by_other_user(client, app):
    assignee = create_user(email="aisha@example.com", password="password123", display_name="Aisha")
    household, assignee_membership = create_household_with_member(assignee, points=0)

    stealer = create_user(email="jordan@example.com", password="password123", display_name="Jordan")
    stealer_membership = Membership(user_id=stealer.id, household_id=household.id, role="Member", points=0)
    db.session.add(stealer_membership)
    db.session.commit()

    task = Task(
        household_id=household.id,
        assigned_user_id=assignee.id,
        title="Take out bins",
        category="trash",
        points_value=10,
        is_completed=False,
    )
    db.session.add(task)
    db.session.commit()

    login(client, email="jordan@example.com", password="password123")
    response = client.post(f"/tasks/{task.id}/toggle")

    assert response.status_code == 200
    assert response.get_json()["message"] == "You stole 10 points from Aisha!"

    db.session.refresh(task)
    db.session.refresh(assignee_membership)
    db.session.refresh(stealer_membership)

    assert task.is_completed
    assert task.points_awarded_to_user_id == stealer.id
    assert assignee_membership.points == 0
    assert stealer_membership.points == 10

    response = client.post(f"/tasks/{task.id}/toggle")

    assert response.status_code == 200

    db.session.refresh(task)
    db.session.refresh(assignee_membership)
    db.session.refresh(stealer_membership)

    assert not task.is_completed
    assert stealer_membership.points == 0
    assert assignee_membership.points == 0


def test_task_reminders_returns_only_current_user_due_soon_tasks(client, app):
    user = create_user(email="aisha@example.com", password="password123", display_name="Aisha")
    household, _ = create_household_with_member(user)

    other_user = create_user(email="jordan@example.com", password="password123", display_name="Jordan")
    db.session.add(Membership(user_id=other_user.id, household_id=household.id, role="Member", points=0))
    db.session.commit()

    now = utcnow_naive()

    due_soon = Task(
        household_id=household.id,
        assigned_user_id=user.id,
        title="Pay power bill",
        category="bills",
        points_value=20,
        due_date=now + timedelta(hours=2),
        is_completed=False,
    )
    due_later = Task(
        household_id=household.id,
        assigned_user_id=user.id,
        title="Clean garage",
        category="cleaning",
        points_value=15,
        due_date=now + timedelta(days=3),
        is_completed=False,
    )
    overdue = Task(
        household_id=household.id,
        assigned_user_id=user.id,
        title="Overdue bins",
        category="trash",
        points_value=10,
        due_date=now - timedelta(hours=1),
        is_completed=False,
    )
    other_user_task = Task(
        household_id=household.id,
        assigned_user_id=other_user.id,
        title="Jordan due soon",
        category="kitchen",
        points_value=10,
        due_date=now + timedelta(hours=3),
        is_completed=False,
    )
    completed_task = Task(
        household_id=household.id,
        assigned_user_id=user.id,
        title="Already done",
        category="cleaning",
        points_value=5,
        due_date=now + timedelta(hours=4),
        is_completed=True,
    )

    db.session.add_all([due_soon, due_later, overdue, other_user_task, completed_task])
    db.session.commit()

    login(client, email="aisha@example.com", password="password123")
    response = client.get("/tasks/reminders")

    assert response.status_code == 200
    data = response.get_json()

    assert data["count"] == 1
    assert data["windowHours"] == 24
    assert data["tasks"][0]["text"] == "Pay power bill"
    assert data["tasks"][0]["points"] == 20


def test_reward_claim_persists_across_sessions(client, app):
    user = create_user(email="aisha@example.com", password="password123", display_name="Aisha")
    household, membership = create_household_with_member(user, points=1200)
    user.current_household = household.id
    db.session.commit()

    login(client, email="aisha@example.com", password="password123")
    response = client.post("/rewards/claim/skip-your-chore")

    assert response.status_code == 200
    assert response.get_json()["claimed"] is True

    db.session.refresh(membership)
    assert db.session.query(RewardClaim).filter_by(
        user_id=user.id,
        household_id=household.id,
        reward_key="skip-your-chore",
    ).count() == 1

    fresh_client = app.test_client()
    login(fresh_client, email="aisha@example.com", password="password123")
    rewards_response = fresh_client.get("/rewards")

    assert rewards_response.status_code == 200
    assert b'data-reward-key="skip-your-chore"' in rewards_response.data
    assert b"status-claimed" in rewards_response.data


def test_email_reminder_toggle_updates_user_preference(client, app):
    user = create_user(email="aisha@example.com", password="password123")
    create_household_with_member(user)

    assert not user.email_reminders_enabled

    login(client, email="aisha@example.com", password="password123")
    response = client.post("/email-reminders/toggle", follow_redirects=False)

    assert response.status_code == 302

    db.session.refresh(user)
    assert user.email_reminders_enabled

    response = client.post("/email-reminders/toggle", follow_redirects=False)

    assert response.status_code == 302

    db.session.refresh(user)
    assert not user.email_reminders_enabled


def test_delete_task_removes_task_from_database(client, app):
    user = create_user()
    household, _ = create_household_with_member(user)

    task = Task(
        household_id=household.id,
        assigned_user_id=user.id,
        title="Delete me",
        category="cleaning",
        points_value=10,
        is_completed=False,
    )
    db.session.add(task)
    db.session.commit()

    task_id = task.id

    login(client)
    response = client.delete(f"/tasks/{task_id}")

    assert response.status_code == 200
    assert response.get_json()["success"] is True
    assert db.session.get(Task, task_id) is None
