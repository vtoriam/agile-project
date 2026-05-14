from datetime import datetime, timedelta

import pytest

from app import create_app, db
from app.config import TestingConfig
from app.models import User, Household, Membership, HouseholdInvite


@pytest.fixture()
def app():
    test_app = create_app(TestingConfig)

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def create_user(email="aisha@example.com", password="password123", display_name="Aisha"):
    user = User(
        full_name=f"{display_name} Khan",
        display_name=display_name,
        email=email,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def create_household_with_member(user, role="Admin", points=0):
    household = Household(name="Test Household")
    db.session.add(household)
    db.session.commit()

    membership = Membership(
        user_id=user.id,
        household_id=household.id,
        role=role,
        points=points,
    )
    db.session.add(membership)
    db.session.commit()

    return household, membership


def create_invite(household, user, code="HM-TEST", days_valid=1, is_active=True):
    invite = HouseholdInvite(
        household_id=household.id,
        created_by_user_id=user.id,
        code=code,
        expires_at=datetime.utcnow() + timedelta(days=days_valid),
        is_active=is_active,
    )
    db.session.add(invite)
    db.session.commit()
    return invite


def login(client, email="aisha@example.com", password="password123"):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )
