from datetime import datetime, timedelta

from app import db
from app.models import Task
from tests.conftest import create_user, create_household_with_member, login


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
            "due": (datetime.utcnow() + timedelta(days=1)).isoformat(),
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
