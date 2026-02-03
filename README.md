# SVU-MCA Intelligent Student Assistant

AI-powered assistant for MCA students of **Samrat Vikramaditya University, Ujjain**. Built with **Streamlit**, **Google Gemini**, and **SQLite**.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Project Structure](#2-project-structure)
3. [Database Schema](#3-database-schema)
4. [Code Flow (Step by Step)](#4-code-flow-step-by-step)
5. [User Flow](#5-user-flow) — includes [User Flow Diagram](#51-user-flow-diagram)
6. [Backend Deep Dive](#6-backend-deep-dive) — includes [Backend Flow Diagram](#60-backend-flow-diagram) and [Function-to-Function Flow](#601-backend-flow--function-to-function)
7. [UI Components](#7-ui-components)
8. [AI Answer Flow](#8-ai-answer-flow)
9. [Setup & Commands](#9-setup--commands) — includes [Streamlit Cloud Deployment](#deploying-on-streamlit-cloud-step-by-step)

---

## 1. Overview

This section describes the high-level architecture of the application and the technologies used at each layer.

The **SVU-MCA Intelligent Student Assistant** is a web application that allows MCA students to ask questions about their university—schedules, notices, exams, admissions, and more. Administrators can manage users, add documents and notices, and view chat history. The application uses **Streamlit** for the user interface, **SQLite** for data storage, and **Google Gemini** for AI-powered answers. When the database does not contain relevant information, the system falls back to **Google Search** via Gemini's grounding feature to fetch real-time information from the internet.

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Streamlit (Python) | Renders the UI, forms, chat, and admin dashboard without writing HTML/JavaScript. |
| **Backend** | SQLite, Python | Stores users, documents, notifications, and chat history in a file-based database. |
| **AI** | Google Gemini (gemini-2.5-flash) | Generates answers from university data and, when needed, from web search results. |
| **Auth** | streamlit-cookies-manager + session state | Persists login across browser reloads (cookies) and during a session (session state). |
| **Data** | `Data/seed_data.json` → `college_data.db` | Initial data is loaded from JSON; runtime data is stored in SQLite. |

---

## 2. Project Structure

This section explains the folder and file organization and what each file is responsible for.

The project is organized into a single main folder: **AI_Assistant_for_Students**. Inside it you will find the main Python files, the database file, configuration files, and data assets.

```
AI_Assistant_for_Students/
├── app.py              # Main UI, routing, auth screens, dashboard
├── auth.py             # login(), register_user() - credential checks
├── assistant.py        # ask_ai(), get_relevant_knowledge() - Gemini + DB/web
├── db_utils.py         # CRUD for users, documents, chat, load_knowledge
├── database.py         # init_db(), seed_from_json(), migrations
├── college_data.db     # SQLite DB (created at runtime)
├── Data/
│   ├── seed_data.json  # Seed: documents, notifications, users
│   └── college_data.txt
├── images/
│   └── Vikram_University_logo.jpg
├── requirements.txt
└── .env                # GOOGLE_API_KEY (optional)
```

**Detailed explanation of each file:**

- **`app.py`** — This is the entry point of the application. When you run `streamlit run app.py`, Streamlit executes this file from top to bottom on every user interaction. It handles database initialization, cookie management, session restoration, routing (whether to show Login/Register or the Dashboard), and all UI rendering for both admin and student views.

- **`auth.py`** — Contains two core functions: `login()` and `register_user()`. The login function checks if the username or mobile number and password match a row in the `users` table. The register function inserts a new student into the database. Both functions connect directly to SQLite and return success or failure.

- **`assistant.py`** — Handles all AI logic. It defines `ask_ai()`, which takes a user question and recent chat context. Internally it fetches relevant documents from the database, asks Gemini to answer from that data first, and if the answer is not available, triggers a web search via Gemini's grounding tool. It also defines helper functions for keyword extraction and relevance filtering.

- **`db_utils.py`** — Provides all database read/write operations: `get_all_users()`, `get_all_documents()`, `load_chat_history()`, `save_chat()`, `load_knowledge()`, `add_document()`, `delete_user()`, and so on. These functions are used by `app.py` and `assistant.py` to interact with the database. Many of them use Streamlit's `@st.cache_data` to avoid repeated queries.

- **`database.py`** — Handles database setup and seeding. The `init_db()` function creates all four tables if they do not exist. The `_migrate_add_username()` function adds the `username` column to existing databases that were created before this feature. The `seed_from_json()` function reads `Data/seed_data.json` and inserts documents, notifications, and users into the database. The `setup_database()` function is the main entry point that runs both `init_db()` and `seed_from_json()`.

- **`college_data.db`** — This is the SQLite database file. It is created automatically when you first run the application or when you run `python database.py`. It stores all persistent data: users, documents, notifications, and chat history.

- **`Data/seed_data.json`** — A JSON file containing sample data for testing. It has three arrays: `documents`, `notifications`, and `users`. When the application starts or when you run `python database.py`, this data is loaded into the database. Documents and notifications are appended each time; users are inserted only if they do not already exist (checked by username or mobile).

- **`requirements.txt`** — Lists all Python packages needed to run the project. These are installed with `pip install -r requirements.txt`.

- **`.env`** — An optional file where you can store your Google Gemini API key as `GOOGLE_API_KEY=your-key-here`. The `assistant.py` module loads this file and uses the key when making API calls. For production (e.g., Streamlit Cloud), you typically use Streamlit secrets instead.

---

## 3. Database Schema

This section describes each table in the SQLite database, its columns, and why it exists.

### 3.1 `users` table

The `users` table stores all registered users—both administrators and students. Each user has a unique username and a unique mobile number. The application allows login using either username or mobile number along with the password.

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    username TEXT UNIQUE,    -- Login with username OR mobile
    mobile TEXT UNIQUE,
    password TEXT,
    role TEXT,               -- 'admin' or 'student'
    course TEXT,
    year TEXT
);
```

**Explanation of each column:**

- **`id`** — A unique identifier for each user. Auto-incremented by SQLite.
- **`name`** — The full name of the user, displayed in the sidebar and welcome messages.
- **`username`** — A unique handle chosen by the user. Used for login along with mobile.
- **`mobile`** — A unique 10-digit phone number. Also used for login.
- **`password`** — Stored in plain text (for simplicity). In production, passwords should be hashed.
- **`role`** — Either `"admin"` or `"student"`. Admins see the admin menu; students see the chat interface.
- **`course`** — The course the student is enrolled in (e.g., "MCA"). For admins, often "ALL".
- **`year`** — The year of study (e.g., "1st", "2nd"). For admins, often "N/A".

**Why both username and mobile?** Username is a short, memorable identifier. Mobile is a contact number. Supporting both for login gives users flexibility—they can log in with whichever they remember.

### 3.2 `documents` table

The `documents` table stores documents and notices that administrators add. These become part of the AI's knowledge base. When a student asks a question, the system retrieves relevant documents and passes them to Gemini as context.

```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT
);
```

- **`id`** — Unique identifier for each document.
- **`title`** — A short title (e.g., "MCA Syllabus Overview", "Examination Schedule 2024-25").
- **`description`** — The full content of the document. This is what the AI reads to answer questions.

### 3.3 `notifications` table

The `notifications` table has the same structure as `documents`. It stores announcements and notices. Both documents and notifications are combined into a single knowledge base when the AI answers questions.

```sql
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT
);
```

The separation between documents and notifications is mainly organizational. In code, both are read by `load_knowledge()` and merged into one list for the AI.

### 3.4 `chat_history` table

The `chat_history` table stores every message in every conversation. Each row is a single message—either from the user or from the assistant. This allows the application to show previous messages when a student returns and to pass recent context to the AI for follow-up questions.

```sql
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    role TEXT,           -- 'user' or 'assistant'
    message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

- **`user_id`** — Links the message to a user in the `users` table.
- **`role`** — Either `"user"` (the student's message) or `"assistant"` (the AI's reply).
- **`message`** — The text of the message.
- **`timestamp`** — When the message was created. Used for ordering and for the admin's Chat History view.

---

## 4. Code Flow (Step by Step)

This section walks through exactly what happens when the application runs, from startup to handling user actions.

### 4.1 App startup (`app.py`)

When you run `streamlit run app.py`, Streamlit loads `app.py` and executes it from top to bottom. On every user interaction (button click, input change, etc.), the script runs again from the beginning. The flow is:

```
app.py loads
    → ensure_database() [cached]
    → cookies.ready()
    → Restore session from cookies (if not logout)
    → if "role" in session: Dashboard else Auth screens
```

**Step 1: Database setup (cached)**

```python
@st.cache_data
def ensure_database():
    setup_database()
    return True

ensure_database()
```

The `ensure_database()` function calls `setup_database()`, which in turn runs `init_db()` (creates tables, runs migrations) and `seed_from_json()` (loads seed data). The `@st.cache_data` decorator means that after the first successful run, subsequent calls return the cached result (`True`) without executing the function again. This avoids re-creating tables and re-inserting seed data on every page rerun.

**Step 2: Cookie manager**

```python
cookies = EncryptedCookieManager(prefix="svu_mca_", password="svu-mca-super-secret-key")
if not cookies.ready():
    st.stop()
```

The cookie manager stores encrypted user data (user_id, name, role, etc.) in the browser so that when the user refreshes the page or closes and reopens the browser, the application can restore their session. The `cookies.ready()` check ensures that the cookie component has finished loading. If it is not ready, `st.stop()` halts execution so that the app waits instead of proceeding with incomplete cookie state.

**Step 3: Restore session from cookies**

```python
if "role" not in st.session_state and not just_logged_out and cookies.get("user_id"):
    st.session_state.user_id = int(cookies["user_id"])
    st.session_state.name = cookies["name"]
    st.session_state.role = cookies["role"]
    st.session_state.course = cookies.get("course", "")
    st.session_state.year = cookies.get("year", "")
```

When the page loads, `st.session_state` is empty. If the user was previously logged in, their data is stored in cookies. This block checks: (1) there is no role in session (user appears logged out), (2) they did not just log out (we skip restore when `?logout=1` is in the URL), and (3) cookies contain a user_id. If all are true, we copy the user data from cookies into session state. From that point on, the application treats the user as logged in.

**Step 4: Routing**

```python
if "role" not in st.session_state:
    # Show Auth screens (Login / Register)
else:
    # Show Dashboard (Admin or Student view)
```

The presence of `role` in session state is the main routing condition. If it is missing, we show the login and register tabs. If it is present, we show the dashboard. For admins (`role == "admin"`), we show the admin menu (Users, Documents, Chat History, etc.). For students, we show the chat interface.

---

### 4.2 Auth flow

**Login**

When the user enters a username or mobile number and password and clicks "Sign in", the application calls `login(login_id, password)` from `auth.py`:

```python
def login(username_or_mobile, password):
    cur.execute(
        "SELECT id, name, role, course, year FROM users WHERE (username=? OR mobile=?) AND password=?",
        (username_or_mobile, username_or_mobile, password),
    )
    return cur.fetchone()
```

The query uses `username=? OR mobile=?` so that the user can log in with either identifier. The same value is passed twice because we do not know in advance whether they entered a username or a mobile number. If a matching row is found, `fetchone()` returns a tuple; otherwise it returns `None`.

**On success**

If login succeeds, `app.py` saves the user data to both cookies and session state, then reruns the app:

```python
if user:
    cookies["user_id"] = str(user[0])
    cookies["name"] = user[1]
    cookies["role"] = user[2]
    cookies["course"] = user[3]
    cookies["year"] = user[4]
    cookies.save()
    st.session_state.user_id = user[0]
    st.session_state.name = user[1]
    st.session_state.role = user[2]
    st.session_state.course = user[3]
    st.session_state.year = user[4]
    st.toast(f"Welcome {user[1]} 🎓")
    st.rerun()
```

Cookies ensure the user stays logged in after a refresh. Session state is used during the current run. `st.rerun()` triggers a full rerun, and because `role` is now in session state, the dashboard is shown instead of the auth screens.

**Register**

Registration inserts a new row into the `users` table with `role='student'`:

```python
def register_user(name, username, mobile, password, course, year):
    cur.execute("""
        INSERT INTO users (name, username, mobile, password, role, course, year)
        VALUES (?, ?, ?, ?, 'student', ?, ?)
    """, (name, username, mobile, password, course, year))
```

The role is hardcoded to `'student'` because the registration form is only for students. Admin accounts are created via seed data or separate admin tools.

---

### 4.3 Logout flow

When the user clicks Logout, `logout_user()` is called:

```python
def logout_user():
    cookies.clear()
    cookies.save()
    st.session_state.clear()
    st.query_params["logout"] = "1"
    st.rerun()
```

We clear cookies and session state so that the user appears logged out. However, the `streamlit-cookies-manager` library has a known issue where cookie deletion does not always work reliably in the browser. To handle this, we set `st.query_params["logout"] = "1"`, which adds `?logout=1` to the URL. On the next run, we check for this parameter and skip restoring the session from cookies even if they still contain user data. This ensures the user sees the login screen after logout.

---

### 4.4 Student chat flow

When a student sends a message, the application loads their chat history, builds recent context, calls the AI, and saves both the user message and the assistant reply:

```python
history = load_chat_history(st.session_state.user_id)
recent_chat = "\n".join(f"{'User' if r == 'user' else 'Assistant'}: {m}" for r, m in history[-6:])

q = st.chat_input("Ask your question...")
if q:
    ans = ask_ai(q, recent_context=recent_chat)
    save_chat(st.session_state.user_id, "user", q)
    save_chat(st.session_state.user_id, "assistant", ans)
```

`recent_chat` contains the last 6 exchanges (up to 12 messages) formatted as "User: ..." and "Assistant: ...". This is passed to `ask_ai()` as `recent_context` so the AI can understand follow-up questions and maintain conversation coherence.

---

## 5. User Flow

This section describes the end-to-end journey of a user through the application.

| Step | User action | What happens in the application |
|------|-------------|----------------------------------|
| **1** | Opens the app | The app runs `ensure_database()` to create tables and load seed data. The cookie manager initializes. If the user is not logged in and has not just logged out, the Auth screens (Login and Register tabs) are shown. |
| **2** | Registers | The user fills in name, username, mobile, password, course, and year. On "Create account", `register_user()` is called. If successful, the user cache is cleared and a success message is shown. The user must then log in. |
| **3** | Logs in | The user enters username or mobile and password. On "Sign in", `login()` is called. If credentials match, user data is saved to cookies and session state, and the app reruns to show the dashboard. |
| **4** | Uses Admin dashboard | If the user's role is "admin", the sidebar shows Home, Profile, Users, Documents & Notices, Chat History, and Logout. The user can update their profile, view and delete users, add documents, and view chat history across all users. |
| **5** | Uses Student view | If the user's role is "student", the sidebar has Profile, Chat, and Logout. Profile lets the user update name, username, mobile, course, year, and password. Chat shows previous messages and an input to ask questions; `ask_ai()` is called and responses are saved to `chat_history`. |
| **6** | Logs out | When the user clicks Logout, `logout_user()` clears cookies and session state, sets the logout query parameter, and reruns. On the next run, the app skips session restore and shows the login screen. |

### 5.1 User Flow Diagram

```
                                    ┌─────────────────────────────────────┐
                                    │           USER OPENS APP             │
                                    └─────────────────────┬───────────────┘
                                                          │
                                                          ▼
                                    ┌─────────────────────────────────────┐
                                    │  ensure_database() → cookies.ready() │
                                    │  Restore session from cookies?       │
                                    └─────────────────────┬───────────────┘
                                                          │
                                    ┌─────────────────────┴─────────────────────┐
                                    │                                           │
                                    ▼                                           ▼
                    ┌───────────────────────────┐               ┌───────────────────────────┐
                    │  NOT LOGGED IN            │               │  LOGGED IN                │
                    │  Show Auth Screens        │               │  role in session_state    │
                    └─────────────┬─────────────┘               └─────────────┬─────────────┘
                                  │                                           │
                    ┌─────────────┴─────────────┐               ┌─────────────┴─────────────┐
                    │                           │               │                           │
                    ▼                           ▼               ▼                           ▼
        ┌───────────────────┐       ┌───────────────────┐   ┌───────────────┐   ┌───────────────────┐
        │  LOGIN TAB        │       │  REGISTER TAB     │   │  ADMIN        │   │  STUDENT          │
        │  Enter user/pass  │       │  Fill form        │   │  role=admin   │   │  role=student     │
        │  → login()        │       │  → register_user()│   │               │   │                   │
        └─────────┬─────────┘       └─────────┬─────────┘   └───────┬───────┘   └─────────┬─────────┘
                  │                           │                     │                     │
                  │ Success                   │ Success             │                     │
                  ▼                           ▼                     ▼                     ▼
        ┌───────────────────┐       ┌───────────────────┐   ┌───────────────┐   ┌───────────────────┐
        │  Save to cookies  │       │  Show success     │   │  Home         │   │  Load chat history│
        │  + session_state  │       │  → Switch to Login│   │  Users        │   │  Chat input       │
        │  st.rerun()       │       └───────────────────┘   │  Documents    │   │  → ask_ai()       │
        └─────────┬─────────┘                               │  Chat History │   │  save_chat()      │
                  │                                         │  Logout       │   └─────────┬─────────┘
                  └─────────────────────────────────────────┴───────┬───────┴─────────────┘
                                                                    │
                                                                    ▼
                                                        ┌───────────────────────┐
                                                        │  LOGOUT               │
                                                        │  logout_user()        │
                                                        │  Clear cookies/session│
                                                        │  ?logout=1 → rerun    │
                                                        └───────────────────────┘
```

---

## 6. Backend Deep Dive

### 6.0 Backend Flow Diagram

High-level flow of data and components in the backend:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    BACKEND ARCHITECTURE                                           │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                   │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────────────────┐    │
│   │   app.py    │─────▶│  auth.py    │─────▶│ college_    │◀─────│  Data/seed_data.json    │    │
│   │   (UI)      │      │  login()    │      │  data.db    │      │  (initial seed)         │    │
│   │             │      │  register() │      │  (SQLite)   │      └─────────────────────────┘    │
│   └──────┬──────┘      └─────────────┘      └──────┬──────┘                                      │
│          │                                        │                                               │
│          │              ┌─────────────┐           │                                               │
│          └─────────────▶│  db_utils   │◀──────────┘                                               │
│                         │  CRUD ops   │                                                           │
│                         │  caching    │                                                           │
│                         └──────┬──────┘                                                           │
│                                │                                                                  │
│          ┌─────────────────────┼─────────────────────┐                                            │
│          │                     │                     │                                            │
│          ▼                     ▼                     ▼                                            │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────────┐                                  │
│   │  database   │      │  assistant  │      │  Google Gemini  │                                  │
│   │  init_db()  │      │  ask_ai()   │─────▶│  API            │                                  │
│   │  seed_*()   │      │  load_      │      │  (+ Web Search   │                                  │
│   └─────────────┘      │  knowledge()│      │   when needed)   │                                  │
│                        └─────────────┘      └─────────────────┘                                  │
│                                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.0.1 Backend Flow — Function to Function

Detailed call flow showing which functions invoke which:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                         FUNCTION-TO-FUNCTION CALL FLOW                                             │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════════════════════════
  APP STARTUP (app.py)
═══════════════════════════════════════════════════════════════════════════════════════════════════

  ensure_database()  ──────▶  setup_database()  ──────▶  init_db()
       │                              │                      │
       │                              │                      ├──▶ CREATE TABLE users
       │                              │                      ├──▶ CREATE TABLE documents
       │                              │                      ├──▶ CREATE TABLE notifications
       │                              │                      ├──▶ CREATE TABLE chat_history
       │                              │                      └──▶ _migrate_add_username(conn)
       │                              │
       │                              └──────────────▶  seed_from_json()
       │                                                    │
       │                                                    ├──▶ read Data/seed_data.json
       │                                                    ├──▶ INSERT INTO documents
       │                                                    ├──▶ INSERT INTO notifications
       │                                                    └──▶ INSERT INTO users (if not exists)
       │
       └──▶ returns True (cached)

═══════════════════════════════════════════════════════════════════════════════════════════════════
  LOGIN (app.py → auth.py)
═══════════════════════════════════════════════════════════════════════════════════════════════════

  app.py: user = login(login_id, password)
              │
              └──▶ auth.login(username_or_mobile, password)
                        │
                        └──▶ sqlite3.connect() → SELECT from users WHERE (username=? OR mobile=?)
                             return user tuple or None

═══════════════════════════════════════════════════════════════════════════════════════════════════
  REGISTER (app.py → auth.py → db_utils)
═══════════════════════════════════════════════════════════════════════════════════════════════════

  app.py: register_user(name, username, mobile, ...)
              │
              └──▶ auth.register_user(...)
                        │
                        └──▶ INSERT INTO users
                             return True/False
              │
              └──▶ get_all_users.clear()   [if success, invalidate cache]

═══════════════════════════════════════════════════════════════════════════════════════════════════
  ADMIN: USERS (app.py → db_utils)
═══════════════════════════════════════════════════════════════════════════════════════════════════

  app.py: get_all_users()
              │
              └──▶ db_utils.get_all_users()
                        │
                        └──▶ SELECT * FROM users  [cached 30s]

  app.py: delete_user(u[0])
              │
              └──▶ db_utils.delete_user(user_id)
                        │
                        ├──▶ DELETE FROM users WHERE id=?
                        └──▶ get_all_users.clear()

═══════════════════════════════════════════════════════════════════════════════════════════════════
  ADMIN: DOCUMENTS (app.py → db_utils)
═══════════════════════════════════════════════════════════════════════════════════════════════════

  app.py: add_document(title, desc)
              │
              └──▶ db_utils.add_document(title, description)
                        │
                        ├──▶ INSERT INTO documents
                        ├──▶ get_all_documents.clear()
                        └──▶ load_knowledge.clear()

  app.py: get_all_documents()
              │
              └──▶ db_utils.get_all_documents()
                        │
                        └──▶ SELECT * FROM documents  [cached 30s]

═══════════════════════════════════════════════════════════════════════════════════════════════════
  STUDENT: CHAT (app.py → db_utils → assistant)
═══════════════════════════════════════════════════════════════════════════════════════════════════

  app.py: load_chat_history(user_id)
              │
              └──▶ db_utils.load_chat_history(user_id)
                        │
                        └──▶ SELECT role, message FROM chat_history WHERE user_id=? ORDER BY id

  app.py: ask_ai(q, recent_context=recent_chat)
              │
              └──▶ assistant.ask_ai(question, recent_context)
                        │
                        ├──▶ get_relevant_knowledge(question)
                        │         │
                        │         ├──▶ load_knowledge()  ◀── db_utils.load_knowledge()
                        │         │         │
                        │         │         ├──▶ SELECT FROM documents
                        │         │         └──▶ SELECT FROM notifications  [cached 60s]
                        │         │
                        │         └──▶ _extract_keywords(question)
                        │                   └──▶ filter by keyword overlap
                        │
                        ├──▶ _answer_from_db(question, knowledge_text, recent_context)
                        │         │
                        │         └──▶ client.models.generate_content()  [Gemini API, no web]
                        │
                        └──▶ if [NEED_WEB_SEARCH] in answer:
                                  │
                                  └──▶ _answer_with_web_search(question)
                                            │
                                            └──▶ client.models.generate_content(config=GoogleSearch)

  app.py: save_chat(user_id, "user", q)
  app.py: save_chat(user_id, "assistant", ans)
              │
              └──▶ db_utils.save_chat(user_id, role, message)
                        │
                        └──▶ INSERT INTO chat_history

═══════════════════════════════════════════════════════════════════════════════════════════════════
  LOGOUT (app.py)
═══════════════════════════════════════════════════════════════════════════════════════════════════

  logout_user()
      │
      ├──▶ cookies.clear()
      ├──▶ cookies.save()
      ├──▶ st.session_state.clear()
      ├──▶ st.query_params["logout"] = "1"
      └──▶ st.rerun()
```

---

### 6.1 `database.py`

This section explains the backend modules in detail: database setup, data access, and authentication.

### 6.1 `database.py`

**init_db()**

This function creates all four tables if they do not exist:

```python
def init_db():
    cur.execute("CREATE TABLE IF NOT EXISTS users (...)")
    cur.execute("CREATE TABLE IF NOT EXISTS documents (...)")
    cur.execute("CREATE TABLE IF NOT EXISTS notifications (...)")
    cur.execute("CREATE TABLE IF NOT EXISTS chat_history (...)")
    _migrate_add_username(conn)
```

`CREATE TABLE IF NOT EXISTS` means that if a table already exists, it is left unchanged. After creating the tables, `_migrate_add_username()` runs to handle databases created before the username column was added.

**_migrate_add_username()**

For existing databases that only had `mobile` and no `username`, this migration adds the column and backfills it:

```python
def _migrate_add_username(conn):
    cur.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cur.fetchall()]
    if "username" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN username TEXT")
        cur.execute("UPDATE users SET username = mobile WHERE username IS NULL")
```

`PRAGMA table_info(users)` returns the list of columns. If `username` is missing, we add it and set `username = mobile` for existing rows so that old users can still log in.

**seed_from_json()**

This function reads `Data/seed_data.json` and inserts documents, notifications, and users:

```python
for user in data.get("users", []):
    username = user.get("username", user["mobile"])
    cur.execute("SELECT id FROM users WHERE username = ? OR mobile = ?", (username, user["mobile"]))
    if cur.fetchone() is None:
        cur.execute("INSERT INTO users (name, username, mobile, ...) VALUES (...)")
```

For users, we first check if a user with the same username or mobile already exists. We only insert if no row is found. Documents and notifications are inserted every time (they are appended, not checked for duplicates).

---

### 6.2 `db_utils.py`

**Caching**

Functions like `get_all_users()`, `get_all_documents()`, and `load_knowledge()` are decorated with `@st.cache_data(ttl=...)`:

```python
@st.cache_data(ttl=30)
def get_all_users():
    # ...
```

This means Streamlit caches the return value. If the function is called again with the same arguments within the TTL (time to live), the cached result is returned instead of running the database query again. This reduces load and speeds up the app.

**Cache invalidation**

When data changes (e.g., a document is added or a user is deleted), we must clear the relevant cache so the next read sees the new data:

```python
def add_document(title, description):
    # ... insert into database ...
    get_all_documents.clear()
    load_knowledge.clear()
```

`get_all_documents.clear()` and `load_knowledge.clear()` remove the cached results for those functions. The next call will hit the database and return fresh data.

**load_knowledge()**

This function combines documents and notifications into a single list of dicts used by the AI:

```python
@st.cache_data(ttl=60)
def load_knowledge():
    cur.execute("SELECT title, description FROM documents")
    # ...
    cur.execute("SELECT title, description FROM notifications")
    # ...
    return [{"title": ..., "description": ...}, ...]
```

The AI receives this list and uses it as context when answering questions. The 60-second TTL means the knowledge base is refreshed at most once per minute unless a document or notification is added (which clears the cache immediately).

---

### 6.3 `auth.py`

**login()**

The login function executes a single SQL query that matches either username or mobile, plus the password:

```python
cur.execute(
    "SELECT id, name, role, course, year FROM users WHERE (username=? OR mobile=?) AND password=?",
    (username_or_mobile, username_or_mobile, password),
)
```

We pass `username_or_mobile` twice because the same input could match either column. If a row is found, we return the tuple; otherwise we return `None`.

**register_user()**

Registration uses a try/except to handle duplicate username or mobile:

```python
try:
    cur.execute("INSERT INTO users ...")
    conn.commit()
    return True
except sqlite3.IntegrityError:
    return False
```

If the username or mobile already exists, the UNIQUE constraint causes an `IntegrityError`. We catch it and return `False` so the UI can show "Username or mobile is already registered."

---

## 7. UI Components

This section describes the main UI elements and how they are built.

### 7.1 Auth screens

The auth screen uses a two-column layout: a branding panel on the left and the form on the right.

**Layout**

```python
col_brand, col_form = st.columns([1, 1])
with col_brand:
    st.markdown('<div class="svu-auth-brand">...</div>')
with col_form:
    tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])
```

`st.columns([1, 1])` creates two equal-width columns. The left column displays HTML with a blue gradient background describing the application. The right column contains two tabs: Login and Register. This keeps the form focused while providing context on the left.

**Login form**

The login tab has two text inputs (username/mobile and password) and a Sign in button. The login identifier field accepts either a username or a mobile number, as supported by the backend.

**Register form**

The register tab has fields for name, username, mobile, password, course, and year. Course and year are in a two-column row. Validation checks that all required fields are filled, the password is at least 6 characters, and the mobile has at least 10 digits. If `register_user()` returns `False` (duplicate username or mobile), an error message is shown.

---

### 7.2 Admin dashboard

**Sidebar menu**

The admin sidebar lists menu items as buttons. Clicking a button updates `st.session_state.admin_menu` and, for Logout, calls `logout_user()`:

```python
admin_menu_items = [
    ("Home", "🏠 Home"),
    ("Users", "👥 Users"),
    ("Documents & Notices", "📄 Documents & Notices"),
    ("Chat History", "💬 Chat History"),
    ("Logout", "⏏ Logout"),
]
for value, label in admin_menu_items:
    if st.button(label):
        st.session_state.admin_menu = value
        if value == "Logout":
            logout_user()
```

**Users table**

The Users view calls `get_all_users()` and displays each user in columns: Name, Username, Mobile, Role, Course, Year, and a Delete button. The delete button calls `delete_user(u[0])` and reruns the app to refresh the list.

**Documents**

The Documents view has a form to add a new document (title and description) and a list of existing documents. Adding a document calls `add_document()`, which clears the relevant caches.

**Chat history**

The Chat History view runs a direct SQL query joining `chat_history` and `users` to show the latest 50 messages across all users, with the sender's name and timestamp.

---

### 7.3 Student chat

The student view shows previous messages using `st.chat_message()` and a chat input with `st.chat_input()`. When the user sends a message, `ask_ai()` is called and the result is displayed. Both the user message and the assistant reply are saved with `save_chat()`.

---

### 7.4 CSS

All styling is inline CSS in `app.py` using `st.markdown(..., unsafe_allow_html=True)`. Key classes include:

- **`.svu-auth-brand`** — Blue gradient background for the left auth panel.
- **`.svu-sidebar-section-title`** — Uppercase, small text for section headers in the admin sidebar.
- **`.svu-nav-item-active`** — Highlights the currently selected admin menu item.
- Button styles for primary actions and sidebar buttons (rounded, hover effects).

---

## 8. AI Answer Flow

This section explains how the AI answers a student's question, from keyword filtering to database context and web search fallback.

### 8.1 Overview

The flow is:

1. Extract keywords from the question.
2. Retrieve relevant documents and notifications from the database.
3. Ask Gemini to answer using only that context.
4. If Gemini indicates it cannot answer (response contains `[NEED_WEB_SEARCH]`), call Gemini again with Google Search grounding.
5. Return the final answer to the user.

### 8.2 Keyword relevance

Before sending the full knowledge base to the AI, we filter it by relevance to reduce token usage and improve accuracy:

```python
def _extract_keywords(question: str) -> set:
    words = re.findall(r"\b\w{2,}\b", question.lower())
    return {w for w in words if w not in STOPWORDS}

def get_relevant_knowledge(question: str) -> list[dict]:
    knowledge = load_knowledge()
    keywords = _extract_keywords(question)
    relevant = [k for k in knowledge if any(kw in (k["title"] + " " + k["description"]).lower() for kw in keywords)]
    return relevant if relevant else knowledge
```

`_extract_keywords()` splits the question into words of length 2 or more and removes common stopwords (e.g., "the", "is", "what"). `get_relevant_knowledge()` keeps only documents whose title or description contains at least one of those keywords. If no document matches, we return the full knowledge list so the AI still has context.

### 8.3 DB-only answer

We first ask Gemini to answer only from the provided university data and to respond with `[NEED_WEB_SEARCH]` if it cannot:

```python
DB_ONLY_PROMPT = (
    "Answer ONLY using the university data provided below. "
    "If the question CANNOT be answered from the provided data, respond with exactly: [NEED_WEB_SEARCH]"
)
response = client.models.generate_content(model="gemini-2.5-flash", contents=full_prompt)
```

This ensures we prefer database content and only use web search when necessary.

### 8.4 Web fallback

If the response contains `[NEED_WEB_SEARCH]`, we call Gemini again with the Google Search tool enabled:

```python
if SEARCH_WEB_MARKER in answer:
    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    config = types.GenerateContentConfig(tools=[grounding_tool])
    response = client.models.generate_content(..., config=config)
```

Gemini then searches the web and grounds its answer in real-time information. If the Google Search types are not available (e.g., older SDK), we return a message asking the user to check the university website.

### 8.5 Caching

`ask_ai()` is cached for 5 minutes:

```python
@st.cache_data(ttl=300)
def ask_ai(question, recent_context: str = "") -> str:
    # ...
```

If the same question (and context) is asked again within 5 minutes, the cached answer is returned. This reduces API cost and latency for repeated questions.

---

## 9. Setup & Commands

This section provides step-by-step setup instructions and a summary of useful commands.

### Prerequisites

- **Python 3.10 or higher** — Required for Streamlit and the Google GenAI library.
- **Google Gemini API key** — Obtain one from [Google AI Studio](https://aistudio.google.com/apikey).

### Step 1: Clone or download the project

Place the project folder on your machine (e.g., on your Desktop). Ensure the folder structure is intact.

### Step 2: Create and activate a virtual environment (recommended)

A virtual environment isolates project dependencies from other Python projects.

**On macOS or Linux:**

```bash
cd AI_Assistant_for_Students
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows (PowerShell):**

```bash
cd AI_Assistant_for_Students
python -m venv .venv
.venv\Scripts\activate
```

After activation, your shell prompt usually shows `(.venv)`.

### Step 3: Install dependencies

Install all required packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

This installs Streamlit, google-genai, streamlit-cookies-manager, and python-dotenv.

### Step 4: Upgrade dependencies (optional)

To update packages to their latest compatible versions:

```bash
pip install -r requirements.txt --upgrade
```

### Step 5: Set your Google Gemini API key

The application needs a Gemini API key to generate answers. You can provide it in two ways:

**Option A: Create a `.env` file**

In the project root (`AI_Assistant_for_Students/`), create a file named `.env` with:

```
GOOGLE_API_KEY=your-gemini-api-key-here
```

Replace `your-gemini-api-key-here` with your actual key. The `assistant.py` module loads this file automatically.

**Option B: Export as an environment variable**

**macOS/Linux:**

```bash
export GOOGLE_API_KEY="your-gemini-api-key-here"
```

**Windows (PowerShell):**

```powershell
$env:GOOGLE_API_KEY="your-gemini-api-key-here"
```

For Streamlit Cloud deployment, use the Secrets section and add `GOOGLE_API_KEY = "..."` in TOML format.

### Step 6: Initialize the database

Run the database setup script to create tables and load seed data:

```bash
python database.py
```

This script runs `init_db()` (creates tables, runs migrations) and `seed_from_json()` (loads `Data/seed_data.json`). If `seed_data.json` exists, documents, notifications, and users from that file are inserted. Otherwise, default admin and student users are created.

### Step 7: Run the application

Start the Streamlit server:

```bash
streamlit run app.py
```

The app opens in your browser at `http://localhost:8501`. You should see the Login and Register tabs. Use the default credentials (e.g., username `admin`, password `admin123`) if they were seeded.

### Deploying on Streamlit Cloud (Step by Step)

This section walks you through deploying the SVU-MCA Assistant on **Streamlit Community Cloud** so it can be accessed online.

#### Prerequisites

- A **GitHub** account ([github.com](https://github.com))
- A **Streamlit Community Cloud** account (sign up with GitHub at [share.streamlit.io](https://share.streamlit.io))
- Your project pushed to a **GitHub repository**
- A **Google Gemini API key** from [Google AI Studio](https://aistudio.google.com/apikey)

---

#### Step 1: Push the project to GitHub

1. **Create a new repository** on GitHub (if you have not already):
   - Go to [github.com/new](https://github.com/new)
   - Enter a repository name (e.g., `AI_Assistant_for_Students`)
   - Choose Public
   - Click **Create repository**

2. **Initialize Git and push** (if the project is not yet in Git):

   ```bash
   cd AI_Assistant_for_Students
   git init
   git add .
   git commit -m "Initial commit: SVU-MCA Assistant"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git push -u origin main
   ```

   Replace `YOUR_USERNAME` and `YOUR_REPO_NAME` with your GitHub username and repository name.

3. **Ensure required files are included**:
   - `app.py`
   - `auth.py`
   - `assistant.py`
   - `db_utils.py`
   - `database.py`
   - `requirements.txt`
   - `Data/seed_data.json`
   - `images/Vikram_University_logo.jpg` (if used)

4. **Do not commit** `.env` or `college_data.db` (add them to `.gitignore`). Secrets will be set in Streamlit Cloud.

---

#### Step 2: Sign in to Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **Sign in with GitHub**
3. Authorize Streamlit to access your GitHub account

---

#### Step 3: Create a new app

1. On the Streamlit Cloud dashboard, click **"New app"** (or **"Create app"**)
2. You will see the app creation form with these fields:
   - **Repository**
   - **Branch**
   - **Main file path**
   - **App URL** (optional)

---

#### Step 4: Configure the repository and main file

1. **Repository**: Select your GitHub repository (e.g., `YOUR_USERNAME/AI_Assistant_for_Students`)

2. **Branch**: Select `main` (or the branch where your code is pushed)

3. **Main file path**: Enter the path to your Streamlit app file.  
   Because the app is inside a subfolder, use:

   ```
   AI_Assistant_for_Students/app.py
   ```

   Or, if the repo root is the project folder:

   ```
   app.py
   ```

4. **App URL** (optional): You can set a custom URL like `svu-mca-assistant` so the app is at `https://svu-mca-assistant.streamlit.app`

---

#### Step 5: Add secrets (Google API key)

The app needs the Google Gemini API key. Do **not** put it in your code or in a committed file. Use Streamlit Cloud Secrets:

1. In the app creation form, expand **"Advanced settings"** (or find **"Secrets"**)
2. Click **"Secrets"** or **"Open in TOML format"**
3. Add your API key in TOML format:

   ```toml
   GOOGLE_API_KEY = "your-gemini-api-key-here"
   ```

4. Replace `your-gemini-api-key-here` with your actual API key from Google AI Studio

5. Save the secrets (they are encrypted and not visible in logs or the UI)

---

#### Step 6: Deploy the app

1. Click **"Deploy!"** (or **"Create app"**)
2. Streamlit Cloud will:
   - Clone your repository
   - Create a Python environment
   - Run `pip install -r requirements.txt` (from the repo root; ensure `requirements.txt` is in the correct path)
3. The build may take 2–5 minutes
4. When done, you will see **"Your app is live!"** and a link like `https://your-app-name.streamlit.app`

---

#### Step 7: Verify the deployment

1. Open the app URL in your browser
2. You should see the Login and Register tabs
3. The database is initialized on first run. If `Data/seed_data.json` is in the repo, seed data is loaded
4. Log in with the default credentials (e.g., `admin` / `admin123`) if they were seeded
5. Test the chat as a student and the admin menu as admin

---

#### Important notes

| Topic | Details |
|-------|---------|
| **Database** | SQLite uses the ephemeral filesystem. Data may be lost when the app sleeps or restarts. For production, use a hosted database (e.g., PostgreSQL, Supabase). |
| **Requirements path** | Streamlit Cloud looks for `requirements.txt` in the same directory as the main file. If main file is `AI_Assistant_for_Students/app.py`, ensure `requirements.txt` exists in `AI_Assistant_for_Students/`. If the repo root is the project folder, use `app.py` as main file and keep `requirements.txt` in the root. |
| **Secrets** | Never commit API keys. Always use Streamlit Secrets for sensitive values. |
| **Free tier** | Free apps may sleep after inactivity. The first request after sleep can take longer to load. |
| **Logs** | Use the **Logs** tab in the Streamlit Cloud dashboard to debug build or runtime errors. |

---

## Quick Reference

### Default login credentials (from seed)

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Student | `student` | `student123` |

### Cache TTL values

| Function | TTL | Purpose |
|----------|-----|---------|
| get_all_users, get_all_documents | 30 seconds | Balance freshness with performance for admin views |
| load_knowledge | 60 seconds | AI knowledge base refreshed every minute |
| ask_ai | 5 minutes | Avoid repeated API calls for duplicate questions |
