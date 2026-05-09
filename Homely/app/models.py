from datetime import datetime, timedelta
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

    rewards = db.relationship(
        "Reward",
        back_populates="household",
        cascade="all, delete-orphan"
    )

    reward_redemptions = db.relationship(
        "RewardRedemption",
        back_populates="household",
        cascade="all, delete-orphan"
    )

    invites = db.relationship(
        "HouseholdInvite",
        back_populates="household",
        cascade="all, delete-orphan"
    )

    point_transactions = db.relationship(
        "PointTransaction",
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

    reward_redemptions = db.relationship(
        "RewardRedemption",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    created_invites = db.relationship(
        "HouseholdInvite",
        back_populates="created_by"
    )

    point_transactions = db.relationship(
        "PointTransaction",
        back_populates="user",
        cascade="all, delete-orphan"
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

    status = db.Column(db.String(30), default="todo")
    icon = db.Column(db.String(50), default="clipboard-list")
    due_date = db.Column(db.DateTime, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    household = db.relationship("Household", back_populates="tasks")
    assignee = db.relationship(
        "User",
        back_populates="assigned_tasks",
        foreign_keys=[assigned_user_id]
    )

    point_transactions = db.relationship(
        "PointTransaction",
        back_populates="task"
    )

    def __repr__(self):
        return f"<Task {self.title}>"


class HouseholdInvite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    household = db.relationship("Household", back_populates="invites")
    created_by = db.relationship("User", back_populates="created_invites")

    def is_valid(self):
        return self.is_active and datetime.utcnow() < self.expires_at

    def __repr__(self):
        return f"<HouseholdInvite {self.code}>"


class Reward(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    points_required = db.Column(db.Integer, nullable=False)
    icon = db.Column(db.String(50), default="gift")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    household = db.relationship("Household", back_populates="rewards")
    redemptions = db.relationship(
        "RewardRedemption",
        back_populates="reward",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Reward {self.name}>"


class RewardRedemption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reward_id = db.Column(db.Integer, db.ForeignKey("reward.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    points_spent = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), default="pending")
    redeemed_at = db.Column(db.DateTime, default=datetime.utcnow)

    reward = db.relationship("Reward", back_populates="redemptions")
    user = db.relationship("User", back_populates="reward_redemptions")
    household = db.relationship("Household", back_populates="reward_redemptions")

    def __repr__(self):
        return f"<RewardRedemption reward={self.reward_id} user={self.user_id}>"


class PointTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=True)
    reward_redemption_id = db.Column(db.Integer, db.ForeignKey("reward_redemption.id"), nullable=True)
    points_delta = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="point_transactions")
    household = db.relationship("Household", back_populates="point_transactions")
    task = db.relationship("Task", back_populates="point_transactions")
    reward_redemption = db.relationship("RewardRedemption")

    def __repr__(self):
        return f"<PointTransaction user={self.user_id} points={self.points_delta}>"


@login.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def create_sample_data():
    if User.query.filter_by(email="aisha@example.com").first():
        return

    user1 = User(
        full_name="Aisha Khan",
        display_name="Aisha",
        email="aisha@example.com",
        avatar="avatar1"
    )
    user2 = User(
        full_name="Jordan Khan",
        display_name="Jordan",
        email="jordan@example.com",
        avatar="avatar2"
    )
    user3 = User(
        full_name="Mohammad Khan",
        display_name="Mohammad",
        email="mohammad@example.com",
        avatar="avatar3"
    )

    user1.set_password("password123")
    user2.set_password("password123")
    user3.set_password("password123")

    db.session.add_all([user1, user2, user3])
    db.session.commit()

    household = Household(name="Khan Family", join_code="HM-72QA")
    db.session.add(household)
    db.session.commit()

    membership1 = Membership(
        user_id=user1.id,
        household_id=household.id,
        role="Admin",
        points=120,
        streak=5
    )
    membership2 = Membership(
        user_id=user2.id,
        household_id=household.id,
        role="Member",
        points=95,
        streak=3
    )
    membership3 = Membership(
        user_id=user3.id,
        household_id=household.id,
        role="Member",
        points=80,
        streak=2
    )

    db.session.add_all([membership1, membership2, membership3])
    db.session.commit()

    task1 = Task(
        household_id=household.id,
        assigned_user_id=user1.id,
        title="Take out bins",
        description="Put bins outside before collection.",
        category="cleaning",
        points_value=20,
        status="todo",
        icon="trash-2"
    )
    task2 = Task(
        household_id=household.id,
        assigned_user_id=user2.id,
        title="Buy groceries",
        description="Pick up shared groceries for the household.",
        category="kitchen",
        points_value=30,
        status="todo",
        icon="shopping-cart"
    )

    reward1 = Reward(
        household_id=household.id,
        name="Skip one chore",
        description="Redeem this reward to skip one normal chore.",
        points_required=100,
        icon="ticket"
    )
    reward2 = Reward(
        household_id=household.id,
        name="Choose takeaway",
        description="Choose the next household takeaway meal.",
        points_required=150,
        icon="utensils"
    )

    invite = HouseholdInvite(
        household_id=household.id,
        created_by_user_id=user1.id,
        code="HM-72QA",
        expires_at=datetime.utcnow() + timedelta(days=7),
        is_active=True
    )

    db.session.add_all([task1, task2, reward1, reward2, invite])
    db.session.commit()

    transaction1 = PointTransaction(
        user_id=user1.id,
        household_id=household.id,
        task_id=task1.id,
        points_delta=20,
        reason="Sample task reward"
    )
    transaction2 = PointTransaction(
        user_id=user2.id,
        household_id=household.id,
        task_id=task2.id,
        points_delta=30,
        reason="Sample task reward"
    )

    db.session.add_all([transaction1, transaction2])
    db.session.commit()