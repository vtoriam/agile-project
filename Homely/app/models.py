from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login
from flask_login import UserMixin


def utc_now():
    return datetime.now(timezone.utc)


class Household(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

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

    invites = db.relationship(
        "HouseholdInvite",
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

    point_transactions = db.relationship(
        "PointTransaction",
        back_populates="household",
        cascade="all, delete-orphan"
    )

    def ranked_members(self):
        """Return household memberships ordered by points for leaderboard display.

        We do not store a separate leaderboard table because rank can be
        calculated from Membership.points whenever the leaderboard is shown.
        """
        return Membership.query.filter_by(
            household_id=self.id
        ).order_by(
            Membership.points.desc(),
            Membership.joined_at.asc()
        ).all()

    def __repr__(self):
        return f"<Household {self.name}>"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    display_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.String(50), default="avatar1")
    created_at = db.Column(db.DateTime, default=utc_now)

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

    created_invites = db.relationship(
        "HouseholdInvite",
        back_populates="created_by",
        foreign_keys="HouseholdInvite.created_by_user_id"
    )

    reward_redemptions = db.relationship(
        "RewardRedemption",
        back_populates="user",
        cascade="all, delete-orphan"
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
    joined_at = db.Column(db.DateTime, default=utc_now)
    last_overdue_popup = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", back_populates="memberships")
    household = db.relationship("Household", back_populates="memberships")

    __table_args__ = (
        db.UniqueConstraint("user_id", "household_id", name="uq_user_household"),
    )

    def rank(self):
        """Return this member's current rank within their household."""
        members = self.household.ranked_members()

        for position, member in enumerate(members, start=1):
            if member.id == self.id:
                return position

        return None

    def __repr__(self):
        return f"<Membership user={self.user_id} household={self.household_id}>"


class HouseholdInvite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    household = db.relationship("Household", back_populates="invites")
    created_by = db.relationship(
        "User",
        back_populates="created_invites",
        foreign_keys=[created_by_user_id]
    )

    def is_valid(self):
        """Return whether this invite code can currently be used."""
        now = utc_now()
        expires_at = self.expires_at

        if expires_at is not None and expires_at.tzinfo is None:
            now = now.replace(tzinfo=None)

        return self.is_active and expires_at is not None and now < expires_at

    def __repr__(self):
        return f"<HouseholdInvite {self.code}>"


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    assigned_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), default="other")
    points_value = db.Column(db.Integer, default=10)

    # status supports wider UI states such as todo/assigned/completed.
    # is_completed is kept because existing routes and scheduler logic use it.
    status = db.Column(db.String(30), default="todo")
    icon = db.Column(db.String(50), default="clipboard-list")

    due_date = db.Column(db.DateTime, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

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


class Reward(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    points_required = db.Column(db.Integer, nullable=False)
    icon = db.Column(db.String(50), default="gift")

    # Allows a household to hide/disable a reward without deleting redemption history.
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    household = db.relationship("Household", back_populates="rewards")
    redemptions = db.relationship(
        "RewardRedemption",
        back_populates="reward",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Reward {self.name}>"


class RewardRedemption(db.Model):
    """Records when a user spends points on a reward.

    This is separate from Reward because one reward can be redeemed many times
    by different users. Keeping redemptions in their own table also lets the
    app track pending/approved/declined reward requests without changing the
    original reward definition.
    """

    id = db.Column(db.Integer, primary_key=True)
    reward_id = db.Column(db.Integer, db.ForeignKey("reward.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    points_spent = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), default="pending")
    redeemed_at = db.Column(db.DateTime, default=utc_now)

    reward = db.relationship("Reward", back_populates="redemptions")
    user = db.relationship("User", back_populates="reward_redemptions")
    household = db.relationship("Household", back_populates="reward_redemptions")
    point_transactions = db.relationship(
        "PointTransaction",
        back_populates="reward_redemption"
    )

    def __repr__(self):
        return f"<RewardRedemption reward={self.reward_id} user={self.user_id}>"


class PointTransaction(db.Model):
    """Ledger of point changes for each household member.

    This table records why points changed, such as completing a task or
    redeeming a reward. It gives the app an audit trail instead of only storing
    the current total on Membership.points.
    """

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=True)
    reward_redemption_id = db.Column(db.Integer, db.ForeignKey("reward_redemption.id"), nullable=True)
    points_delta = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    user = db.relationship("User", back_populates="point_transactions")
    household = db.relationship("Household", back_populates="point_transactions")
    task = db.relationship("Task", back_populates="point_transactions")
    reward_redemption = db.relationship(
        "RewardRedemption",
        back_populates="point_transactions"
    )

    def __repr__(self):
        return f"<PointTransaction user={self.user_id} points={self.points_delta}>"


@login.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


def create_sample_data():
    if User.query.filter_by(email="aisha@example.com").first():
        return

    user1 = User(full_name="Aisha Khan", display_name="Aisha", email="aisha@example.com")
    user2 = User(full_name="Jordan Khan", display_name="Jordan", email="jordan@example.com")
    user3 = User(full_name="Mohammad Khan", display_name="Mohammad", email="mohammad@example.com")

    user1.set_password("password123")
    user2.set_password("password123")
    user3.set_password("password123")

    db.session.add_all([user1, user2, user3])
    db.session.commit()

    household = Household(name="Khan Family")
    db.session.add(household)
    db.session.commit()

    membership1 = Membership(user_id=user1.id, household_id=household.id, role="Admin", points=120)
    membership2 = Membership(user_id=user2.id, household_id=household.id, role="Member", points=95)
    membership3 = Membership(user_id=user3.id, household_id=household.id, role="Member", points=80)

    db.session.add_all([membership1, membership2, membership3])
    db.session.commit()

    now = utc_now()
    d = lambda days: now - timedelta(days=days)

    sample_tasks = [
        Task(household_id=household.id, assigned_user_id=user1.id, title="Vacuum living room", category="cleaning", points_value=15, is_completed=True, due_date=d(12), completed_at=d(13), status="completed", icon="sparkles"),
        Task(household_id=household.id, assigned_user_id=user1.id, title="Take out bins", category="trash", points_value=10, is_completed=True, due_date=d(9), completed_at=d(10), status="completed", icon="trash-2"),
        Task(household_id=household.id, assigned_user_id=user1.id, title="Wipe kitchen counters", category="kitchen", points_value=10, is_completed=True, due_date=d(7), completed_at=d(8), status="completed", icon="utensils"),
        Task(household_id=household.id, assigned_user_id=user1.id, title="Clean bathroom", category="bathroom", points_value=20, is_completed=True, due_date=d(5), completed_at=d(6), status="completed", icon="sparkles"),
        Task(household_id=household.id, assigned_user_id=user1.id, title="Grocery run", category="shopping", points_value=15, is_completed=True, due_date=d(3), completed_at=d(4), status="completed", icon="shopping-cart"),
        Task(household_id=household.id, assigned_user_id=user1.id, title="Mop floors", category="cleaning", points_value=15, is_completed=True, due_date=d(8), completed_at=d(6), status="completed", icon="sparkles"),
        Task(household_id=household.id, assigned_user_id=user1.id, title="Organise pantry", category="kitchen", points_value=20, is_completed=True, due_date=d(14), completed_at=d(11), status="completed", icon="utensils"),
        Task(household_id=household.id, assigned_user_id=user1.id, title="Water the plants", category="garden", points_value=5, is_completed=False, due_date=d(2), completed_at=None, status="todo", icon="leaf"),
        Task(household_id=household.id, assigned_user_id=user2.id, title="Do the laundry", category="laundry", points_value=15, is_completed=True, due_date=d(10), completed_at=d(11), status="completed", icon="shirt"),
        Task(household_id=household.id, assigned_user_id=user2.id, title="Clean the hob", category="kitchen", points_value=10, is_completed=True, due_date=d(7), completed_at=d(8), status="completed", icon="utensils"),
        Task(household_id=household.id, assigned_user_id=user2.id, title="Empty dishwasher", category="kitchen", points_value=5, is_completed=True, due_date=d(4), completed_at=d(5), status="completed", icon="utensils"),
        Task(household_id=household.id, assigned_user_id=user2.id, title="Wipe bathroom mirror", category="bathroom", points_value=5, is_completed=True, due_date=d(6), completed_at=d(7), status="completed", icon="sparkles"),
        Task(household_id=household.id, assigned_user_id=user2.id, title="Fix leaky tap", category="repairs", points_value=25, is_completed=True, due_date=d(11), completed_at=d(9), status="completed", icon="wrench"),
        Task(household_id=household.id, assigned_user_id=user2.id, title="Sort recycling", category="trash", points_value=5, is_completed=False, due_date=d(1), completed_at=None, status="todo", icon="recycle"),
        Task(household_id=household.id, assigned_user_id=user3.id, title="Sweep the patio", category="garden", points_value=10, is_completed=True, due_date=d(9), completed_at=d(10), status="completed", icon="leaf"),
        Task(household_id=household.id, assigned_user_id=user3.id, title="Clean fridge", category="kitchen", points_value=15, is_completed=True, due_date=d(5), completed_at=d(6), status="completed", icon="utensils"),
        Task(household_id=household.id, assigned_user_id=user3.id, title="Replace light bulb", category="repairs", points_value=5, is_completed=True, due_date=d(13), completed_at=d(10), status="completed", icon="lightbulb"),
        Task(household_id=household.id, assigned_user_id=user3.id, title="Deep clean oven", category="kitchen", points_value=20, is_completed=True, due_date=d(15), completed_at=d(12), status="completed", icon="utensils"),
    ]
    db.session.add_all(sample_tasks)
    db.session.commit()

    rewards = [
        Reward(household_id=household.id, name="Skip one chore", description="Redeem this reward to skip one normal chore.", points_required=100, icon="ticket"),
        Reward(household_id=household.id, name="Choose takeaway", description="Choose the next household takeaway meal.", points_required=150, icon="utensils"),
        Reward(household_id=household.id, name="Pick movie night", description="Choose the next household movie.", points_required=75, icon="clapperboard"),
    ]
    db.session.add_all(rewards)
    db.session.commit()

    invite = HouseholdInvite(
        household_id=household.id,
        created_by_user_id=user1.id,
        code="HM-SAMPLE",
        expires_at=utc_now() + timedelta(days=7),
    )
    db.session.add(invite)
    db.session.commit()

    point_transactions = [
        PointTransaction(
            user_id=task.assigned_user_id,
            household_id=household.id,
            task_id=task.id,
            points_delta=task.points_value,
            reason=f"Completed task: {task.title}"
        )
        for task in sample_tasks
        if task.is_completed and task.assigned_user_id is not None
    ]
    db.session.add_all(point_transactions)
    db.session.commit()