import json
import sqlite3
from pathlib import Path

DB_FILE = "college_data.db"
SEED_JSON = Path(__file__).parent / "Data" / "seed_data.json"


def init_db():
    """Create all required tables if they do not exist."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            username TEXT UNIQUE,
            mobile TEXT UNIQUE,
            password TEXT,
            role TEXT,
            course TEXT,
            year TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    _migrate_add_username(conn)
    conn.commit()
    conn.close()


def _migrate_add_username(conn):
    """Add username column if missing (migration for existing DBs)."""
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cur.fetchall()]
    if "username" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN username TEXT")
        cur.execute("UPDATE users SET username = mobile WHERE username IS NULL")


def seed_default_users():
    """
    Insert default admin and student users if they do not already exist.

    - Admin:
        username/mobile: admin
        password: admin123
    - Student:
        username/mobile: student
        password: student123
    """
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Admin user
    cur.execute("SELECT id FROM users WHERE username = ? OR mobile = ?", ("admin", "admin"))
    if cur.fetchone() is None:
        cur.execute(
            """
            INSERT INTO users (name, username, mobile, password, role, course, year)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("Admin User", "admin", "9999999999", "admin123", "admin", "ALL", "N/A"),
        )

    # Student user
    cur.execute("SELECT id FROM users WHERE username = ? OR mobile = ?", ("student", "student"))
    if cur.fetchone() is None:
        cur.execute(
            """
            INSERT INTO users (name, username, mobile, password, role, course, year)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("Demo Student", "student", "8888888888", "student123", "student", "MCA", "1st"),
        )

    conn.commit()
    conn.close()


def seed_from_json():
    """
    Load seed data from Data/seed_data.json and insert into DB.
    Users are inserted only if mobile does not already exist.
    Documents and notifications are appended (safe to run multiple times for testing).
    """
    if not SEED_JSON.exists():
        seed_default_users()
        return

    with open(SEED_JSON, encoding="utf-8") as f:
        data = json.load(f)

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    for doc in data.get("documents", []):
        cur.execute(
            "INSERT INTO documents (title, description) VALUES (?, ?)",
            (doc["title"], doc["description"]),
        )

    for notif in data.get("notifications", []):
        cur.execute(
            "INSERT INTO notifications (title, description) VALUES (?, ?)",
            (notif["title"], notif["description"]),
        )

    for user in data.get("users", []):
        username = user.get("username", user["mobile"])
        cur.execute("SELECT id FROM users WHERE username = ? OR mobile = ?", (username, user["mobile"]))
        if cur.fetchone() is None:
            cur.execute(
                """
                INSERT INTO users (name, username, mobile, password, role, course, year)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user["name"],
                    username,
                    user["mobile"],
                    user["password"],
                    user["role"],
                    user["course"],
                    user["year"],
                ),
            )

    conn.commit()
    conn.close()


def setup_database():
    """
    Public helper to initialize DB and seed data.
    Uses Data/seed_data.json if present, otherwise falls back to default users.
    Safe to call multiple times (idempotent).
    """
    init_db()
    seed_from_json()


if __name__ == "__main__":
    setup_database()
    print("✅ Database initialized and seeded from Data/seed_data.json")
