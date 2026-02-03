import sqlite3

def login(username_or_mobile, password):
    """Login with username or mobile number."""
    conn = sqlite3.connect("college_data.db")
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, role, course, year FROM users WHERE (username=? OR mobile=?) AND password=?",
        (username_or_mobile, username_or_mobile, password),
    )
    user = cur.fetchone()
    conn.close()
    return user


def register_user(name, username, mobile, password, course, year):
    conn = sqlite3.connect("college_data.db")
    cur = conn.cursor()
    try:
        cur.execute("""
        INSERT INTO users (name, username, mobile, password, role, course, year)
        VALUES (?, ?, ?, ?, 'student', ?, ?)
        """, (name, username, mobile, password, course, year))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
