import random
import string

from flask import render_template, redirect, url_for, request, session, jsonify, current_app, flash, current_app
from sqlalchemy import func

from app import db
from app import socketio
from app.email_utils import send_email
from app.scheduler import format_due_task_email
from app.forms import (
    SignupForm,
    LoginForm,
    EditProfileForm,
    CreateHouseholdForm,
    JoinHouseholdForm,
    SwitchHouseholdForm,
    ResetPasswordForm,
)
from app.utils import require_valid_form
from app.blueprints import main
from app.models import User, Household, Membership, RewardClaim, Task, HouseholdInvite, CustomReward
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime, timedelta, timezone
from flask_socketio import emit, join_room, leave_room


REMINDER_WINDOW_HOURS = 24


def utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def emit_leaderboard_update(household_id):
    try:
        household = db.session.query(Household).filter_by(id=household_id).first()
        if not household:
            return
        member_stats = {}
        members = db.session.query(Membership).filter_by(household_id=household.id).all()
        members.sort(key=lambda m: m.points, reverse=True)
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
        room = f"household_{household_id}"
        socketio.emit('leaderboard:update', {'member_stats': member_stats, 'household_id': household_id}, room=room)
    except Exception:
        current_app.logger.exception('emit_leaderboard_update failed')


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

    now = utcnow_naive()
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

    now = utcnow_naive()

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
        membership.last_overdue_popup = utcnow_naive()
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

    now = utcnow_naive()

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
        current_household=household,
        first=first, second=second, third=third,
        other_members=other_members,
        member_stats=member_stats,
        household_id=household.id if household else None,
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
            # compute the user's rank within the household (1 = top member)
            ranked_members = (
                db.session.query(Membership)
                .filter_by(household_id=household.id)
                .order_by(Membership.points.desc())
                .all()
            )
            member_rank = next((i + 1 for i, m in enumerate(ranked_members) if m.user_id == current_user.id), None)

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

    claimed_reward_keys = set()
    if household:
        claimed_reward_keys = {
            claim.reward_key
            for claim in db.session.query(RewardClaim.reward_key)
            .filter(
                RewardClaim.user_id == current_user.id,
                RewardClaim.household_id == household.id,
            )
            .all()
        }

    reward_catalog = [
        {
            "key": "skip-your-chore",
            "title": "Skip Your Chore for the Week",
            "description": "Take a well-earned break and skip one assigned chore this week.",
            "icon": "sofa",
            "threshold": 1000,
        },
        {
            "key": "choose-takeaway",
            "title": "Choose Tonight's Takeaway",
            "description": "You get the final say on what the household orders for dinner tonight.",
            "icon": "pizza",
            "threshold": 1500,
        },
        {
            "key": "tv-remote",
            "title": "TV Remote for the Evening",
            "description": "Full control of the TV for one evening, no debates, no compromises.",
            "icon": "tv",
            "threshold": 2000,
        },
        {
            "key": "first-shower",
            "title": "First Shower Rights for a Week",
            "description": "Priority bathroom access every morning for a full week.",
            "icon": "bath",
            "threshold": 3000,
        },
        {
            "key": "household-champion",
            "title": "Household Champion",
            "description": "Hold the #1 spot on the household leaderboard.",
            "icon": "crown",
            "threshold": 1,
        },
    ]

    rewards = []
    for reward in reward_catalog:
        threshold = reward["threshold"]
        is_rank_reward = reward["key"] == "household-champion"

        if not is_rank_reward:
            unlocked = user_points >= threshold
            remaining_points = max(threshold - user_points, 0)
            progress_pct = 100 if threshold <= 0 else min(100, round((user_points / threshold) * 100))
            progress_points = min(user_points, threshold)
            status_text = "Unlocked" if unlocked else f"{remaining_points:,} pts away"
            condition_label = f"{threshold:,} pts"
            condition_icon = "zap"
            progress_label = f"{progress_points:,} / {threshold:,} pts"
        else:
            unlocked = household_rank == threshold
            status_text = "Unlocked" if unlocked else f"#{threshold} spot required"
            condition_label = f"#{threshold} household rank"
            condition_icon = "medal"
            progress_pct = None
            progress_label = None

        rewards.append(
            {
                **reward,
                "unlocked": unlocked,
                "claimed": reward["key"] in claimed_reward_keys,
                "status_text": status_text,
                "condition_label": condition_label,
                "condition_icon": condition_icon,
                "progress_pct": progress_pct,
                "progress_label": progress_label,
                "claim_url": url_for("main.claim_reward", reward_key=reward["key"]),
            }
        )

    custom_rewards = (
        db.session.query(CustomReward)
        .filter_by(household_id=household.id)
        .order_by(CustomReward.created_at.desc())
        .all()
        if household else []
    )

    claimed_custom_ids = {
        int(key[7:]) for key in claimed_reward_keys if key.startswith("custom-")
    }

    return render_template(
        "rewards.html",
        title="Rewards",
        user_points=user_points,
        current_membership=current_membership,
        household_rank=household_rank,
        member_rank=member_rank if 'member_rank' in locals() else None,
        rewards=rewards,
        custom_rewards=custom_rewards,
        claimed_custom_ids=claimed_custom_ids,
        claimed_count=len(claimed_reward_keys),
    )


@main.route("/rewards/claim/<reward_key>", methods=["POST"])
@login_required
def claim_reward(reward_key):
    household = db.session.query(Household).filter_by(id=current_user.current_household).first()
    if not household:
        return jsonify({"success": False, "message": "No active household found."}), 400

    membership = db.session.query(Membership).filter_by(
        user_id=current_user.id,
        household_id=household.id,
    ).first()
    if not membership:
        return jsonify({"success": False, "message": "You are not a member of this household."}), 403

    user_points = membership.points or 0
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
    household_rank = 1 + sum(1 for item in ranked_households if item.total_points > household_points)

    reward_lookup = {
        "skip-your-chore": {"threshold": 1000, "title": "Skip Your Chore for the Week"},
        "choose-takeaway": {"threshold": 1500, "title": "Choose Tonight's Takeaway"},
        "tv-remote": {"threshold": 2000, "title": "TV Remote for the Evening"},
        "first-shower": {"threshold": 3000, "title": "First Shower Rights for a Week"},
        "household-champion": {"threshold": 1, "title": "Household Champion"},
    }

    reward = reward_lookup.get(reward_key)
    if not reward:
        return jsonify({"success": False, "message": "Unknown reward."}), 404

    unlocked = household_rank == reward["threshold"] if reward_key == "household-champion" else user_points >= reward["threshold"]
    if not unlocked:
        return jsonify({"success": False, "message": "This reward is not unlocked yet."}), 400

    existing_claim = db.session.query(RewardClaim).filter_by(
        user_id=current_user.id,
        household_id=household.id,
        reward_key=reward_key,
    ).first()
    if existing_claim:
        return jsonify({
            "success": True,
            "claimed": True,
            "rewardKey": reward_key,
            "title": reward["title"],
        })

    db.session.add(
        RewardClaim(
            user_id=current_user.id,
            household_id=household.id,
            reward_key=reward_key,
        )
    )

    # Deduct points for non-rank rewards
    if reward_key != "household-champion":
        claiming_membership = db.session.query(Membership).filter_by(
            user_id=current_user.id,
            household_id=household.id,
        ).first()
        if claiming_membership:
            claiming_membership.points = max(0, claiming_membership.points - reward["threshold"])

    db.session.commit()

    try:
        emit_leaderboard_update(household.id)
    except Exception:
        current_app.logger.exception('failed emitting leaderboard update from claim_reward')

    new_points = claiming_membership.points if (reward_key != "household-champion" and claiming_membership) else user_points
    return jsonify({
        "success": True,
        "claimed": True,
        "rewardKey": reward_key,
        "title": reward["title"],
        "newPoints": new_points,
    })


@main.route("/rewards/custom/create", methods=["POST"])
@login_required
def create_custom_reward():
    household = db.session.query(Household).filter_by(id=current_user.current_household).first()
    if not household:
        return jsonify({"error": "No household found"}), 403

    data = request.get_json()
    title = (data.get("title") or "").strip()
    desc = (data.get("desc") or "").strip()
    icon = (data.get("icon") or "star").strip()

    try:
        threshold = int(data.get("threshold"))
        if threshold < 1:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Points must be a positive number"}), 400

    if not title:
        return jsonify({"error": "Title is required"}), 400

    reward = CustomReward(
        household_id=household.id,
        created_by_user_id=current_user.id,
        title=title,
        description=desc,
        points_threshold=threshold,
        icon=icon,
    )
    db.session.add(reward)
    db.session.commit()
    return jsonify({"id": reward.id, "title": reward.title}), 201


@main.route("/rewards/custom/<int:reward_id>", methods=["DELETE"])
@login_required
def delete_custom_reward(reward_id):
    reward = db.session.query(CustomReward).filter_by(id=reward_id).first()
    if not reward:
        return jsonify({"error": "Not found"}), 404

    membership = db.session.query(Membership).filter_by(
        user_id=current_user.id,
        household_id=reward.household_id,
    ).first()
    if not membership:
        return jsonify({"error": "Unauthorised"}), 403

    db.session.delete(reward)
    db.session.commit()
    return jsonify({"success": True}), 200


@main.route("/rewards/custom/<int:reward_id>/claim", methods=["POST"])
@login_required
def claim_custom_reward(reward_id):
    household = db.session.query(Household).filter_by(id=current_user.current_household).first()
    if not household:
        return jsonify({"success": False, "message": "No active household found."}), 400

    membership = db.session.query(Membership).filter_by(
        user_id=current_user.id,
        household_id=household.id,
    ).first()
    if not membership:
        return jsonify({"success": False, "message": "Not a member of this household."}), 403

    reward = db.session.query(CustomReward).filter_by(id=reward_id, household_id=household.id).first()
    if not reward:
        return jsonify({"success": False, "message": "Reward not found."}), 404

    if (membership.points or 0) < reward.points_threshold:
        return jsonify({"success": False, "message": "This reward is not unlocked yet."}), 400

    reward_key = f"custom-{reward_id}"
    existing = db.session.query(RewardClaim).filter_by(
        user_id=current_user.id,
        household_id=household.id,
        reward_key=reward_key,
    ).first()
    if not existing:
        db.session.add(RewardClaim(
            user_id=current_user.id,
            household_id=household.id,
            reward_key=reward_key,
        ))
        membership.points = max(0, (membership.points or 0) - reward.points_threshold)
        db.session.commit()

    return jsonify({"success": True, "claimed": True, "newPoints": membership.points})


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
                household = Household(name=household_name)
                db.session.add(household)
                db.session.flush()

                user = User(
                    full_name=f"{signup_data['first_name']} {signup_data['last_name']}",
                    display_name=signup_data["display_name"],
                    email=signup_data["email"],
                    current_household=household.id
                )
                user.set_password(signup_data["password"])
                db.session.add(user)
                db.session.flush()


                join_code = HouseholdInvite(
                    household_id=household.id,
                    created_by_user_id=user.id,
                    code="HM-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=4)),
                    expires_at=utcnow_naive() + timedelta(days=1),
                    is_active=True,
                )
                db.session.add(join_code)

                membership = Membership(
                    user_id=user.id,
                    household_id=household.id,
                    role="Admin",
                    points=0,
                )
                db.session.add(membership)
                user.current_household = household.id
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

    members = household.memberships if household else []

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
        households=households
    )

@main.route("/household/switch", methods=["POST"])
@login_required
def switch_household():
    form = SwitchHouseholdForm()
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
    form = CreateHouseholdForm()
    if not form.validate_on_submit():
        return redirect(url_for("main.manage_household"))

    name = form.household_name.data.strip()
    if not name:
        return redirect(url_for("main.manage_household"))

    household = Household(name=name)
    db.session.add(household)
    db.session.flush()

    join_code = HouseholdInvite(
        household_id=household.id,
        created_by_user_id=current_user.id,
        code="HM-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=4)),
        expires_at=datetime.utcnow() + timedelta(days=1),
        is_active=True,
    )
    db.session.add(join_code)

    membership = Membership(
        user_id=current_user.id,
        household_id=household.id,
        role="Admin",
        points=0,
    )
    db.session.add(membership)
    current_user.current_household = household.id
    db.session.commit()
    return redirect(url_for("main.home"))

@main.route("/household/join", methods=["POST"])
@login_required
def join_household():
    form = JoinHouseholdForm()
    if not form.validate_on_submit():
        return redirect(url_for("main.manage_household"))

    join_code = form.join_code.data.strip().upper()
    invite = db.session.query(HouseholdInvite).filter_by(
        code=join_code
    ).first()

    if not invite or not invite.is_active:
        error = "Invalid or expired invite code. Please check the code and try again, or ask an admin to regenerate it."
        return jsonify({"error": error}), 400

    household = db.session.query(Household).filter_by(id=invite.household_id).first()
    if not household:
        return redirect(url_for("main.manage_household"))

    membership = Membership(
        user_id=current_user.id,
        household_id=household.id,
        role="Member",
        points=0,
    )
    db.session.add(membership)
    current_user.current_household = household.id
    db.session.commit()
    return redirect(url_for("main.home"))

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
        expires_at=utcnow_naive() + timedelta(days=1),
        is_active=True,
    )
    db.session.add(new_invite)
    db.session.commit()

    return redirect(url_for("main.manage_household"))



@main.route("/email-reminders/toggle", methods=["POST"])
@login_required
def toggle_email_reminders():
    """Allow the logged-in user to opt in or out of due-task email reminders."""
    current_user.email_reminders_enabled = not current_user.email_reminders_enabled
    db.session.commit()

    status = "enabled" if current_user.email_reminders_enabled else "disabled"
    flash(f"Email reminders {status}.", "success")
    return redirect(url_for("main.manage_household"))


@main.route("/email-reminders/send-now", methods=["POST"])
@login_required
def send_email_reminder_now():
    """Send a due-task reminder email immediately for demo/testing."""
    if not current_user.email_reminders_enabled:
        flash("Turn on email reminders before sending a reminder email.", "warning")
        return redirect(url_for("main.manage_household"))

    due_soon_tasks = due_soon_tasks_for_user(current_user.id)

    if not due_soon_tasks:
        flash("No due-soon tasks found for your account.", "info")
        return redirect(url_for("main.manage_household"))

    subject = f"Homely reminder: {len(due_soon_tasks)} task(s) due soon"
    body = format_due_task_email(current_user, due_soon_tasks)
    send_email(current_app, current_user.email, subject, body)

    flash("Reminder email sent.", "success")
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
    task.completed_at = utcnow_naive() if task.is_completed else None

    message = None
    stole_points = False

    if task.is_completed:
        task.points_awarded_to_user_id = current_user.id
        membership.points += task.points_value

        if task.assignee and task.assigned_user_id != current_user.id:
            stole_points = True
            message = f"You stole {task.points_value} points from {task.assignee.display_name}!"
        else:
            message = f"You earned {task.points_value} points!"
    else:
        recipient_user_id = task.points_awarded_to_user_id or task.assigned_user_id
        if recipient_user_id:
            recipient_membership = db.session.query(Membership).filter_by(
                user_id=recipient_user_id,
                household_id=task.household_id,
            ).first()
            if recipient_membership:
                recipient_membership.points = max(0, recipient_membership.points - task.points_value)

    db.session.commit()
    # Emit updated leaderboard stats to connected clients
    try:
        household = db.session.query(Household).filter_by(id=task.household_id).first()
        member_stats = {}
        if household:
            members = db.session.query(Membership).filter_by(household_id=household.id).all()
            members.sort(key=lambda m: m.points, reverse=True)
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
        room = f"household_{task.household_id}"
        socketio.emit('leaderboard:update', {'member_stats': member_stats, 'household_id': task.household_id}, room=room)
    except Exception:
        pass

    return {
        "done": task.is_completed,
        "points": task.points_value,
        "message": message,
        "pointsAwardedToUserId": task.points_awarded_to_user_id,
        "stole": stole_points,
    }, 200

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

    try:
        emit_leaderboard_update(task.household_id)
    except Exception:
        current_app.logger.exception('failed emitting leaderboard update from create_task')

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

    hid = task.household_id
    db.session.delete(task)
    db.session.commit()
    try:
        emit_leaderboard_update(hid)
    except Exception:
        current_app.logger.exception('failed emitting leaderboard update from delete_task')
    return {"success": True}, 200


# Socket.IO event handlers
@socketio.on('join')
def handle_join(data):
    try:
        hid = data.get('household_id')
        if hid:
            room = f"household_{hid}"
            join_room(room)
            emit('joined', {'room': room})
    except Exception:
        pass

@socketio.on('leave')
def handle_leave(data):
    try:
        hid = data.get('household_id')
        if hid:
            room = f"household_{hid}"
            leave_room(room)
            emit('left', {'room': room})
    except Exception:
        pass

from flask import current_app, flash, redirect, render_template, request, url_for

from app.email_utils import send_email
from app.password_reset import (
    RESET_MAX_AGE_SECONDS,
    generate_password_reset_token,
    verify_password_reset_token,
)


@main.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Send a password reset email if the submitted account exists."""
    message = None
    error = None

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()

        if not email:
            error = "Please enter your email address."
        else:
            user = db.session.query(User).filter_by(email=email).first()

            if user:
                token = generate_password_reset_token(user)
                reset_path = url_for("main.reset_password", token=token)
                reset_url = request.host_url.rstrip("/") + reset_path

                subject = "Reset your Homely password"
                body = (
                    f"Hi {user.display_name},\n\n"
                    "A password reset was requested for your Homely account.\n\n"
                    f"Use this link to reset your password:\n{reset_url}\n\n"
                    f"This link expires in {RESET_MAX_AGE_SECONDS // 60} minutes.\n\n"
                    "If you did not request this, you can ignore this email.\n"
                )

                send_email(current_app, user.email, subject, body)

            message = "If an account exists for that email, a reset link has been sent."

    return render_template(
        "forgot_password.html",
        title="Forgot Password",
        message=message,
        error=error,
    )


@main.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Allow a user to set a new password using a valid reset token."""
    user = verify_password_reset_token(token)

    if not user:
        return render_template(
            "reset_password.html",
            title="Reset Password",
            token=None,
            error="This password reset link is invalid or has expired.",
        ), 400

    form = ResetPasswordForm()

    if form.validate_on_submit():
        # form has already validated password length and equality
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been updated. Please sign in.", "success")
        return redirect(url_for("main.login"))

    # If POST but not valid, aggregate errors for display
    error = None
    if request.method == 'POST' and not form.validate():
        # collect first error message
        for fld, errs in form.errors.items():
            if errs:
                error = errs[0]
                break

    return render_template(
        "reset_password.html",
        title="Reset Password",
        token=token,
        form=form,
        error=error,
    )