from types import SimpleNamespace

from flask import render_template, redirect, url_for

from app import app


@app.route("/index")
def index():
    return render_template("index.html", title="Homely")


@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html", title="Home")


@app.route("/dashboard")
def dashboard():
    return render_template("home.html", title="Dashboard")


@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html", title="Leaderboard")


@app.route("/edit-profile")
def edit_profile():
    return render_template("edit-profile.html", title="Edit Profile")


@app.route("/rewards")
def rewards():
    return render_template("rewards.html", title="Rewards")


@app.route("/login")
def login():
    return render_template("login.html", title="Login")


@app.route("/logout")
def logout():
    return redirect(url_for("login"))


@app.route("/signup")
def signup():
    return render_template("signup.html", title="Sign Up", form_data={})


@app.route("/signup/household")
@app.route("/signup-household")
def signup_household():
    return render_template(
        "signup_household.html",
        title="Household Setup",
        form_data={}
    )


@app.route("/household/manage")
@app.route("/manage-household")
def manage_household():
    demo_household = SimpleNamespace(
        name="Demo Household",
        join_code="HM-72QA",
        reward_style="Balanced",
        reminder_frequency="Weekly"
    )

    current_user = SimpleNamespace(
        id=1,
        display_name="Mohammad"
    )

    current_membership = SimpleNamespace(
        user_id=1,
        user=current_user,
        role="Admin",
        bio="Managing household setup and member access.",
        points=120,
        streak=5
    )

    members = [
        current_membership,
        SimpleNamespace(
            user_id=2,
            user=SimpleNamespace(id=2, display_name="Aisha"),
            role="Member",
            bio="Completes shared chores and contributes to household tasks.",
            points=95,
            streak=3
        ),
        SimpleNamespace(
            user_id=3,
            user=SimpleNamespace(id=3, display_name="Jordan"),
            role="Member",
            bio="Helps with recurring chores and shared responsibilities.",
            points=80,
            streak=2
        )
    ]

    return render_template(
        "manage_household.html",
        title="Manage Household",
        household=demo_household,
        members=members,
        current_membership=current_membership
    )


@app.route("/household/leave", methods=["POST"])
def leave_household():
    return redirect(url_for("home"))