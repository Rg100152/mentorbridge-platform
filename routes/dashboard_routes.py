"""Role-based dashboards plus booking, favorite, review and profile actions."""
import uuid
from datetime import date

from flask import (
    Blueprint, abort, flash, redirect, render_template, request, session, url_for,
)

from routes import execute_db, login_required, query_db, role_required
from routes.main_routes import get_mentor, get_mentors

dashboard_bp = Blueprint("dashboard", __name__)

STATUSES = ("pending", "accepted", "declined", "completed")


def current_user_id():
    return session["user_id"]


def bookings_for_mentee(user_id):
    return query_db(
        """SELECT b.*, u.name AS mentor_name, u.avatar AS mentor_avatar, p.category
           FROM bookings b JOIN users u ON u.id = b.mentor_id
           LEFT JOIN mentor_profiles p ON p.user_id = u.id
           WHERE b.mentee_id = ? ORDER BY b.id DESC""",
        (user_id,),
    )


def bookings_for_mentor(user_id):
    return query_db(
        """SELECT b.*, u.name AS mentee_name, u.email AS mentee_email, u.avatar AS mentee_avatar
           FROM bookings b JOIN users u ON u.id = b.mentee_id
           WHERE b.mentor_id = ? ORDER BY
             CASE b.status WHEN 'pending' THEN 0 WHEN 'accepted' THEN 1 ELSE 2 END, b.id DESC""",
        (user_id,),
    )


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    user_id = current_user_id()
    user = query_db("SELECT * FROM users WHERE id = ?", (user_id,), one=True)
    if session.get("role") == "mentor":
        bookings = bookings_for_mentor(user_id)
        profile = query_db("SELECT * FROM mentor_profiles WHERE user_id = ?", (user_id,), one=True)
        pending = [b for b in bookings if b["status"] == "pending"]
        accepted = [b for b in bookings if b["status"] == "accepted"]
        reviews = query_db(
            "SELECT * FROM reviews WHERE mentor_id = ? ORDER BY id DESC LIMIT 5", (user_id,)
        )
        return render_template(
            "dashboard.html", mode="mentor", account=user, bookings=bookings,
            profile=profile, pending=pending, accepted=accepted, reviews=reviews,
        )

    bookings = bookings_for_mentee(user_id)
    favorites = query_db(
        """SELECT u.id, u.name, u.avatar, p.category, p.rating, p.headline
           FROM favorites f JOIN users u ON u.id = f.mentor_id
           JOIN mentor_profiles p ON p.user_id = u.id
           WHERE f.mentee_id = ? ORDER BY f.id DESC""",
        (user_id,),
    )
    recommended = [m for m in get_mentors() if m["id"] != user_id][:3]
    return render_template(
        "dashboard.html", mode="mentee", account=user, bookings=bookings,
        favorites=favorites, recommended=recommended,
    )


@dashboard_bp.route("/mentor/<int:mentor_id>/book", methods=["POST"])
@login_required
@role_required("mentee")
def book_session(mentor_id):
    mentor = get_mentor(mentor_id)
    if not mentor:
        abort(404)
    if mentor_id == current_user_id():
        flash("You cannot book a session with yourself.", "warning")
        return redirect(url_for("main.mentor_profile", mentor_id=mentor_id))

    topic = request.form.get("topic", "").strip()
    session_date = request.form.get("session_date", "").strip()
    time_slot = request.form.get("time_slot", "").strip()
    note = request.form.get("note", "").strip()

    if len(topic) < 3:
        flash("Please describe the topic you want to discuss (3+ characters).", "danger")
    elif not session_date or session_date < date.today().isoformat():
        flash("Please choose a valid future date.", "danger")
    elif not time_slot:
        flash("Please choose a time slot.", "danger")
    else:
        execute_db(
            """INSERT INTO bookings (mentee_id, mentor_id, topic, session_date, time_slot, note)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (current_user_id(), mentor_id, topic, session_date, time_slot, note),
        )
        flash("Session request sent! Your mentor will review it shortly.", "success")
        return redirect(url_for("dashboard.dashboard", booked=1))

    return redirect(url_for("main.mentor_profile", mentor_id=mentor_id))


@dashboard_bp.route("/booking/<int:booking_id>/<action>", methods=["POST"])
@login_required
def booking_action(booking_id, action):
    booking = query_db("SELECT * FROM bookings WHERE id = ?", (booking_id,), one=True)
    if not booking:
        abort(404)
    if action not in ("accept", "decline", "complete", "cancel"):
        abort(404)

    if action in ("cancel",):
        if booking["mentee_id"] != current_user_id():
            abort(403)
        if booking["status"] != "pending":
            flash("Only pending requests can be cancelled.", "warning")
        else:
            execute_db("UPDATE bookings SET status='declined', updated_at=CURRENT_TIMESTAMP WHERE id=?", (booking_id,))
            flash("Session request cancelled.", "info")
    else:
        if booking["mentor_id"] != current_user_id():
            abort(403)
        if action == "accept" and booking["status"] == "pending":
            # Free, key-less Jitsi Meet room generated when a mentor approves a session.
            room = "MentorBridge-" + uuid.uuid4().hex[:12]
            execute_db(
                """UPDATE bookings SET status='accepted', meeting_link=?, updated_at=CURRENT_TIMESTAMP
                   WHERE id=?""",
                (f"https://meet.jit.si/{room}", booking_id),
            )
            execute_db(
                "UPDATE mentor_profiles SET sessions_count = sessions_count + 1 WHERE user_id = ?",
                (current_user_id(),),
            )
            flash("Request accepted. A live Jitsi video link is now available!", "success")
        elif action == "decline" and booking["status"] == "pending":
            execute_db("UPDATE bookings SET status='declined', updated_at=CURRENT_TIMESTAMP WHERE id=?", (booking_id,))
            flash("Request declined.", "info")
        elif action == "complete" and booking["status"] == "accepted":
            execute_db("UPDATE bookings SET status='completed', updated_at=CURRENT_TIMESTAMP WHERE id=?", (booking_id,))
            flash("Session marked as completed.", "success")
        else:
            flash("This request can no longer be changed.", "warning")

    return redirect(url_for("dashboard.dashboard"))


@dashboard_bp.route("/mentor/profile", methods=["POST"])
@login_required
@role_required("mentor")
def update_profile():
    form = request.form
    headline = form.get("headline", "").strip()[:120]
    bio = form.get("bio", "").strip()[:2000]
    skills = form.get("skills", "").strip()[:500]
    category = form.get("category", "Career Guidance").strip()
    github_username = form.get("github_username", "").strip().lstrip("@")
    free_slots = form.get("free_slots", "").strip()[:500]
    is_available = 1 if form.get("is_available") else 0
    try:
        experience = max(0, min(60, int(form.get("experience") or 0)))
        hourly_rate = max(0.0, min(10000.0, float(form.get("hourly_rate") or 0)))
    except ValueError:
        flash("Experience and rate must be numbers.", "danger")
        return redirect(url_for("dashboard.dashboard"))

    if not headline or not skills:
        flash("Headline and skills are required.", "danger")
        return redirect(url_for("dashboard.dashboard"))
    if not all(c.isalnum() or c in "-_" for c in github_username):
        flash("GitHub username may only contain letters, numbers, - and _.", "danger")
        return redirect(url_for("dashboard.dashboard"))

    execute_db(
        """UPDATE mentor_profiles SET headline=?, bio=?, skills=?, category=?, experience=?,
           hourly_rate=?, github_username=?, free_slots=?, is_available=?, updated_at=CURRENT_TIMESTAMP
           WHERE user_id=?""",
        (headline, bio, skills, category, experience, hourly_rate,
         github_username, free_slots, is_available, current_user_id()),
    )
    flash("Mentor profile updated successfully.", "success")
    return redirect(url_for("dashboard.dashboard"))


@dashboard_bp.route("/favorite/<int:mentor_id>", methods=["POST"])
@login_required
@role_required("mentee")
def toggle_favorite(mentor_id):
    if not get_mentor(mentor_id):
        abort(404)
    existing = query_db(
        "SELECT id FROM favorites WHERE mentee_id=? AND mentor_id=?",
        (current_user_id(), mentor_id), one=True,
    )
    if existing:
        execute_db("DELETE FROM favorites WHERE id=?", (existing["id"],))
        flash("Removed from favourites.", "info")
    else:
        execute_db(
            "INSERT INTO favorites (mentee_id, mentor_id) VALUES (?, ?)",
            (current_user_id(), mentor_id),
        )
        flash("Mentor saved to your favourites.", "success")
    return redirect(request.referrer or url_for("main.mentors"))


@dashboard_bp.route("/review/<int:mentor_id>", methods=["POST"])
@login_required
@role_required("mentee")
def add_review(mentor_id):
    allowed = query_db(
        """SELECT 1 FROM bookings WHERE mentee_id=? AND mentor_id=?
           AND status IN ('accepted','completed') LIMIT 1""",
        (current_user_id(), mentor_id), one=True,
    )
    if not allowed:
        flash("You can review a mentor after an approved session.", "warning")
        return redirect(url_for("dashboard.dashboard"))

    try:
        rating = int(request.form.get("rating", 5))
    except ValueError:
        rating = 5
    rating = max(1, min(5, rating))
    comment = request.form.get("comment", "").strip()[:500]
    execute_db(
        "INSERT INTO reviews (mentor_id, mentee_id, rating, comment) VALUES (?, ?, ?, ?)",
        (mentor_id, current_user_id(), rating, comment),
    )
    flash("Thanks for sharing your feedback!", "success")
    return redirect(url_for("dashboard.dashboard"))
