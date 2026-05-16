import random
import string

from flask import render_template, redirect, url_for, request, session, jsonify, current_app
from sqlalchemy import func

from app import db
from app.forms import (
    SignupForm,
    LoginForm,
    EditProfileForm,
    CreateHouseholdForm,
    JoinHouseholdForm,
    SwitchHouseholdForm,
)
from app.utils import require_valid_form
from app.blueprints import main
from app.models import User, Household, Membership, Task, HouseholdInvite
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime, timedelta


REMINDER_WINDOW_HOURS = 24


def serialize_task_reminder(task):
    """Return lightweight task data for due-soon reminder UI/API."""
    return {
        "id": task.id,
        "text": task.title,
        "cat": task.category,
        "points": task.points_value,
        "due": task.due_date.isoformat() if task.due_date else None,
        "dueLabel": task.due_date.strftime("%a %d %b, %I:%M %p") if task.due_date else "No due date",
    }


def due_soon_tasks_for_user(user_id, hours=REMINDER_WINDOW_HOURS):
    """Return incomplete tasks assigned to a user and due within the reminder window."""
    membership = db.session.query(Membership).filter_by(user_id=user_id).first()

    if not membership:
        return []

    now = datetime.utcnow()
    window_end = now + timedelta(hours=hours)

    return (
        db.session.query(Task)
        .filter(
            Task.household_id == membership.household_id,
            Task.assigned_user_id == user_id,
            Task.is_completed == False,
            Task.due_date != None,
            Task.due_date >= now,
            Task.due_date <= window_end,
        )
        .order_by(Task.due_date.asc())
        .all()
    )

@main.route("/index")
@login_required
def index():
    return render_template("index.html", title="Homely")


@main.route("/")
def root():
    return redirect(url_for("main.login"))


@main.route("/home")
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

    # Find overdue tasks in the current household so the refresh state matches the frontend.
    overdue_tasks = (
        db.session.query(Task)
        .filter(
            Task.household_id == membership.household_id,
            Task.is_completed == False,
            Task.due_date != None,
            Task.due_date < now,
        )
        .all()
        if membership
        else []
    )

    overdue_count = len(overdue_tasks)

    due_soon_tasks = due_soon_tasks_for_user(current_user.id) if membership else []
    due_soon_data = [serialize_task_reminder(task) for task in due_soon_tasks]

    # Current daily loss is 5 points for each overdue task.
    total_points_lost = overdue_count * 5

    # Show the user's effective total after accounting for today's overdue tasks.
    effective_points = max(0, (membership.points if membership else 0) - total_points_lost)

    # Show popup when a task has become overdue since the last dismissal.
    show_popup = False
    if overdue_count > 0 and membership:
        latest_overdue_due = max(task.due_date for task in overdue_tasks if task.due_date)
        if membership.last_overdue_popup is None or \
           latest_overdue_due > membership.last_overdue_popup or \
           (now - membership.last_overdue_popup).total_seconds() > 86400:
            show_popup = True

    import json

    tasks_data = [
        {
            "id": t.id,
            "text": t.title,
            "done": t.is_completed,
            "cat": t.category,
            "assignedTo": t.assignee.display_name if t.assignee else None,
            "points": t.points_value,
            "due": t.due_date.isoformat() if t.due_date else None,
        }
        for t in db.session.query(Task).filter_by(
            household_id=membership.household_id
        ).all()
    ] if membership else []

    members_data = [
        {
            "id": m.user_id,
            "name": m.user.display_name,
        }
        for m in db.session.query(Membership).filter_by(
            household_id=membership.household_id
        ).all()
    ] if membership else []

    return render_template(
        "home.html",
        title="Home",
        members=members,
        due_soon_count=len(due_soon_data),
        due_soon_tasks=due_soon_data,
        due_soon_window_hours=REMINDER_WINDOW_HOURS,
        overdue_count=overdue_count,
        total_points_lost=total_points_lost,
        effective_points=effective_points,
        show_popup=show_popup,
        tasks_data=tasks_data,
        members_data=members_data
    )

@main.route("/dismiss-overdue-popup", methods=["POST"])
@login_required
def dismiss_overdue_popup():
    membership = db.session.query(Membership).filter_by(
        user_id=current_user.id
    ).first()
    if membership:
        membership.last_overdue_popup = datetime.utcnow()
        db.session.commit()
    return "", 204


@main.route("/tasks/reminders")
@login_required
def task_reminders():
    due_soon_tasks = due_soon_tasks_for_user(current_user.id)
    return jsonify({
        "count": len(due_soon_tasks),
        "windowHours": REMINDER_WINDOW_HOURS,
        "tasks": [serialize_task_reminder(task) for task in due_soon_tasks],
    })

@main.route("/dashboard")
@login_required
def dashboard():
    return redirect(url_for("main.home"))


@main.route("/my-tasks")
@login_required
def my_tasks():
    membership = db.session.query(Membership).filter_by(user_id=current_user.id).first()
    tasks = db.session.query(Task).filter_by(
        household_id=membership.household_id,
        assigned_user_id=current_user.id
    ).all() if membership else []

    now = datetime.utcnow()

    # Find overdue tasks assigned to current user
    overdue_tasks = (
        db.session.query(Task)
        .filter(
            Task.household_id == membership.household_id,
            Task.assigned_user_id == current_user.id,
            Task.is_completed == False,
            Task.due_date != None,
            Task.due_date < now,
        )
        .all()
        if membership
        else []
    )

    overdue_count = len(overdue_tasks)
    total_points_lost = overdue_count * 5

    tasks_data = [
        {
            "id": task.id,
            "text": task.title,
            "done": task.is_completed,
            "cat": task.category,
            "points": task.points_value,
            "due": task.due_date.isoformat() if task.due_date else None,
        }
        for task in tasks
    ]
    return render_template("my-tasks.html", title="My Tasks", tasks_data=tasks_data, overdue_count=overdue_count, total_points_lost=total_points_lost)


@main.route("/leaderboard")
@login_required
def leaderboard():
    household = db.session.query(Household).filter_by(id=current_user.current_household).first()
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


@main.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()

    if form.validate_on_submit():
        current_user.display_name = form.display_name.data.strip()
        current_user.avatar = form.avatar.data.strip()
        db.session.commit()
        return redirect(url_for("main.edit_profile"))
    
    # GET request
    member = db.session.query(Membership).filter_by(user_id=current_user.id).first()
    households = db.session.query(Household).join(Membership).filter(Membership.user_id == current_user.id).all()
    
    # Calculate rank in current household
    household_rank = None
    completed_tasks_count = 0
    if member:
        ranked_members = db.session.query(Membership).filter_by(
            household_id=member.household_id
        ).order_by(Membership.points.desc()).all()
        household_rank = next((i + 1 for i, m in enumerate(ranked_members) if m.user_id == current_user.id), None)
        
        # Count completed tasks
        completed_tasks_count = db.session.query(Task).filter_by(
            assigned_user_id=current_user.id,
            household_id=member.household_id,
            is_completed=True
        ).count()
    
    return render_template(
        "edit-profile.html", 
        title="Edit Profile", 
        member=member, 
        households=households,
        household_rank=household_rank,
        completed_tasks_count=completed_tasks_count
    )


@main.route("/rewards")
@login_required
def rewards():
    household = db.session.query(Household).filter_by(id=current_user.current_household).first()
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


@main.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    error = None
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        password = form.password.data
        user = db.session.query(User).filter_by(email=email).first()
        if not user or not user.check_password(password):
            error = "Invalid email or password."
        else:
            login_user(user)
            return redirect(url_for("main.home"))
    elif request.method == "POST":
        error = "Please fill in all fields."
    return render_template("login.html", title="Login", error=error, form=form)


@main.route("/logout", methods=["GET", "POST"])
def logout():
    logout_user()
    return redirect(url_for("main.login"))


@main.route("/signup", methods=["GET", "POST"])
@require_valid_form(SignupForm, 'signup.html', title="Sign Up")
def signup(form):
    # At this point `form` has passed `validate_on_submit()` (CSRF + field validators)
    existing = db.session.query(User).filter_by(email=form.email.data.strip().lower()).first()
    if existing:
        error = "An account with that email already exists."
        return render_template('signup.html', form=form, error=error, title="Sign Up")

    session["signup_data"] = {
        "first_name": form.first_name.data.strip(),
        "last_name": form.last_name.data.strip(),
        "display_name": form.display_name.data.strip(),
        "email": form.email.data.strip().lower(),
        "password": form.password.data,
    }
    return redirect(url_for("main.signup_household"))


@main.route("/signup/household")
@main.route("/signup-household")
def signup_household():
    if not session.get("signup_data"):
        return redirect(url_for("main.signup"))
    return render_template("signup_household.html", title="Household Setup")

@main.route("/signup/household/create", methods=["GET", "POST"])
def signup_create_household():
    signup_data = session.get("signup_data")
    if not signup_data:
        return redirect(url_for("main.signup"))

    form = CreateHouseholdForm()
    error = None
    form_data = {}

    if request.method == "POST":
        form_data = request.form.to_dict()
        if form.validate_on_submit():
            household_name = form.household_name.data.strip()

            if db.session.query(User).filter_by(email=signup_data["email"]).first():
                error = "An account with that email already exists. Please sign in."
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

                user.current_household = household.id
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
                    role="Admin",
                    points=0,
                ))
                db.session.commit()
                session.pop("signup_data", None)
                login_user(user)
                return redirect(url_for("main.home"))
        elif not form.household_name.data or not form.household_name.data.strip():
            error = "Please enter a household name."
        else:
            error = "Please enter a household name."

    return render_template(
        "signup_create_household.html",
        title="Create Household",
        form=form,
        form_data=form_data,
        error=error,
    )


@main.route("/signup/household/join", methods=["GET", "POST"])
def signup_join_household():
    signup_data = session.get("signup_data")
    if not signup_data:
        return redirect(url_for("main.signup"))

    form = JoinHouseholdForm()
    error = None
    form_data = {}

    if request.method == "POST":
        form_data = request.form.to_dict()
        if form.validate_on_submit():
            join_code = form.join_code.data.strip().upper()

            if db.session.query(User).filter_by(email=signup_data["email"]).first():
                error = "An account with that email already exists. Please sign in."
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
                    # Ensure the user's current household is set when joining
                    user.current_household = invite.household_id
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
                    return redirect(url_for("main.home"))
        elif not form.join_code.data or not form.join_code.data.strip():
            error = "Please enter an invite code."
        else:
            error = "Please enter an invite code."

    return render_template(
        "signup_join_household.html",
        title="Join Household",
        form=form,
        form_data=form_data,
        error=error,
    )


@main.route("/household/manage")
@main.route("/manage-household")
@login_required
def manage_household():
    household = db.session.query(Household).filter_by(id=current_user.current_household).first()

    current_membership = db.session.query(Membership).filter_by(
        user_id=current_user.id,
        household_id=household.id
    ).first() if household else None

    members = db.session.query(Membership).filter_by(
        household_id=household.id
    ).order_by(Membership.points.desc()).all() if household else []

    households = db.session.query(Household).join(Membership).filter(Membership.user_id == current_user.id).all()

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
        current_household=household,
        members=members,
        current_membership=current_membership,
        invite=invite,
        households=households,
    )

@main.route("/household/switch", methods=["POST"])
@login_required
def switch_household():
    form = SwitchHouseholdForm(meta={"csrf": False})
    if not form.validate_on_submit():
        return redirect(url_for("main.manage_household"))

    household_id = form.household_id.data
    membership = db.session.query(Membership).filter_by(
        user_id=current_user.id,
        household_id=household_id,
    ).first()
    if membership:
        current_user.current_household = household_id
        db.session.commit()
    return redirect(url_for("main.home"))

@main.route("/household/create", methods=["POST"])
@login_required
def create_household():
    pass

@main.route("/household/join", methods=["POST"])
@login_required
def join_household():
    pass

@main.route("/household/leave", methods=["POST"])
@login_required
def leave_household():
    return redirect(url_for("main.home"))


@main.route("/household/delete", methods=["POST"])
@login_required
def delete_household():
    household = db.session.query(Household).filter_by(id=current_user.current_household).first()
    if not household:
        return redirect(url_for("main.home"))

    membership = db.session.query(Membership).filter_by(
        user_id=current_user.id,
        household_id=household.id,
    ).first()
    if not membership or membership.role.lower() != "admin":
        return redirect(url_for("main.manage_household"))

    db.session.delete(household)
    db.session.commit()
    return redirect(url_for("main.home"))

@main.route("/household/remove/<int:user_id>", methods=["POST"])
@login_required
def remove_member(user_id):
    household = db.session.query(Household).filter_by(id=current_user.current_household).first()

    if not household:
        current_app.logger.info(f"remove_member: no household for current_user {current_user.id}")
        return redirect(url_for("main.manage_household"))

    # Ensure the requester is an admin in this household
    requester_membership = db.session.query(Membership).filter_by(
        user_id=current_user.id,
        household_id=household.id,
    ).first()
    if not requester_membership or requester_membership.role.lower() != "admin":
        current_app.logger.info(f"remove_member: unauthorised request by user {current_user.id}")
        return redirect(url_for("main.manage_household"))

    membership = db.session.query(Membership).filter_by(
        user_id=user_id,
        household_id=household.id,
    ).first()

    if membership:
        current_app.logger.info(f"remove_member: deleting membership {membership.id} user={user_id} household={household.id}")
        db.session.delete(membership)
        db.session.commit()
    else:
        current_app.logger.info(f"remove_member: membership not found for user={user_id} household={household.id}")

    return redirect(url_for("main.manage_household"))


@main.route("/household/invite/regenerate", methods=["POST"])
@login_required
def regenerate_invite():
    household = db.session.query(Household).filter_by(id=current_user.current_household).first()

    if not household:
        return redirect(url_for("main.home"))

    membership = db.session.query(Membership).filter_by(
        user_id=current_user.id,
        household_id=household.id,
    ).first()

    if not membership or membership.role.lower() != "admin":
        return redirect(url_for("main.manage_household"))

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

    return redirect(url_for("main.manage_household"))

@main.route("/tasks/<int:task_id>/toggle", methods=["POST"])
@login_required
def toggle_task(task_id):
    task = db.session.query(Task).filter_by(id=task_id).first()
    if not task:
        return {"error": "Task not found"}, 404

    membership = db.session.query(Membership).filter_by(
        user_id=current_user.id,
        household_id=task.household_id
    ).first()
    if not membership:
        return {"error": "Unauthorised"}, 403

    task.is_completed = not task.is_completed
    task.completed_at = datetime.utcnow() if task.is_completed else None

    # Award or deduct points when toggling
    if task.assignee:
        assigned_membership = db.session.query(Membership).filter_by(
            user_id=task.assigned_user_id,
            household_id=task.household_id
        ).first()
        if assigned_membership:
            if task.is_completed:
                assigned_membership.points += task.points_value
            else:
                assigned_membership.points = max(0, assigned_membership.points - task.points_value)

    db.session.commit()
    return {"done": task.is_completed, "points": task.points_value}, 200

@main.route("/tasks/create", methods=["POST"])
@login_required
def create_task():
    membership = db.session.query(Membership).filter_by(
        user_id=current_user.id
    ).first()
    if not membership:
        return {"error": "No household found"}, 403

    data = request.get_json()

    assigned_member = None
    assigned_to = (data.get("assignedTo") or "").strip()
    if assigned_to:
        assigned_member = db.session.query(Membership).filter_by(
            household_id=membership.household_id
        ).join(User).filter(User.display_name == assigned_to).first()

    due_date = None
    if data.get("due"):
        try:
            due_date = datetime.fromisoformat(data["due"])
        except ValueError:
            pass

    task = Task(
        household_id=membership.household_id,
        assigned_user_id=assigned_member.user_id if assigned_member else current_user.id,
        title=data.get("text", "").strip(),
        category=data.get("cat", "other"),
        points_value=int(data.get("points")) if data.get("points") else 10,
        due_date=due_date,
        is_completed=False,
    )
    db.session.add(task)
    db.session.commit()

    return {
        "id": task.id,
        "text": task.title,
        "done": task.is_completed,
        "cat": task.category,
        "assignedTo": assigned_member.user.display_name if assigned_member else None,
        "points": task.points_value,
        "due": task.due_date.isoformat() if task.due_date else None,
    }, 201


@main.route("/tasks/<int:task_id>", methods=["DELETE"])
@login_required
def delete_task(task_id):
    task = db.session.query(Task).filter_by(id=task_id).first()
    if not task:
        return {"error": "Task not found"}, 404

    membership = db.session.query(Membership).filter_by(
        user_id=current_user.id,
        household_id=task.household_id,
    ).first()
    if not membership:
        return {"error": "Unauthorised"}, 403

    db.session.delete(task)
    db.session.commit()
    return {"success": True}, 200