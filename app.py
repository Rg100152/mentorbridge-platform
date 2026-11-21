"""MentorBridge - full-stack peer-to-peer & expert mentorship platform.

Developer: Raj Gautam
Run: python app.py   ->   http://127.0.0.1:5000
"""
import os
import uuid
from pathlib import Path

from flask import Flask, g, render_template, session

from routes import close_db, get_db
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.main_routes import main_bp

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database" / "mentorbridge.db"


def init_db():
    """Create database folder and all tables if they do not exist yet."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    schema = (BASE_DIR / "database" / "schema.sql").read_text(encoding="utf-8")
    db = get_db()
    db.executescript(schema)
    db.commit()


def create_app():
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("MENTORBRIDGE_SECRET", "dev-only-change-me-" + uuid.uuid4().hex),
        DATABASE=str(DATABASE_PATH),
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(dashboard_bp)
    app.teardown_appcontext(close_db)

    @app.context_processor
    def inject_current_user():
        user = None
        if session.get("user_id"):
            user = get_db().execute(
                "SELECT id, name, email, role, avatar FROM users WHERE id = ?",
                (session["user_id"],),
            ).fetchone()
        return {"current_user": user}

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html"), 404

    with app.app_context():
        init_db()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
