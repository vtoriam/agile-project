from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login
from flask_login import UserMixin


class Household(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    join_code = db.Column(db.String(20), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    memberships = db.relationship(
        "Membership",
        back_populates="household",
        cascade="all, delete-orphan"
    )

    tasks = db.relationship(
        "Task",
        back_populates="household",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Household {self.name}>"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    display_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.String(50), default="avatar1")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    memberships = db.relationship(
        "Membership",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    assigned_tasks = db.relationship(
        "Task",
        back_populates="assignee",
        foreign_keys="Task.assigned_user_id"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class Membership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    role = db.Column(db.String(30), default="member")
    points = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="memberships")
    household = db.relationship("Household", back_populates="memberships")

    __table_args__ = (
        db.UniqueConstraint("user_id", "household_id", name="uq_user_household"),
    )

    def __repr__(self):
        return f"<Membership user={self.user_id} household={self.household_id}>"


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    assigned_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), default="other")
    points_value = db.Column(db.Integer, default=10)

    due_date = db.Column(db.DateTime, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    household = db.relationship("Household", back_populates="tasks")
    assignee = db.relationship("User", back_populates="assigned_tasks", foreign_keys=[assigned_user_id])

    def __repr__(self):
        return f"<Task {self.title}>"

@login.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)

def create_sample_data():
    # Create sample users
    user1 = User(full_name="Aisha Khan", display_name="Aisha", email="aisha@example.com")
    user2 = User(full_name="Jordan Khan", display_name="Jordan", email="jordan@example.com")
    user3 = User(full_name="Mohammad Khan", display_name="Mohammad", email="mohammad@example.com")

    user1.set_password("password123")
    user2.set_password("password123")
    user3.set_password("password123")

    db.session.add_all([user1, user2, user3])
    db.session.commit()

    # Create sample household
    household = Household(name="Khan Family", join_code="HM-72QA")
    db.session.add(household)
    db.session.commit()

    # Create memberships
    membership1 = Membership(user_id=user1.id, household_id=household.id, role="Admin", points=120, streak=5)
    membership2 = Membership(user_id=user2.id, household_id=household.id, role="Member", points=95, streak=3)
    membership3 = Membership(user_id=user3.id, household_id=household.id, role="Member", points=80, streak=2)

    db.session.add_all([membership1, membership2, membership3])
    db.session.commit()