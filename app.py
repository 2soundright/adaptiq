"""
app.py
------
Entry point for the AI Assistant Streamlit app.
Handles:
  - DB initialisation
  - Authentication gate (login / register)
  - Session state management
  - Navigation to Chat and Admin pages
"""

import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from utils.db_init import init_db
from utils.auth import login, register
from utils.responsive import inject_responsive_css
from utils.sidebar import inject_hide_sidebar_css
from utils.pendo import track_event_server as pendo_track

# ── page config (must be the first Streamlit call) ────────────────────────────
st.set_page_config(
    page_title="AdaptIQ",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_responsive_css()


# ── DB bootstrap ──────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Initialising database …")
def _init() -> bool:
    """Run once per process – initialise SQLite and seed defaults."""
    try:
        os.makedirs("./data", exist_ok=True)
        init_db()
        return True
    except Exception as exc:
        st.error(f"Database initialisation failed: {exc}")
        return False


_db_ready = _init()

# ── session defaults ──────────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None
if "company_id" not in st.session_state:
    st.session_state.company_id = int(os.getenv("DEFAULT_COMPANY_ID", "1"))
if "messages" not in st.session_state:
    st.session_state.messages = []
if "reg_error" not in st.session_state:
    st.session_state.reg_error = ""


# ── top navigation bar ────────────────────────────────────────────────────────


def render_topbar() -> None:
    """Renders a top navigation bar with user info and logout."""
    user = st.session_state.user
    if not user:
        return

    col_nav, col_user = st.columns([5, 2])

    with col_nav:
        nav_cols = st.columns([1, 1, 5])
        with nav_cols[0]:
            st.page_link("pages/chat.py", label="💬 Chat")
        if user["role"] == "admin":
            with nav_cols[1]:
                st.page_link("pages/admin.py", label="⚙️ Admin")

    with col_user:
        info_col, logout_col = st.columns([6, 1])
        with info_col:
            st.markdown(
                f"<div style='text-align:right;padding-top:6px'>"
                f"<small style='color:#888'>{user['email']} · <code>{user['role']}</code></small>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with logout_col:
            if st.button("🚪", help="Log out"):
                st.session_state.user = None
                st.session_state.messages = []
                st.rerun()

    st.divider()


# ── login / register form ─────────────────────────────────────────────────────


def _auth_form() -> None:
    # Hide sidebar and toggle button completely on the login page
    inject_hide_sidebar_css()
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 5vh !important;
            padding-bottom: 2rem !important;
        }
        /* Style switch buttons as link-like text */
        [data-testid="stBaseButton-secondary"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #2aade1 !important;
            font-weight: 500 !important;
            text-decoration: underline !important;
        }
        [data-testid="stBaseButton-secondary"]:hover {
            color: #1a8dbf !important;
            background: transparent !important;
            border: none !important;
        }
        /* Rounded form container */
        [data-testid="stForm"] {
            border-radius: 5px !important;
            text-align: left;
        }
        /* Input field backgrounds */
        [data-testid="stTextInput"] input,
        [data-baseweb="input"] {
            background-color: #f0f2f6 !important;
        }
        /* Input container background */
        [data-baseweb="base-input"] {
            background-color: #f0f2f6 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    _, center, _ = st.columns([1.5, 1, 1.5])
    with center:
        st.markdown(
            "<p style='text-align:center; font-size:40px; font-weight:600; margin:0;'>AdaptIQ</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center; font-weight:300;'>Welcome! Please log in or create an account.</p>",
            unsafe_allow_html=True,
        )

        company_id = st.session_state.company_id

        if "auth_mode" not in st.session_state:
            st.session_state.auth_mode = "login"

        if st.session_state.auth_mode == "login":
            submitted = False
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Log in", use_container_width=True)

            if submitted:
                if not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    ok, user, msg = login(email, password, company_id)
                    if ok and user:
                        st.session_state.user = user
                        pendo_track(
                            "user_logged_in",
                            visitor_id=user["id"],
                            account_id=company_id,
                            properties={
                                "role": user.get("role", "unknown"),
                                "company_id": company_id,
                                "user_id": user["id"],
                            },
                        )
                        st.switch_page("pages/chat.py")
                    else:
                        st.error(msg)

            _t, _b = st.columns([1.4, 0.9])
            with _t:
                st.markdown(
                    "<p style='text-align:right; color:#888; margin:0; padding-top:8px; font-weight:300;'>Don't have an account?</p>",
                    unsafe_allow_html=True,
                )
            with _b:
                if st.button("Register", key="switch_to_register", type="secondary"):
                    st.session_state.auth_mode = "register"
                    st.rerun()

        else:
            if "reg_error" in st.session_state and st.session_state.reg_error:
                st.error(st.session_state.reg_error)
                st.session_state.reg_error = ""

            with st.form("register_form"):
                reg_email = st.text_input(
                    "Email", placeholder="you@example.com", key="reg_email"
                )
                reg_password = st.text_input(
                    "Password", type="password", key="reg_pass"
                )
                reg_role = st.selectbox("Role", ["user", "worker"], key="reg_role")
                reg_submit = st.form_submit_button(
                    "Create account", use_container_width=True
                )

            if reg_submit:
                if not reg_email or not reg_password:
                    st.session_state.reg_error = "Please fill in all fields."
                    st.rerun()
                else:
                    ok, msg = register(reg_email, reg_password, company_id, reg_role)
                    if ok:
                        _, user, _ = login(reg_email, reg_password, company_id)
                        if user:
                            st.session_state.user = user
                            pendo_track(
                                "user_registered",
                                visitor_id=user["id"],
                                account_id=company_id,
                                properties={
                                    "role": reg_role,
                                    "company_id": company_id,
                                    "user_id": user["id"],
                                },
                            )
                            st.switch_page("pages/chat.py")
                        else:
                            st.session_state.reg_error = msg + " You can now log in."
                            st.rerun()
                    else:
                        st.session_state.reg_error = msg
                        st.rerun()

            _t2, _b2 = st.columns([1.5, 0.6])
            with _t2:
                st.markdown(
                    "<p style='text-align:right; color:#888; margin:0; padding-top:8px; font-weight:300;'>Already have an account?</p>",
                    unsafe_allow_html=True,
                )
            with _b2:
                if st.button("Log in", key="switch_to_login", type="secondary"):
                    st.session_state.auth_mode = "login"
                    st.rerun()


# ── main ──────────────────────────────────────────────────────────────────────

if not _db_ready:
    st.error("Database failed to initialise. Check your environment and restart.")
    st.stop()

if st.session_state.user is None:
    from utils.pendo import inject_pendo
    inject_pendo()
    _auth_form()
else:
    st.switch_page("pages/chat.py")
