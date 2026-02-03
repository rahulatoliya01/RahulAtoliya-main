import sqlite3

import streamlit as st

DB_FILE = "college_data.db"

# ------------------ CHAT ------------------
def save_chat(user_id, role, message):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("INSERT INTO chat_history (user_id, role, message) VALUES (?,?,?)",
                (user_id, role, message))
    conn.commit()
    conn.close()

def load_chat_history(user_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("SELECT role, message FROM chat_history WHERE user_id=? ORDER BY id", (user_id,))
    data = cur.fetchall()
    conn.close()
    return data

# ------------------ USERS ------------------
@st.cache_data(ttl=30)
def get_all_users():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            username TEXT UNIQUE,
            mobile TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'student',
            course TEXT,
            year TEXT
        )
    """)
    cur.execute("SELECT * FROM users")
    data = cur.fetchall()
    conn.close()
    return data

def get_user_by_id(user_id):
    """Fetch a single user by id. Returns (id, name, username, mobile, password, role, course, year) or None."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row

def update_user(user_id, name, username, mobile, course, year):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET name=?, username=?, mobile=?, course=?, year=? WHERE id=?",
                    (name, username, mobile, course, year, user_id))
        conn.commit()
        get_all_users.clear()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_password(user_id, new_password):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE users SET password=? WHERE id=?", (new_password, user_id))
    conn.commit()
    conn.close()
    get_all_users.clear()

def delete_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    get_all_users.clear()

# ------------------ DOCUMENTS / NOTICES ------------------
@st.cache_data(ttl=30)
def get_all_documents():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT
        )
    """)
    cur.execute("SELECT * FROM documents")
    data = cur.fetchall()
    conn.close()
    return data

def add_document(title, description):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT INTO documents (title, description) VALUES (?,?)",
                (title, description))
    conn.commit()
    conn.close()
    get_all_documents.clear()
    load_knowledge.clear()

def update_document(doc_id, title, description):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE documents SET title=?, description=? WHERE id=?",
                (title, description, doc_id))
    conn.commit()
    conn.close()
    get_all_documents.clear()
    load_knowledge.clear()

def delete_document(doc_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("DELETE FROM documents WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()
    get_all_documents.clear()
    load_knowledge.clear()

@st.cache_data(ttl=30)
def get_all_notifications():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM notifications")
    data = cur.fetchall()
    conn.close()
    return data

def delete_notification(notif_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("DELETE FROM notifications WHERE id=?", (notif_id,))
    conn.commit()
    conn.close()
    get_all_notifications.clear()
    load_knowledge.clear()

# ------------------ LOAD KNOWLEDGE FOR AI ------------------
@st.cache_data(ttl=60)
def load_knowledge():
    """
    Returns all documents and notifications as a list of dicts
    [{'title': ..., 'description': ...}, ...]
    """
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    # Ensure tables exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT
        )
    """)
    knowledge = []

    cur.execute("SELECT title, description FROM documents")
    for row in cur.fetchall():
        knowledge.append({"title": row[0], "description": row[1]})

    cur.execute("SELECT title, description FROM notifications")
    for row in cur.fetchall():
        knowledge.append({"title": row[0], "description": row[1]})

    conn.close()
    return knowledge
