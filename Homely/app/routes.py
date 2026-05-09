from types import SimpleNamespace

from flask import render_template, redirect, url_for, request

from app import app, db
from app.models import User, Household, Membership
from flask_login import login_user, logout_user, current_user, login_required

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
    return render_template("home.html", title="Home")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("home.html", title="Dashboard")


@app.route("/leaderboard")
@login_required
def leaderboard():
    household = db.session.query(Household).first()
    if household:
        members = db.session.query(Membership).filter_by(household_id=household.id).all()
        members.sort(key=lambda m: m.points, reverse=True)
        first = members[0] if len(members) > 0 else None
        second = members[1] if len(members) > 1 else None
        third = members[2] if len(members) > 2 else None
        other_members = members[3:] if len(members) > 3 else []
    else:
        first = second = third = None
        other_members = []
    return render_template("leaderboard.html", title="Leaderboard", first=first, second=second, third=third, other_members=other_members)


@app.route("/edit-profile")
@login_required
def edit_profile():
    return render_template("edit-profile.html", title="Edit Profile")


@app.route("/rewards")
@login_required
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
        user = db.session.query(User).filter_by(email=email).first()
        if not user or not user.check_password(request.form["password"]):
            error = "Invalid email or password."
        else:
            login_user(user)
            return redirect(url_for("home"))
    return render_template("login.html", title="Login", error=error)


@app.route("/logout")
def logout():
    logout_user()
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
@login_required
def manage_household():
    household = db.session.query(Household).first()
    current_membership = db.session.query(Membership).filter_by(
        user_id=current_user.id,
        household_id=household.id    ).first() if household else None
    return render_template(
        "manage_household.html",
        title="Manage Household",
        household=db.session.query(Household).first(),
        members= db.session.query(Membership).filter_by(household_id=household.id).all() if household else [],
        current_membership=current_membership
    )


@app.route("/household/leave", methods=["POST"])
def leave_household():
    return redirect(url_for("home"))