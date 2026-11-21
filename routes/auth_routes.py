"""Real authentication: sign up (Mentor / Mentee), sign in and sign out."""
import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from routes import execute_db, get_db, query_db

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def avatar_for(name, email):
    """Free, key-less professional avatar from DiceBear (fallback for missing photos)."""
    seed = re.sub(r"[^a-zA-Z0-9]", "-", (name or email).strip().lower()).strip("-")
    return f"https://api.dicebear.com/9.x/notionists/svg?seed={seed}&backgroundColor=bef264,064e3b"


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("auth.html", mode="signup", form={})

    form = request.form
    name = form.get("name", "").strip()
    email = form.get("email", "").strip().lower()
    password = form.get("password", "")
    confirm = form.get("confirm", "")
    role = form.get("role", "mentee")
    category = form.get("category", "Career Guidance").strip()
    skills = form.get("skills", "").strip()

    if role not in ("mentor", "mentee"):
        role = "mentee"
    if len(name) < 2:
        flash("Please enter your full name.", "danger")
    elif not EMAIL_RE.match(email):
        flash("Please enter a valid email address.", "danger")
    elif len(password) < 8:
        flash("Password must be at least 8 characters long.", "danger")
    elif password != confirm:
        flash("Passwords do not match.", "danger")
    elif query_db("SELECT id FROM users WHERE email = ?", (email,), one=True):
        flash("An account with that email already exists. Try signing in.", "danger")
    else:
        user_id = execute_db(
            "INSERT INTO users (name, email, password_hash, role, avatar) VALUES (?, ?, ?, ?, ?)",
            (name, email, generate_password_hash(password), role, avatar_for(name, email)),
        )
        if role == "mentor":
            execute_db(
                """INSERT INTO mentor_profiles
                   (user_id, headline, bio, skills, category, hourly_rate, verified, is_available)
                   VALUES (?, ?, ?, ?, ?, ?, 0, 1)""",
                (
                    user_id,
                    form.get("headline", "").strip() or f"{category} Mentor",
                    form.get("bio", "").strip() or "New mentor on MentorBridge. Bio coming soon!",
                    skills or category,
                    category,
                    float(form.get("hourly_rate") or 0),
                ),
            )
        session.clear()
        session["user_id"] = user_id
        session["role"] = role
        flash(f"Welcome to MentorBridge, {name.split()[0]}! Your {role} account is ready.", "success")
        return redirect(url_for("dashboard.dashboard"))

    return render_template("auth.html", mode="signup", form={"name": name, "email": email, "role": role})


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "GET":
        return render_template("auth.html", mode="login", form={})

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    user = query_db("SELECT * FROM users WHERE email = ?", (email,), one=True)

    if user and check_password_hash(user["password_hash"], password):
        session.clear()
        session["user_id"] = user["id"]
        session["role"] = user["role"]
        flash(f"Welcome back, {user['name'].split()[0]}!", "success")
        return redirect(url_for("dashboard.dashboard"))

    flash("Invalid email or password.", "danger")
    return render_template("auth.html", mode="login", form={"email": email})


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("main.index"))
