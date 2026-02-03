import streamlit as st
import sqlite3

from auth import login, register_user
from assistant import ask_ai
from db_utils import (
    save_chat,
    load_chat_history,
    get_all_users,
    get_all_documents,
    get_all_notifications,
    get_user_by_id,
    update_user,
    update_password,
    delete_user,
    add_document,
    update_document,
    delete_document,
    delete_notification,
)
from database import setup_database

from streamlit_cookies_manager import EncryptedCookieManager


# ================= INITIAL SETUP =================
@st.cache_data
def ensure_database():
    setup_database()
    return True


ensure_database()


# ================= COOKIES =================
cookies = EncryptedCookieManager(
    prefix="svu_mca_",
    password="svu-mca-super-secret-key"
)

if not cookies.ready():
    st.stop()


# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="SVU-MCA Assistant",
    page_icon="🎓",
    layout="wide",
)


# ================= CSS =================
st.markdown(
    """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
/* Do NOT hide header - it contains the sidebar collapse/expand button */
[data-testid="stSidebar"] {
    width: 260px;
    background: linear-gradient(180deg, #0f172a 0%, #020617 40%, #020617 100%);
    color: #e5e7eb;
}

[data-testid="stSidebar"] h3, 
[data-testid="stSidebar"] p, 
[data-testid="stSidebar"] span {
    color: #e5e7eb !important;
}

/* General typography */
html, body, [class*="css"]  {
    font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

/* Card-like container */
.svu-card {
    padding: 1.5rem 1.75rem;
    border-radius: 0.75rem;
    background-color: #ffffff;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
}

/* Auth branding panel */
.svu-auth-brand {
    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #2563eb 100%);
    border-radius: 1rem;
    padding: 2.5rem;
    color: white;
    height: 100%;
    min-height: 320px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.svu-auth-brand h2 { margin: 0 0 0.5rem 0; font-size: 1.5rem; font-weight: 700; }
.svu-auth-brand p { margin: 0; opacity: 0.9; font-size: 0.95rem; line-height: 1.6; }

/* Input focus styling */
.stTextInput > div > div > input:focus {
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.3);
    border-color: #2563eb;
}

/* Auth section labels */
.svu-auth-label { font-size: 0.85rem; font-weight: 600; color: #475569; margin-bottom: 0.25rem; }

/* Primary accent color */
.svu-accent {
    color: #2563eb;
}

/* Primary buttons */
div.stButton > button[kind="primary"],
div.stButton > button {
    border-radius: 999px;
    background: linear-gradient(90deg, #2563eb, #1d4ed8);
    color: #ffffff;
    border: none;
    padding: 0.55rem 1.4rem;
    font-weight: 600;
    letter-spacing: 0.01em;
}

div.stButton > button:hover {
    background: linear-gradient(90deg, #1d4ed8, #1e40af);
    box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.25), 0 6px 14px rgba(15, 23, 42, 0.25);
}

/* Sidebar buttons (e.g., Logout) */
section[data-testid="stSidebar"] div.stButton > button {
    width: 100%;
    border-radius: 999px;
    border: 1px solid rgba(148, 163, 184, 0.7);
    background: rgba(15, 23, 42, 0.8);
    color: #e5e7eb;
    font-weight: 500;
}

section[data-testid="stSidebar"] div.stButton > button:hover {
    background-color: rgba(37, 99, 235, 0.35);
    border-color: rgba(37, 99, 235, 0.9);
}

/* Admin menu: custom vertical nav using markdown + buttons */
.svu-sidebar-section-title {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #9ca3af;
    margin-bottom: 0.25rem;
}

/* Sidebar nav items */
.svu-nav-item {
    margin-bottom: 0.15rem;
}

.svu-nav-item button {
    width: 100%;
    justify-content: flex-start;
    background: transparent;
    border-radius: 999px;
    border: 1px solid transparent;
    color: #e5e7eb;
    font-weight: 500;
    padding-left: 0.9rem;
}

.svu-nav-item button:hover {
    background-color: rgba(37, 99, 235, 0.25);
}

.svu-nav-item-active button {
    background: linear-gradient(90deg, #2563eb, #1d4ed8);
    border-color: rgba(191, 219, 254, 0.6);
    color: #f9fafb;
    box-shadow: 0 0 0 1px rgba(191, 219, 254, 0.6);
}
</style>
""",
    unsafe_allow_html=True,
)


# ================= LOGOUT FUNCTION =================
def logout_user():
    cookies.clear()
    cookies.save()
    st.session_state.clear()
    st.query_params["logout"] = "1"  # Signal logout (cookies often fail to delete)
    st.rerun()


# ================= STUDENT HOME SECTION =================
def _render_student_home():
    """Render the student home page with assistant info and how-to, styled like login UI."""
    col_info, col_nav = st.columns([1, 1])
    with col_info:
        st.markdown(
            """
            <div class="svu-auth-brand">
                <h2>🎓 SVU-MCA Assistant</h2>
                <p style="margin-top: 1rem;">Welcome, <strong>{name}</strong>! Your intelligent assistant for MCA at Samrat Vikramaditya University, Ujjain.</p>
                <p style="margin-top: 1.25rem; font-size: 0.95rem;">Ask questions about schedules, notices, exams, admissions, syllabus, and more. Responses are powered by Google Gemini and official university documents.</p>
                <h3 style="margin-top: 1.5rem; font-size: 1rem;">How to use</h3>
                <ul style="margin: 0.5rem 0 0 0; padding-left: 1.25rem; opacity: 0.95;">
                    <li>Go to <strong>Chat</strong> to ask questions</li>
                    <li>View past conversations in <strong>Chat History</strong></li>
                    <li>Update your details in <strong>Profile</strong></li>
                </ul>
            </div>
            """.format(name=st.session_state.get("name", "Student")),
            unsafe_allow_html=True,
        )
    with col_nav:
        st.markdown("### Navigation")
        st.markdown(
            """
            <div class="svu-card" style="margin-top: 0.5rem;">
                <p style="margin: 0 0 0.75rem 0; font-weight: 600; color: #334155;">Project flow</p>
                <ol style="margin: 0; padding-left: 1.25rem; color: #475569; line-height: 2;">
                    <li><strong>Home</strong> — Overview & how to use</li>
                    <li><strong>Chat</strong> — Ask questions</li>
                    <li><strong>Chat History</strong> — View past conversations</li>
                    <li><strong>Profile</strong> — Update your information</li>
                    <li><strong>Logout</strong> — Sign out</li>
                </ol>
                <p style="margin-top: 1.25rem; margin-bottom: 0; font-size: 0.9rem; color: #64748b;">Use the sidebar to navigate.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ================= PROFILE SECTION =================
def _render_profile_section():
    """Render profile form for the logged-in user to update their information."""
    user = get_user_by_id(st.session_state.user_id)
    if not user:
        st.error("User not found.")
        return

    # user: (id, name, username, mobile, password, role, course, year)
    st.markdown("Update your account information below.")
    st.markdown("---")

    with st.form("profile_form", clear_on_submit=False):
        name = st.text_input("Full Name", value=user[1], key="profile_name")
        username = st.text_input("Username", value=user[2], placeholder="Used for login", key="profile_username")
        mobile = st.text_input("Mobile", value=user[3], placeholder="10-digit mobile number", key="profile_mobile")

        if st.session_state.role == "student":
            course = st.text_input("Course", value=user[6] or "MCA", key="profile_course")
            year = st.selectbox("Year", ["1st", "2nd"], index=["1st", "2nd"].index(user[7]) if user[7] in ("1st", "2nd") else 0, key="profile_year")
        else:
            course = user[6] or "ALL"
            year = user[7] or "N/A"

        st.markdown("**Change Password** (leave blank to keep current)")
        new_password = st.text_input("New Password", type="password", placeholder="At least 6 characters", key="profile_new_pass")
        confirm_password = st.text_input("Confirm New Password", type="password", key="profile_confirm_pass")

        submitted = st.form_submit_button("Save Changes")

    if submitted:
        if not name.strip() or not username.strip() or not mobile.strip():
            st.error("Name, username, and mobile are required.")
        elif len(mobile.strip()) < 10:
            st.error("Please enter a valid 10-digit mobile number.")
        elif new_password and len(new_password) < 6:
            st.error("Password must be at least 6 characters.")
        elif new_password and new_password != confirm_password:
            st.error("Passwords do not match.")
        else:
            if update_user(st.session_state.user_id, name.strip(), username.strip(), mobile.strip(), course, year):
                if new_password:
                    update_password(st.session_state.user_id, new_password)

                cookies["user_id"] = str(st.session_state.user_id)
                cookies["name"] = name.strip()
                cookies["role"] = st.session_state.role
                cookies["course"] = course
                cookies["year"] = year
                cookies.save()

                st.session_state.name = name.strip()
                st.session_state.course = course
                st.session_state.year = year

                st.success("Profile updated successfully.")
                st.rerun()
            else:
                st.error("Username or mobile is already taken by another user.")


# ================= RESTORE LOGIN FROM COOKIE =================
# Skip restore if user just logged out (cookie deletion is unreliable in streamlit-cookies-manager)
just_logged_out = "logout" in st.query_params
if just_logged_out:
    del st.query_params["logout"]

if (
    "role" not in st.session_state
    and not just_logged_out
    and cookies.get("user_id")
):
    st.session_state.user_id = int(cookies["user_id"])
    st.session_state.name = cookies["name"]
    st.session_state.role = cookies["role"]
    st.session_state.course = cookies.get("course", "")
    st.session_state.year = cookies.get("year", "")


# ================= AUTH SCREENS =================
if "role" not in st.session_state:

    col_brand, col_form = st.columns([1, 1])

    with col_brand:
        st.markdown(
            """
            <div class="svu-auth-brand">
                <h2>🎓 SVU-MCA Assistant</h2>
                <p style="margin-top: 1rem;">Intelligent assistant for MCA students of Samrat Vikramaditya University, Ujjain.</p>
                <p style="margin-top: 1.25rem; font-size: 0.9rem;">Ask questions about schedules, notices, exams, and more. Responses are powered by Google Gemini and university documents.</p>
                <ul style="margin: 1.5rem 0 0 0; padding-left: 1.25rem; opacity: 0.95;">
                    <li>Students: register once, log in anytime</li>
                    <li>Admin: manage users, documents & chat history</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_form:
        st.markdown("")
        st.markdown("### Account")

        tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])

        with tab_login:
            st.markdown("")
            login_id = st.text_input(
                "Username / Mobile",
                placeholder="Enter username or mobile number",
                key="login_id",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_pass",
            )
            st.markdown("")
            if st.button("Sign in", type="primary", use_container_width=True, key="btn_login"):
                user = login(login_id, password)
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
                else:
                    st.error("Invalid username or password")

        with tab_register:
            st.markdown("")
            name = st.text_input(
                "Full Name",
                placeholder="Enter your full name",
                key="reg_name",
            )
            username = st.text_input(
                "Username",
                placeholder="Used for login (unique)",
                key="reg_username",
            )
            mobile = st.text_input(
                "Mobile",
                placeholder="10-digit mobile number",
                key="reg_mobile",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="At least 6 characters",
                key="reg_pass",
            )
            course, year = st.columns(2)
            with course:
                course_val = st.text_input("Course", value="MCA", placeholder="MCA", key="reg_course")
            with year:
                year_val = st.selectbox("Year", ["1st", "2nd"], key="reg_year")
            st.markdown("")
            if st.button("Create account", type="primary", use_container_width=True, key="btn_register"):
                if not name.strip() or not username.strip() or not mobile.strip() or not password.strip():
                    st.error("All fields are required.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                elif len(mobile.strip()) < 10:
                    st.error("Please enter a valid 10-digit mobile number.")
                else:
                    if register_user(name, username, mobile, password, course_val, year_val):
                        get_all_users.clear()
                        st.success("Registered successfully. Please log in.")
                    else:
                        st.error("Username or mobile is already registered.")

# ================= DASHBOARD =================
else:
    # ---------- SIDEBAR ----------
    st.sidebar.image("images/Vikram_University_logo.jpg", width=90)
    st.sidebar.markdown(f"### {st.session_state.name}")
    st.sidebar.caption(st.session_state.role.upper())
    st.sidebar.markdown("---")

    # ---------- ADMIN ----------
    if st.session_state.role == "admin":
        # Maintain selected admin menu in session_state
        if "admin_menu" not in st.session_state:
            st.session_state.admin_menu = "Home"

        st.sidebar.markdown(
            '<div class="svu-sidebar-section-title">ADMIN MENU</div>',
            unsafe_allow_html=True,
        )

        admin_menu_items = [
            ("Home", "🏠 Home"),
            ("Profile", "👤 Profile"),
            ("Users", "👥 Users"),
            ("Documents & Notices", "📄 Documents & Notices"),
            ("Logout", "⏏ Logout"),
        ]

        for value, label in admin_menu_items:
            is_active = value == st.session_state.admin_menu
            css_class = "svu-nav-item-active" if is_active else "svu-nav-item"

            with st.sidebar.container():
                st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
                if st.button(label, key=f"admin_menu_{value}"):
                    st.session_state.admin_menu = value
                    if value == "Logout":
                        logout_user()
                st.markdown("</div>", unsafe_allow_html=True)

        menu = st.session_state.admin_menu

        if menu == "Home":
            st.subheader("👋 Welcome Admin")
            st.write("Use the side menu to manage users, documents, and chat history.")

        elif menu == "Profile":
            _render_profile_section()

        elif menu == "Users":
            st.subheader("📋 User Management")

            # Show user chat history when History button is clicked
            if "view_history_user_id" in st.session_state and st.session_state.view_history_user_id:
                uid = st.session_state.view_history_user_id
                uname = st.session_state.get("view_history_user_name", "User")
                if st.button("← Back to users"):
                    del st.session_state["view_history_user_id"]
                    if "view_history_user_name" in st.session_state:
                        del st.session_state["view_history_user_name"]
                    st.rerun()
                st.markdown(f"### 💬 Chat history: {uname}")
                st.markdown("---")
                conn = sqlite3.connect("college_data.db")
                cur = conn.cursor()
                cur.execute(
                    "SELECT role, message, timestamp FROM chat_history WHERE user_id=? ORDER BY id ASC",
                    (uid,),
                )
                rows = cur.fetchall()
                conn.close()
                if not rows:
                    st.info("No chat history for this user.")
                else:
                    for role, message, ts in rows:
                        label = "User" if role == "user" else "Assistant"
                        st.markdown(f"**{label}** — {ts or ''}")
                        st.write(message)
                        st.markdown("---")
            else:
                st.markdown("**Name | Username | Mobile | Role | Course | Year | Actions**")
                st.markdown("---")
                for u in get_all_users():
                    cols = st.columns([3, 2, 2, 2, 2, 2, 1, 1])
                    cols[0].write(u[1])
                    cols[1].write(u[2])
                    cols[2].write(u[3])
                    cols[3].write(u[5])
                    cols[4].write(u[6])
                    cols[5].write(u[7])
                    if cols[6].button("📜 History", key=f"hist_{u[0]}"):
                        st.session_state.view_history_user_id = u[0]
                        st.session_state.view_history_user_name = u[1]
                        st.rerun()
                    if cols[7].button("❌ Delete", key=f"del_{u[0]}"):
                        delete_user(u[0])
                        st.rerun()

        elif menu == "Documents & Notices":
            st.subheader("📄 Documents / Notices")
            title = st.text_input("Title")
            desc = st.text_area("Description")

            if st.button("Add"):
                if title.strip() and desc.strip():
                    add_document(title, desc)
                    st.success("Added")
                    st.rerun()
                else:
                    st.error("Title and description are required.")

            st.markdown("---")
            st.markdown("**Documents**")
            for d in get_all_documents():
                c1, c2 = st.columns([6, 1])
                with c1:
                    st.markdown(f"**{d[1]}**")
                    st.write(d[2])
                with c2:
                    if st.button("🗑️ Remove", key=f"del_doc_{d[0]}"):
                        delete_document(d[0])
                        st.rerun()
                st.markdown("---")

            st.markdown("**Notices**")
            for n in get_all_notifications():
                c1, c2 = st.columns([6, 1])
                with c1:
                    st.markdown(f"**{n[1]}**")
                    st.write(n[2])
                with c2:
                    if st.button("🗑️ Remove", key=f"del_notif_{n[0]}"):
                        delete_notification(n[0])
                        st.rerun()
                st.markdown("---")

        elif menu == "Logout":
            logout_user()

    # ---------- STUDENT ----------
    else:
        if "student_view" not in st.session_state:
            st.session_state.student_view = "Home"

        st.sidebar.markdown("### Session")
        if st.sidebar.button("🏠 Home", use_container_width=True, key="student_home_btn"):
            st.session_state.student_view = "Home"
            st.rerun()
        if st.sidebar.button("💬 Chat", use_container_width=True, key="student_chat_btn"):
            st.session_state.student_view = "Chat"
            st.rerun()
        if st.sidebar.button("📜 Chat History", use_container_width=True, key="student_chat_history_btn"):
            st.session_state.student_view = "Chat History"
            st.rerun()
        if st.sidebar.button("👤 Profile", use_container_width=True, key="student_profile_btn"):
            st.session_state.student_view = "Profile"
            st.rerun()
        st.sidebar.markdown("---")
        st.sidebar.button("Logout", on_click=logout_user)

        if st.session_state.student_view == "Home":
            _render_student_home()
        elif st.session_state.student_view == "Profile":
            st.markdown("### 👤 Profile")
            _render_profile_section()
        elif st.session_state.student_view == "Chat History":
            st.subheader("📜 Chat History")
            conn = sqlite3.connect("college_data.db")
            cur = conn.cursor()
            cur.execute(
                """
                SELECT role, message, timestamp
                FROM chat_history
                WHERE user_id = ?
                ORDER BY id ASC
                """,
                (st.session_state.user_id,),
            )
            rows = cur.fetchall()
            conn.close()
            if not rows:
                st.info("No chat history yet. Start a conversation in **Chat**.")
            else:
                for role, message, ts in rows:
                    label = "You" if role == "user" else "Assistant"
                    st.markdown(f"**{label}** — {ts or ''}")
                    st.write(message)
                    st.markdown("---")
        elif st.session_state.student_view == "Chat":
            st.markdown("### 👋 Welcome back")
            st.markdown(
                f"**{st.session_state.name}**, ask any MCA or university-related question below."
            )
            st.markdown("---")

            # Load and display previous chat from DB for context
            history = load_chat_history(st.session_state.user_id)
            recent_chat = "\n".join(
                f"{'User' if r == 'user' else 'Assistant'}: {m}" for r, m in history[-6:]
            )
            for role, message in history:
                with st.chat_message("assistant" if role == "assistant" else "user"):
                    st.write(message)

            q = st.chat_input("Ask your question...")

            if q:
                with st.chat_message("user"):
                    st.write(q)

                ans = ask_ai(q, recent_context=recent_chat)

                with st.chat_message("assistant"):
                    st.write(ans)

                # Always save chat for logged-in users
                save_chat(st.session_state.user_id, "user", q)
                save_chat(st.session_state.user_id, "assistant", ans)
