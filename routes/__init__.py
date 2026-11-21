"""Shared database helpers, auth guard and decorators for MentorBridge routes."""
import sqlite3
from functools import wraps

from flask import current_app, flash, g, redirect, session, url_for


def get_db():
    """Open one SQLite connection per request (stored on flask.g)."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query_db(sql, args=(), one=False):
    cursor = get_db().execute(sql, args)
    rows = cursor.fetchall()
    cursor.close()
    return (rows[0] if rows else None) if one else rows


def execute_db(sql, args=()):
    db = get_db()
    cursor = db.execute(sql, args)
    db.commit()
    last_id = cursor.lastrowid
    cursor.close()
    return last_id


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if session.get("role") != role:
                flash("You do not have access to that area.", "warning")
                return redirect(url_for("dashboard.dashboard"))
            return view(*args, **kwargs)

        return wrapped

    return decorator
