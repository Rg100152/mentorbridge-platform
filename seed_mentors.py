"""Seed MentorBridge with 12 realistic mentors, demo accounts, bookings and reviews.

Usage:
    python seed_mentors.py            # seeds only when the database is empty
    python seed_mentors.py --reset    # wipes sample data and seeds again
"""
import sys

from werkzeug.security import generate_password_hash

from app import app
from routes import get_db

DEMO_PASSWORD = "demo1234"


def unsplash(photo_id):
    return f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w=480&q=80"


MENTORS = [
    # (name, email, category, headline, bio, skills, exp, rate, photo, slots, github, rating, sessions)
    ("Aarav Sharma", "mentor@mentorbridge.dev", "Python", "Senior Python Engineer @ Fintech",
     "I help developers go from scripting to shipping production-grade Python. We work on clean architecture, FastAPI/Django, testing and code review.",
     "Python, FastAPI, Django, REST APIs, Docker, Clean Code", 9, 1200,
     "photo-1560250097-0b93528c311a", "Mon 10:00, Tue 18:00, Thu 11:00, Sat 09:30", "aaravsharma", 4.9, 148),
    ("Priya Nair", "priya.nair@mentorbridge.dev", "Cyber Security", "Security Architect & OWASP Advocate",
     "Practical cyber security mentoring: threat modelling, web app pentesting, SOC fundamentals and building a security portfolio that gets you hired.",
     "Cyber Security, Pentesting, OWASP, SIEM, MCP", 8, 1800,
     "photo-1573496359142-b8d87734a5a2", "Mon 16:00, Wed 19:00, Fri 11:30", "priyanair", 5.0, 203),
    ("Arjun Mehta", "arjun.mehta@mentorbridge.dev", "Web Design", "Product Designer & Frontend Mentor",
     "Design systems, accessible UI and pixel-perfect frontend. I review your portfolio and help you present work like a senior designer.",
     "UI/UX, Figma, Web Design, React, Design Systems, CSS", 7, 900,
     "photo-1500648767791-00dcc994a43e", "Tue 14:00, Wed 10:00, Sat 17:00", "arjunmehta", 4.8, 96),
    ("Dr. Kavya Iyer", "kavya.iyer@mentorbridge.dev", "Data Science", "ML Scientist | Ex-Google",
     "From statistics to deployed ML models. Special focus on interview preparation, feature engineering and reproducible data science projects.",
     "Data Science, Machine Learning, Python, Pandas, PyTorch, SQL", 11, 2000,
     "photo-1580489944761-15a19d654956", "Mon 09:00, Thu 16:00, Fri 15:00", "kavya-iyer", 5.0, 312),
    ("Rahul Verma", "rahul.verma@mentorbridge.dev", "Career Guidance", "Career Coach for Tech Professionals",
     "Resume reviews, mock interviews, salary negotiation and 90-day career plans. I have coached 400+ engineers across product and service companies.",
     "Career Guidance, Resume, Interviews, Leadership, Negotiation", 12, 700,
     "photo-1507003211169-0a1dd7228f2d", "Tue 11:00, Thu 18:30, Sun 10:00", "rahulverma", 4.9, 421),
    ("Sneha Kulkarni", "sneha.kulkarni@mentorbridge.dev", "Python", "Django Tech Lead",
     "Backend mentoring with a practical bent: ORM design, async tasks, CI/CD and deployment. Bring your repo and we refactor it together.",
     "Python, Django, PostgreSQL, Celery, AWS, CI/CD", 6, 800,
     "photo-1534528741775-53994a69daeb", "Mon 12:00, Wed 17:00, Fri 10:00", "snehakulkarni", 4.8, 87),
    ("Vikram Rao", "vikram.rao@mentorbridge.dev", "Cyber Security", "Principal Penetration Tester",
     "Learn ethical hacking the right way: recon, exploitation, reporting and OSCP-style lab practice. Beginner friendly, no judgment.",
     "Cyber Security, Pentesting, Burp Suite, Linux, OSCP, Networking", 10, 1500,
     "photo-1519085360753-af0119f7cbe7", "Tue 19:00, Thu 14:00, Sat 11:00", "vikramrao", 4.9, 176),
    ("Meera Joshi", "meera.joshi@mentorbridge.dev", "Web Design", "Frontend Specialist & CSS Wizard",
     "I mentor designers who want to code and developers who want better design taste. Animations, responsive layouts and accessibility included.",
     "Web Design, CSS, JavaScript, Accessibility, Figma, Animations", 5, 600,
     "photo-1494790108377-be9c29b29330", "Mon 15:00, Wed 12:30, Sat 16:00", "meerajoshi", 4.7, 64),
    ("Aditya Bose", "aditya.bose@mentorbridge.dev", "Data Science", "Analytics Manager | SQL Expert",
     "Turn messy data into decisions. SQL optimisation, dashboards, A/B testing and telling a clear story with numbers.",
     "Data Science, SQL, Power BI, A/B Testing, Statistics, Excel", 8, 1300,
     "photo-1506794778202-cad84cf45f1d", "Tue 09:30, Thu 12:00, Fri 18:00", "adityabose", 4.8, 132),
    ("Ananya Das", "ananya.das@mentorbridge.dev", "Career Guidance", "Tech Recruiter turned Career Coach",
     "Get hired faster with a targeted resume, strong LinkedIn profile and interview answers that actually land. Special support for career switchers.",
     "Career Guidance, LinkedIn, Resume, Job Search, Mock Interviews", 9, 500,
     "photo-1531123897727-8f129e1688ce", "Mon 11:30, Wed 15:00, Sat 10:30", "ananyadas", 4.9, 289),
    ("Rohan Gill", "rohan.gill@mentorbridge.dev", "Python", "AI & Backend Developer (Community Mentor)",
     "Free mentoring for beginners! Let us build your first Python project together and get you comfortable with Git, APIs and testing.",
     "Python, Git, APIs, Testing, Beginner Friendly, AI", 4, 0,
     "photo-1568602471122-7832951cc4c5", "Tue 16:00, Fri 14:00, Sun 11:00", "rohangill", 4.9, 58),
    ("Ishita Pandey", "ishita.pandey@mentorbridge.dev", "Data Science", "Senior Data Engineer",
     "Data pipelines, Spark, dbt and cloud warehouses. I help analysts make the jump into data engineering with real projects.",
     "Data Science, Data Engineering, Spark, dbt, Snowflake, Python", 7, 1100,
     "photo-1544005313-94ddf0286df2", "Mon 17:30, Wed 09:00, Thu 15:30", "ishitapandey", 4.8, 104),
]

LEARNERS = [
    ("Demo Learner", "demo@mentorbridge.dev"),
    ("Nikhil Bhatt", "nikhil@example.com"),
    ("Simran Kaur", "simran@example.com"),
]


def seed(reset=False):
    with app.app_context():
        db = get_db()
        existing = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if existing and not reset:
            print(f"Database already has {existing} users. Use --reset to reseed.")
            return

        if reset:
            for table in ("reviews", "favorites", "bookings", "mentor_profiles", "users"):
                db.execute(f"DELETE FROM {table}")
            db.execute("DELETE FROM sqlite_sequence WHERE name IN ('users','mentor_profiles','bookings','reviews','favorites')")

        pw = generate_password_hash(DEMO_PASSWORD)

        for (name, email, category, headline, bio, skills, exp, rate,
             photo, slots, github, rating, sessions) in MENTORS:
            cur = db.execute(
                "INSERT INTO users (name, email, password_hash, role, avatar) VALUES (?, ?, ?, 'mentor', ?)",
                (name, email, pw, unsplash(photo)),
            )
            db.execute(
                """INSERT INTO mentor_profiles
                   (user_id, headline, bio, skills, category, experience, hourly_rate, free_slots,
                    github_username, rating, sessions_count, verified, is_available)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1)""",
                (cur.lastrowid, headline, bio, skills, category, exp, rate,
                 slots, github, rating, sessions),
            )

        mentee_ids = []
        for name, email in LEARNERS:
            cur = db.execute(
                "INSERT INTO users (name, email, password_hash, role, avatar) VALUES (?, ?, ?, 'mentee', ?)",
                (name, email, pw, f"https://api.dicebear.com/9.x/notionists/svg?seed={name.replace(' ', '')}"),
            )
            mentee_ids.append(cur.lastrowid)

        demo, nikhil, simran = mentee_ids
        db.executemany(
            """INSERT INTO bookings (mentee_id, mentor_id, topic, session_date, time_slot, note, status, meeting_link)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (demo, 1, "Python REST API architecture review", "2026-12-02", "10:30 - 11:30",
                 "I am building a FastAPI service and need feedback on structure.", "pending", ""),
                (demo, 2, "Web application threat modelling", "2026-11-28", "16:00 - 17:00",
                 "Preparing for a security interview.", "accepted",
                 "https://meet.jit.si/MentorBridge-demo-4f8a2c91b7e3"),
                (demo, 5, "Mock product manager interview", "2026-11-10", "11:00 - 12:00",
                 "Great session, thank you!", "completed", ""),
                (nikhil, 1, "Django ORM performance tuning", "2026-12-05", "14:00 - 15:00",
                 "Queries are slow on a large table.", "pending", ""),
                (simran, 1, "Transitioning from Java to Python", "2026-12-08", "18:30 - 19:30",
                 "Career switch guidance.", "pending", ""),
                (nikhil, 4, "ML project portfolio review", "2026-12-01", "09:00 - 10:00",
                 "Two Kaggle projects to discuss.", "accepted",
                 "https://meet.jit.si/MentorBridge-demo-9c1d7e2a4b6f"),
            ],
        )
        db.executemany(
            "INSERT INTO reviews (mentor_id, mentee_id, rating, comment) VALUES (?, ?, ?, ?)",
            [
                (2, demo, 5, "Priya explained threat modelling with real examples. Extremely practical session!"),
                (5, demo, 5, "Rahul gave me a clear 90-day plan and reviewed my resume line by line."),
                (4, nikhil, 5, "Kavya is brilliant. The ML interview prep was exactly what I needed."),
                (1, simran, 4, "Very patient and clear explanation of Python internals."),
            ],
        )
        db.execute("INSERT INTO favorites (mentee_id, mentor_id) VALUES (?, ?)", (demo, 4))
        db.execute("INSERT INTO favorites (mentee_id, mentor_id) VALUES (?, ?)", (demo, 5))
        db.commit()
        print("Seed complete: 12 mentors, 3 learners, 6 bookings, 4 reviews.")
        print(f"Mentor login : mentor@mentorbridge.dev / {DEMO_PASSWORD}")
        print(f"Mentee login : demo@mentorbridge.dev / {DEMO_PASSWORD}")


if __name__ == "__main__":
    seed(reset="--reset" in sys.argv)
