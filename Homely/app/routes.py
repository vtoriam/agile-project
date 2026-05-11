import random
import string

from flask import render_template, redirect, url_for, request, session
from sqlalchemy import func

from app import app, db
from app.models import User, Household, Membership, Task, HouseholdInvite
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime, timedelta

@app.route("/index")
@login_required
def index():
    return render_template("index.html", title="Homely")


@app.route("/")
def root():
    return redirect(url_for("login"))


@app.route("/home")
@login_required
def home():
    membership = db.session.query(Membership).filter_by(user_id=current_user.id).first()
    members = (
        db.session.query(Membership)
        .filter_by(household_id=membership.household_id)
        .all()
        if membership else []
    )

    now = datetime.utcnow()

    # Find overdue tasks assigned to the current user
    overdue_tasks = db.session.query(Task).filter(
        Task.is_completed == False,
        Task.due_date != None,
        Task.due_date < now,
        Task.assigned_user_id == current_user.id,
    ).all() if membership else []

    overdue_count = len(overdue_tasks)

    # Calculate total points at risk (days overdue × 5 per task)
    total_points_lost = sum(
        max(0, (now - task.due_date).days) * 5
        for task in overdue_tasks
    )

    # Show popup if they have overdue tasks and haven't dismissed it today
    show_popup = False
    if overdue_count > 0 and membership:
        if membership.last_overdue_popup is None or \
           (now - membership.last_overdue_popup).total_seconds() > 86400:
            show_popup = True

    return render_template(
        "home.html",
        title="Home",
        members=members,
        overdue_count=overdue_count,
        total_points_lost=total_points_lost,
        show_popup=show_popup,
    )

@app.route("/dismiss-overdue-popup", methods=["POST"])
@login_required
def dismiss_overdue_popup():
    membership = db.session.query(Membership).filter_by(
        user_id=current_user.id
    ).first()
    if membership:
        membership.last_overdue_popup = datetime.utcnow()
        db.session.commit()
    return "", 204

@app.route("/dashboard")
@login_required
def dashboard():
    return redirect(url_for("home"))


@app.route("/my-tasks")
def my_tasks():
    return render_template("my-tasks.html", title="My Tasks")


@app.route("/leaderboard")
@login_required
def leaderboard():
    household = db.session.query(Household).first()
    member_stats = {}
    if household:
        members = db.session.query(Membership).filter_by(household_id=household.id).all()
        members.sort(key=lambda m: m.points, reverse=True)
        first = members[0] if len(members) > 0 else None
        second = members[1] if len(members) > 1 else None
        third = members[2] if len(members) > 2 else None
        other_members = members[3:] if len(members) > 3 else []

        rank_icons = ['crown', 'medal', 'award']
        rank_colors = ['#c49a2a', '#9e9087', '#b07248']
        for i, m in enumerate(members):
            done_tasks = db.session.query(Task).filter_by(
                household_id=household.id,
                assigned_user_id=m.user_id,
                is_completed=True,
            ).all()
            completed = len(done_tasks)
            on_time = sum(
                1 for t in done_tasks
                if t.completed_at and t.due_date and t.completed_at <= t.due_date
            )
            late = sum(
                1 for t in done_tasks
                if t.completed_at and t.due_date and t.completed_at > t.due_date
            )
            member_stats[m.user.display_name] = {
                'rank':      i + 1,
                'points':    m.points,
                'completed': completed,
                'on_time':   on_time,
                'late':      late,
                'avatar':    rank_icons[i] if i < 3 else 'user',
                'rankColor': rank_colors[i] if i < 3 else '#888888',
            }
    else:
        first = second = third = None
        other_members = []
    return render_template(
        "leaderboard.html",
        title="Leaderboard",
        first=first, second=second, third=third,
        other_members=other_members,
        member_stats=member_stats,
    )


@app.route("/edit-profile")
@login_required
def edit_profile():
    return render_template("edit-profile.html", title="Edit Profile")


@app.route("/rewards")
@login_required
def rewards():
    household = db.session.query(Household).first()
    current_membership = None
    user_points = 0
    household_rank = None
    household_points = 0

    if household:
        current_membership = db.session.query(Membership).filter_by(
            user_id=current_user.id,
            household_id=household.id,
        ).first()
        if current_membership:
            user_points = current_membership.points or 0

        household_points = (
            db.session.query(func.coalesce(func.sum(Membership.points), 0))
            .filter(Membership.household_id == household.id)
            .scalar()
            or 0
        )

        ranked_households = (
            db.session.query(
                Household.id.label("household_id"),
                func.coalesce(func.sum(Membership.points), 0).label("total_points"),
            )
            .outerjoin(Membership, Membership.household_id == Household.id)
            .group_by(Household.id)
            .all()
        )
        household_rank = (
            1
            + sum(
                1
                for item in ranked_households
                if item.total_points > household_points
            )
        )

    return render_template(
        "rewards.html",
        title="Rewards",
        user_points=user_points,
        current_membership=current_membership,
        household_rank=household_rank,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if not email or not password:
            error = "Please fill in all fields."
        user = db.session.query(User).filter_by(email=email).first()
        if not user or not user.check_password(request.form["password"]):
            error = "Invalid email or password."
        else:
            login_user(user)
            return redirect(url_for("home"))
    return render_template("login.html", title="Login", error=error)


@app.route("/logout", methods=["GET", "POST"])
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    form_data = {}
    if request.method == "POST":
        form_data = request.form.to_dict()
        if not all([
            form_data.get("first_name"),
            form_data.get("last_name"),
            form_data.get("display_name"),
            form_data.get("email"),
            form_data.get("password"),
        ]):
            error = "Please fill in all required fields."
        elif form_data.get("password") != form_data.get("confirm_password"):
            error = "Passwords do not match."
        elif db.session.query(User).filter_by(email=form_data["email"].strip().lower()).first():
            error = "An account with that email already exists."
        else:
            session["signup_data"] = {
                "first_name":    form_data["first_name"].strip(),
                "last_name":     form_data["last_name"].strip(),
                "display_name":  form_data["display_name"].strip(),
                "email":         form_data["email"].strip().lower(),
                "password":      form_data["password"],
            }
            return redirect(url_for("signup_household"))
    return render_template("signup.html", title="Sign Up", form_data=form_data, error=error)


@app.route("/signup/household")
@app.route("/signup-household")
def signup_household():
    if not session.get("signup_data"):
        return redirect(url_for("signup"))
    return render_template("signup_household.html", title="Household Setup")


@app.route("/signup/household/create", methods=["GET", "POST"])
def signup_create_household():
    signup_data = session.get("signup_data")
    if not signup_data:
        return redirect(url_for("signup"))

    error = None
    form_data = {}

    if request.method == "POST":
        form_data = request.form.to_dict()
        household_name = form_data.get("household_name", "").strip()

        if db.session.query(User).filter_by(email=signup_data["email"]).first():
            error = "An account with that email already exists. Please sign in."
        elif not household_name:
            error = "Please enter a household name."
        else:
            user = User(
                full_name=f"{signup_data['first_name']} {signup_data['last_name']}",
                display_name=signup_data["display_name"],
                email=signup_data["email"],
            )
            user.set_password(signup_data["password"])
            db.session.add(user)
            db.session.flush()

            household = Household(name=household_name)
            db.session.add(household)
            db.session.flush()

            first_invite = HouseholdInvite(
                household_id=household.id,
                created_by_user_id=user.id,
                code="HM-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=4)),
                expires_at=datetime.utcnow() + timedelta(days=7),
                is_active=True,
            )
            db.session.add(first_invite)

            db.session.add(Membership(
                user_id=user.id,
                household_id=household.id,
                role=form_data.get("role", "Admin"),
                points=0,
            ))
            db.session.commit()
            session.pop("signup_data", None)
            login_user(user)
            return redirect(url_for("home"))

    return render_template(
        "signup_create_household.html",
        title="Create Household",
        form_data=form_data,
        error=error,
    )


@app.route("/signup/household/join", methods=["GET", "POST"])
def signup_join_household():
    signup_data = session.get("signup_data")
    if not signup_data:
        return redirect(url_for("signup"))

    error = None
    form_data = {}

    if request.method == "POST":
        form_data = request.form.to_dict()
        join_code = form_data.get("join_code", "").strip().upper()

        if db.session.query(User).filter_by(email=signup_data["email"]).first():
            error = "An account with that email already exists. Please sign in."
        elif not join_code:
            error = "Please enter an invite code."
        else:
            invite = db.session.query(HouseholdInvite).filter_by(
                code=join_code
            ).first()

            if not invite:
                error = "No household found with that code. Check the code and try again."
            elif not invite.is_valid():
                error = "This invite code has expired or been deactivated. Ask an admin to regenerate it."
            else:
                user = User(
                    full_name=f"{signup_data['first_name']} {signup_data['last_name']}",
                    display_name=signup_data["display_name"],
                    email=signup_data["email"],
                )
                user.set_password(signup_data["password"])
                db.session.add(user)
                db.session.flush()

                db.session.add(Membership(
                    user_id=user.id,
                    household_id=invite.household_id,
                    role="Member",
                    points=0,
                ))
                db.session.commit()
                session.pop("signup_data", None)
                login_user(user)
                return redirect(url_for("home"))

    return render_template(
        "signup_join_household.html",
        title="Join Household",
        form_data=form_data,
        error=error,
    )


@app.route("/household/manage")
@app.route("/manage-household")
@login_required
def manage_household():
    household = db.session.query(Household).filter(
        Household.id == db.session.query(Membership.household_id).filter_by(
            user_id=current_user.id
        ).scalar_subquery()
    ).first()

    current_membership = db.session.query(Membership).filter_by(
        user_id=current_user.id,
        household_id=household.id
    ).first() if household else None

    members = db.session.query(Membership).filter_by(
        household_id=household.id
    ).order_by(Membership.points.desc()).all() if household else []

    for member in members:
        member.completed_chores = db.session.query(Task).filter_by(
            household_id=household.id,
            assigned_user_id=member.user_id,
            is_completed=True,
        ).count() if household else 0

    # Get the most recent valid invite
    invite = db.session.query(HouseholdInvite).filter_by(
        household_id=household.id,
        is_active=True,
    ).order_by(HouseholdInvite.created_at.desc()).first() if household else None

    return render_template(
        "manage_household.html",
        title="Manage Household",
        household=household,
        members=members,
        current_membership=current_membership,
        invite=invite,
    )

@app.route("/household/leave", methods=["POST"])
def leave_household():
    return redirect(url_for("home"))


@app.route("/household/delete", methods=["POST"])
@login_required
def delete_household():
    household = db.session.query(Household).first()
    if not household:
        return redirect(url_for("home"))

    membership = db.session.query(Membership).filter_by(
        user_id=current_user.id,
        household_id=household.id,
    ).first()
    if not membership or membership.role.lower() != "admin":
        return redirect(url_for("manage_household"))

    db.session.delete(household)
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/household/remove/<int:user_id>", methods=["POST"])
@login_required
def remove_member(user_id):
    household = db.session.query(Household).first()
    membership = db.session.query(Membership).filter_by(
        user_id=user_id,
        household_id=household.id
    ).first()
    if membership:
        db.session.delete(membership)
        db.session.commit()
    return redirect(url_for("manage_household"))


@app.route("/household/invite/regenerate", methods=["POST"])
@login_required
def regenerate_invite():
    household = db.session.query(Household).filter(
        Household.id == db.session.query(Membership.household_id).filter_by(
            user_id=current_user.id
        ).scalar_subquery()
    ).first()

    if not household:
        return redirect(url_for("home"))

    membership = db.session.query(Membership).filter_by(
        user_id=current_user.id,
        household_id=household.id,
    ).first()

    if not membership or membership.role.lower() != "admin":
        return redirect(url_for("manage_household"))

    # Deactivate all existing codes for this household
    db.session.query(HouseholdInvite).filter_by(
        household_id=household.id
    ).update({"is_active": False})

    # Generate a new unique code
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "HM-" + "".join(random.choices(chars, k=4))
        if not db.session.query(HouseholdInvite).filter_by(code=code).first():
            break

    new_invite = HouseholdInvite(
        household_id=household.id,
        created_by_user_id=current_user.id,
        code=code,
        expires_at=datetime.utcnow() + timedelta(days=7),
        is_active=True,
    )
    db.session.add(new_invite)
    db.session.commit()

    return redirect(url_for("manage_household"))