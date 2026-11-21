-- MentorBridge schema (SQLite3)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('mentor', 'mentee')),
    avatar        TEXT,
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mentor_profiles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    headline        TEXT NOT NULL DEFAULT 'Mentor at MentorBridge',
    bio             TEXT NOT NULL DEFAULT '',
    skills          TEXT NOT NULL DEFAULT '',
    category        TEXT NOT NULL DEFAULT 'Career Guidance',
    experience      INTEGER NOT NULL DEFAULT 0,
    hourly_rate     REAL NOT NULL DEFAULT 0,
    free_slots      TEXT NOT NULL DEFAULT '',
    github_username TEXT NOT NULL DEFAULT '',
    rating          REAL NOT NULL DEFAULT 4.9,
    sessions_count  INTEGER NOT NULL DEFAULT 0,
    verified        INTEGER NOT NULL DEFAULT 1,
    is_available    INTEGER NOT NULL DEFAULT 1,
    updated_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    mentee_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mentor_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic        TEXT NOT NULL,
    session_date TEXT NOT NULL,
    time_slot    TEXT NOT NULL,
    note         TEXT NOT NULL DEFAULT '',
    status       TEXT NOT NULL DEFAULT 'pending'
                 CHECK (status IN ('pending', 'accepted', 'declined', 'completed')),
    meeting_link TEXT NOT NULL DEFAULT '',
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reviews (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    mentor_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mentee_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating     INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment    TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS favorites (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    mentee_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mentor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (mentee_id, mentor_id)
);

CREATE INDEX IF NOT EXISTS idx_bookings_mentee ON bookings(mentee_id);
CREATE INDEX IF NOT EXISTS idx_bookings_mentor ON bookings(mentor_id);
CREATE INDEX IF NOT EXISTS idx_mentor_category ON mentor_profiles(category);
