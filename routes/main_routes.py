"""Public pages: home, mentor directory and mentor profile."""
from datetime import date

from flask import Blueprint, abort, render_template, request, session

from routes import get_db, query_db

main_bp = Blueprint("main", __name__)

CATEGORIES = [
    ("Python", "Python & Backend"),
    ("Cyber Security", "Cyber Security"),
    ("Web Design", "Web Design"),
    ("Data Science", "Data Science"),
    ("Career Guidance", "Career Guidance"),
]

DEFAULT_SLOTS = [
    "09:00 - 10:00", "10:30 - 11:30", "12:00 - 13:00",
    "14:00 - 15:00", "16:00 - 17:00", "18:30 - 19:30",
]

MENTOR_SELECT = """
    SELECT u.id, u.name, u.email, u.avatar, u.created_at,
           p.headline, p.bio, p.skills, p.category, p.experience,
           p.hourly_rate, p.free_slots, p.github_username, p.rating,
           p.sessions_count, p.verified, p.is_available
    FROM users u JOIN mentor_profiles p ON p.user_id = u.id
"""


def get_mentors(where="", args=()):
    """Every mentor joined with their public profile."""
    sql = MENTOR_SELECT
    if where:
        sql += " WHERE " + where
    sql += " ORDER BY p.verified DESC, p.rating DESC, u.name ASC"
    return query_db(sql, args)


def get_mentor(mentor_id):
    rows = query_db(MENTOR_SELECT + " WHERE u.id = ? LIMIT 1", (mentor_id,))
    return rows[0] if rows else None


def slots_for(mentor):
    raw = (mentor["free_slots"] or "").strip()
    if not raw:
        return DEFAULT_SLOTS
    slots = [s.strip() for s in raw.replace("|", ",").split(",") if s.strip()]
    return slots or DEFAULT_SLOTS


@main_bp.route("/")
def index():
    db = get_db()
    featured = [m for m in get_mentors() if m["is_available"]][:6]
    mentor_count = db.execute("SELECT COUNT(*) FROM users WHERE role = 'mentor'").fetchone()[0]
    booking_count = db.execute(
        "SELECT COUNT(*) FROM bookings WHERE status IN ('accepted','completed')"
    ).fetchone()[0]
    stats = {
        "mentors": max(750, mentor_count),
        "growth": 85,
        "sessions": max(10000, booking_count),
        "live_mentors": mentor_count,
        "live_sessions": booking_count,
    }
    return render_template(
        "index.html",
        featured=featured,
        categories=CATEGORIES,
        stats=stats,
        today=date.today().isoformat(),
    )


@main_bp.route("/mentors")
def mentors():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    all_mentors = get_mentors()
    rows = list(all_mentors)

    if q:
        needle = q.lower()
        rows = [
            m for m in rows
            if needle in (f"{m['name']} {m['skills'] or ''} {m['headline'] or ''} {m['category'] or ''}").lower()
        ]
    if category and category.lower() != "all":
        rows = [m for m in rows if (m["category"] or "").lower() == category.lower()]

    return render_template(
        "mentors.html",
        mentors=rows,
        all_mentors=all_mentors,
        categories=CATEGORIES,
        q=q,
        category=category,
    )


@main_bp.route("/mentor/<int:mentor_id>")
def mentor_profile(mentor_id):
    mentor = get_mentor(mentor_id)
    if not mentor:
        abort(404)

    reviews = query_db(
        """SELECT r.*, u.name AS mentee_name, u.avatar AS mentee_avatar
           FROM reviews r JOIN users u ON u.id = r.mentee_id
           WHERE r.mentor_id = ? ORDER BY r.id DESC LIMIT 8""",
        (mentor_id,),
    )
    is_favorite = False
    if session.get("user_id"):
        is_favorite = bool(
            query_db(
                "SELECT 1 FROM favorites WHERE mentee_id = ? AND mentor_id = ?",
                (session["user_id"], mentor_id),
                one=True,
            )
        )

    return render_template(
        "mentor_profile.html",
        mentor=mentor,
        reviews=reviews,
        slots=slots_for(mentor),
        is_favorite=is_favorite,
        today=date.today().isoformat(),
        category_label=dict(CATEGORIES).get(mentor["category"], mentor["category"]),
    )
