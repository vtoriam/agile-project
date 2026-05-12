from app import db
from app.models import HouseholdInvite
from tests.conftest import create_user, create_household_with_member, create_invite


def test_user_password_is_hashed(app):
    user = create_user(password="secret123")

    assert user.password_hash != "secret123"
    assert user.check_password("secret123")
    assert not user.check_password("wrong-password")


def test_household_membership_links_user_to_household(app):
    user = create_user()
    household, membership = create_household_with_member(user, role="Admin", points=50)

    assert membership.user_id == user.id
    assert membership.household_id == household.id
    assert membership.role == "Admin"
    assert membership.points == 50


def test_invite_code_valid_when_active_and_not_expired(app):
    user = create_user()
    household, _ = create_household_with_member(user)

    invite = create_invite(household, user, code="HM-TEST", days_valid=1, is_active=True)

    assert invite.is_valid()


def test_invite_code_invalid_when_expired(app):
    user = create_user()
    household, _ = create_household_with_member(user)

    invite = create_invite(household, user, code="HM-OLD", days_valid=-1, is_active=True)

    assert not invite.is_valid()


def test_invite_code_invalid_when_inactive(app):
    user = create_user()
    household, _ = create_household_with_member(user)

    invite = create_invite(household, user, code="HM-OFF", days_valid=1, is_active=False)

    assert not invite.is_valid()
