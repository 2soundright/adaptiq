"""
utils/sidebar.py
----------------
Shared sidebar navigation — AITU dark style.
Always-visible sidebar: no toggle button.
  - Admin: Chat, Documents, Analytics, Scraper, Logs, Log out
  - Regular user: Chat, Log out
"""

import streamlit as st
from typing import Dict

# \u00A0 = non-breaking space
_SECTIONS = [
    ("documents", "📄︎\u00a0\u00a0\u00a0Documents"),
    ("analytics", "📊︎\u00a0\u00a0\u00a0Analytics"),
    ("scraper", "🔍︎\u00a0\u00a0\u00a0Scraper"),
    ("logs", "📋︎\u00a0\u00a0\u00a0Logs"),
]

# Sidebar always open — hide the toggle button entirely.
_SIDEBAR_CSS = """
<style>

/* ── HIDE Material Icon text fallbacks site-wide ───────────── */
/* Prevents "arrow_right", "keyboard_double", "info" fragments  */
[data-testid="stIconMaterial"] {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
    position: absolute !important;
    font-size: 0 !important;
    line-height: 0 !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* ── Always show sidebar, hide toggle button completely ────── */
[data-testid="stSidebar"],
section[data-testid="stSidebar"] {
    display: flex !important;
    visibility: visible !important;
    width: 360px !important;
    min-width: 360px !important;
    max-width: 360px !important;
    overflow: unset !important;
    transform: none !important;
}

/* Hide the open/close toggle button entirely */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
button[data-testid="baseButton-headerNoPadding"],
button[kind="header"] {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
    position: absolute !important;
}

[data-testid="stSidebar"] {
    background: #0f1b2d !important;
    border-right: none !important;
}
[data-testid="stSidebar"] > div:first-child {
    height: 100vh !important;
    overflow: hidden !important;
    padding-top: 0 !important;
    margin-top: 0 !important;
    background: #0f1b2d !important;
}
[data-testid="stSidebar"] > div:first-child > div:first-child {
    padding-top: 0 !important;
    margin-top: 0 !important;
    padding-bottom: 1rem !important;
}
section[data-testid="stSidebar"] > div {
    padding-top: 0 !important;
}
[data-testid="stSidebar"] .stMarkdown p {
    font-size: 0.8rem !important;
    color: #a0b4c8 !important;
    margin: 0 !important;
    padding: 0 !important;
    padding-left: 1.4rem !important;
}
[data-testid="stSidebar"] .stMarkdown strong {
    font-size: 18px !important;
    font-weight: 500 !important;
    color: #e8f0f8 !important;
}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    font-size: 18px !important;
    font-weight: 500 !important;
    color: #97b4c8 !important;
    padding: 0 !important;
    padding-left: 1.4rem !important;
    margin: 0 !important;
}
[data-testid="stSidebar"] hr {
    margin: 0.15rem 0 !important;
    border-color: rgba(255,255,255,0.07) !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a {
    display: flex !important;
    align-items: center !important;
    padding: 0.55rem 1rem !important;
    font-size: 0.875rem !important;
    color: #a0b4c8 !important;
    text-decoration: none !important;
    border-radius: 0 !important;
    margin: 0 !important;
    line-height: 1.4 !important;
    background: transparent !important;
    border-left: 3px solid transparent !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
    background: rgba(255,255,255,0.07) !important;
    color: #ffffff !important;
}
[data-testid="stSidebar"] .stButton {
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
    text-align: left !important;
}
[data-testid="stSidebar"] .stButton > button {
    text-align: left !important;
    justify-content: flex-start !important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"],
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
    all: unset !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    gap: 0 !important;
    width: 100% !important;
    box-sizing: border-box !important;
    padding: 0.3rem 1rem 0.3rem 1.5rem !important;
    font-size: 16px !important;
    font-weight: 400 !important;
    font-family: 'Inter', sans-serif !important;
    color: #ffffff !important;
    cursor: pointer !important;
    line-height: 1.4 !important;
    background: transparent !important;
    border-left: 3px solid transparent !important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] p,
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] p,
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] span,
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] span,
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] *,
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] * {
    font-size: 16px !important;
    font-weight: 400 !important;
    font-family: 'Inter', sans-serif !important;
    color: #ffffff !important;
    text-align: left !important;
    justify-content: flex-start !important;
    margin-left: 0 !important;
    margin-right: auto !important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
    background: rgba(255,255,255,0.07) !important;
    color: #ffffff !important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
    background: #1a6faf !important;
    color: #ffffff !important;
    border-left: 3px solid #4db8ff !important;
}
[data-testid="stSidebar"] .ed4y4ls0 {
    color: #ffffff !important;
}
[data-testid="stSidebar"] .exttvjz3,
[data-testid="stSidebar"] .st-emotion-cache-23r7bk {
    background-color: #0f1b2d !important;
    border-radius: 20px !important;
}

.sidebar-logout-gap {
    margin-top: 14rem !important;
    display: block !important;
}
</style>
"""

# Completely hide sidebar + toggle on the login page
_HIDE_ALL_SIDEBAR_CSS = """
<style>
[data-testid="stSidebar"],
section[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
[data-testid="stSidebarContent"],
button[data-testid="baseButton-headerNoPadding"],
button[kind="header"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
    position: absolute !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
}
</style>
"""


def _get_logo_html() -> str:
    return ""


def inject_hide_sidebar_css() -> None:
    """Inject CSS that fully hides sidebar and toggle — use on the login page."""
    st.markdown(_HIDE_ALL_SIDEBAR_CSS, unsafe_allow_html=True)


def render_admin_sidebar(user: Dict, on_admin_page: bool = False) -> None:
    """Sidebar for admin users: Chat, Documents, Analytics, Scraper, Logs, Log out."""
    with st.sidebar:
        st.markdown(_SIDEBAR_CSS, unsafe_allow_html=True)
        st.markdown(_get_logo_html(), unsafe_allow_html=True)

        st.markdown(f"**{user['email']}**")
        st.caption("Admin")
        st.divider()

        if st.button(
            "💬︎\u00a0\u00a0\u00a0Chat",
            key="sidebar_chat",
            use_container_width=True,
            type="secondary",
        ):
            st.switch_page("pages/chat.py")
        st.divider()

        current = st.session_state.get("admin_section", "documents")
        for key, label in _SECTIONS:
            is_active = on_admin_page and (current == key)
            if st.button(
                label,
                key=f"sidebar_{key}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.admin_section = key
                if on_admin_page:
                    st.rerun()
                else:
                    st.switch_page("pages/admin.py")

        st.markdown('<div class="sidebar-logout-gap"></div>', unsafe_allow_html=True)
        st.divider()
        if st.button(
            "↪︎\u00a0\u00a0\u00a0Log out", key="sidebar_logout", use_container_width=True
        ):
            st.session_state.user = None
            st.session_state.messages = []
            st.switch_page("app.py")


def render_user_sidebar(user: Dict) -> None:
    """Sidebar for regular users: Chat, Log out."""
    with st.sidebar:
        st.markdown(_SIDEBAR_CSS, unsafe_allow_html=True)
        st.markdown(_get_logo_html(), unsafe_allow_html=True)

        st.markdown(f"**{user['email']}**")
        st.caption("User")
        st.divider()

        if st.button(
            "💬︎\u00a0\u00a0\u00a0Chat",
            key="sidebar_chat_user",
            use_container_width=True,
            type="secondary",
        ):
            st.switch_page("pages/chat.py")

        st.markdown('<div class="sidebar-logout-gap"></div>', unsafe_allow_html=True)
        st.divider()
        if st.button(
            "↪︎\u00a0\u00a0\u00a0Log out",
            key="sidebar_logout_user",
            use_container_width=True,
        ):
            st.session_state.user = None
            st.session_state.messages = []
            st.switch_page("app.py")
