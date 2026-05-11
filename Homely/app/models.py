from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login
from flask_login import UserMixin


class Household(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

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

    def __repr__(self):
        return f"<Household {self.name}>"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    display_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.String(50), default="avatar1")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

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
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_overdue_popup = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", back_populates="memberships")
    household = db.relationship("Household", back_populates="memberships")

    __table_args__ = (
        db.UniqueConstraint("user_id", "household_id", name="uq_user_household"),
    )

    def __repr__(self):
        return f"<Membership user={self.user_id} household={self.household_id}>"

class HouseholdInvite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    household = db.relationship("Household", back_populates="invites")
    created_by = db.relationship(
        "User",
        back_populates="created_invites",
        foreign_keys=[created_by_user_id]
    )

    def is_valid(self):
        return self.is_active and datetime.utcnow() < self.expires_at
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

    due_date = db.Column(db.DateTime, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

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
    household = Household(name="Khan Family")
    db.session.add(household)
    db.session.commit()

    # Create memberships
    membership1 = Membership(user_id=user1.id, household_id=household.id, role="Admin", points=120)
    membership2 = Membership(user_id=user2.id, household_id=household.id, role="Member", points=95)
    membership3 = Membership(user_id=user3.id, household_id=household.id, role="Member", points=80)

    db.session.add_all([membership1, membership2, membership3])
    db.session.commit()

    now = datetime.now(timezone.utc)
    d = lambda days: now - timedelta(days=days)

    # Sample tasks: mix of on-time completions and late completions
    sample_tasks = [
        # Aisha — 7 completed (5 on time, 2 late), 1 pending overdue
        Task(household_id=household.id, assigned_user_id=user1.id, title="Vacuum living room",     category="cleaning",  points_value=15, is_completed=True,  due_date=d(12), completed_at=d(13)),
        Task(household_id=household.id, assigned_user_id=user1.id, title="Take out bins",          category="trash",     points_value=10, is_completed=True,  due_date=d(9),  completed_at=d(10)),
        Task(household_id=household.id, assigned_user_id=user1.id, title="Wipe kitchen counters",  category="kitchen",   points_value=10, is_completed=True,  due_date=d(7),  completed_at=d(8)),
        Task(household_id=household.id, assigned_user_id=user1.id, title="Clean bathroom",         category="bathroom",  points_value=20, is_completed=True,  due_date=d(5),  completed_at=d(6)),
        Task(household_id=household.id, assigned_user_id=user1.id, title="Grocery run",            category="shopping",  points_value=15, is_completed=True,  due_date=d(3),  completed_at=d(4)),
        Task(household_id=household.id, assigned_user_id=user1.id, title="Mop floors",             category="cleaning",  points_value=15, is_completed=True,  due_date=d(8),  completed_at=d(6)),   # late
        Task(household_id=household.id, assigned_user_id=user1.id, title="Organise pantry",        category="kitchen",   points_value=20, is_completed=True,  due_date=d(14), completed_at=d(11)),  # late
        Task(household_id=household.id, assigned_user_id=user1.id, title="Water the plants",       category="garden",    points_value=5,  is_completed=False, due_date=d(2),  completed_at=None),   # overdue

        # Jordan — 5 completed (4 on time, 1 late), 1 pending overdue
        Task(household_id=household.id, assigned_user_id=user2.id, title="Do the laundry",         category="laundry",   points_value=15, is_completed=True,  due_date=d(10), completed_at=d(11)),
        Task(household_id=household.id, assigned_user_id=user2.id, title="Clean the hob",          category="kitchen",   points_value=10, is_completed=True,  due_date=d(7),  completed_at=d(8)),
        Task(household_id=household.id, assigned_user_id=user2.id, title="Empty dishwasher",       category="kitchen",   points_value=5,  is_completed=True,  due_date=d(4),  completed_at=d(5)),
        Task(household_id=household.id, assigned_user_id=user2.id, title="Wipe bathroom mirror",   category="bathroom",  points_value=5,  is_completed=True,  due_date=d(6),  completed_at=d(7)),
        Task(household_id=household.id, assigned_user_id=user2.id, title="Fix leaky tap",          category="repairs",   points_value=25, is_completed=True,  due_date=d(11), completed_at=d(9)),   # late
        Task(household_id=household.id, assigned_user_id=user2.id, title="Sort recycling",         category="trash",     points_value=5,  is_completed=False, due_date=d(1),  completed_at=None),   # overdue

        # Mohammad — 4 completed (2 on time, 2 late)
        Task(household_id=household.id, assigned_user_id=user3.id, title="Sweep the patio",        category="garden",    points_value=10, is_completed=True,  due_date=d(9),  completed_at=d(10)),
        Task(household_id=household.id, assigned_user_id=user3.id, title="Clean fridge",           category="kitchen",   points_value=15, is_completed=True,  due_date=d(5),  completed_at=d(6)),
        Task(household_id=household.id, assigned_user_id=user3.id, title="Replace light bulb",     category="repairs",   points_value=5,  is_completed=True,  due_date=d(13), completed_at=d(10)),  # late
        Task(household_id=household.id, assigned_user_id=user3.id, title="Deep clean oven",        category="kitchen",   points_value=20, is_completed=True,  due_date=d(15), completed_at=d(12)),  # late
    ]
    db.session.add_all(sample_tasks)
    db.session.commit()

    # Create a sample invite code
    invite = HouseholdInvite(
        household_id=household.id,
        created_by_user_id=user1.id,
        code="HM-SAMPLE",
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.session.add(invite)
    db.session.commit()