from types import SimpleNamespace

from flask import render_template, redirect, url_for, request

from app import app


@app.route("/index")
def index():
    return render_template("index.html", title="Homely")


@app.route("/")
def root():
    return redirect(url_for("login"))


@app.route("/home")
def home():
    return render_template("home.html", title="Home")


@app.route("/dashboard")
def dashboard():
    return render_template("home.html", title="Dashboard")


@app.route("/my-tasks")
def my_tasks():
    return render_template("my-tasks.html", title="My Tasks")


@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html", title="Leaderboard")


@app.route("/edit-profile")
def edit_profile():
    return render_template("edit-profile.html", title="Edit Profile")


@app.route("/rewards")
def rewards():
    return render_template("rewards.html", title="Rewards")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if not email or not password:
            error = "Please fill in all fields."
        else:
            return redirect(url_for("home"))
    return render_template("login.html", title="Login", error=error)


@app.route("/logout")
def logout():
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
        else:
            return redirect(url_for("signup_household"))
    return render_template("signup.html", title="Sign Up", form_data=form_data, error=error)


@app.route("/signup/household", methods=["GET", "POST"])
@app.route("/signup-household", methods=["GET", "POST"])
def signup_household():
    error = None
    form_data = {}
    if request.method == "POST":
        form_data = request.form.to_dict()
        return redirect(url_for("home"))
    return render_template(
        "signup_household.html",
        title="Household Setup",
        form_data=form_data,
        error=error
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