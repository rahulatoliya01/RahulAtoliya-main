import sqlite3

conn = sqlite3.connect("college_data.db")
cur = conn.cursor()

cur.execute("""
INSERT INTO users (name, mobile, password, role, course, year)
VALUES (?, ?, ?, ?, ?, ?)
""", (
    "Admin SVU",
    "9999999999",
    "admin123",
    "admin",
    "ALL",
    "2"
))

conn.commit()
conn.close()

print("Admin user created")
