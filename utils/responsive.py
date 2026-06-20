"""
utils/responsive.py
-------------------
Shared responsive CSS injected on every page.
"""

import streamlit as st


RESPONSIVE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ─────────────────────────────────────────────
   GLOBAL FONT
───────────────────────────────────────────── */
html, body, p, div, span, h1, h2, h3, h4, h5, h6,
a, input, textarea, button, select {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont,
    'Segoe UI', sans-serif !important;
}

/* ─────────────────────────────────────────────
   MATERIAL ICON FIX
───────────────────────────────────────────── */
[data-testid="stIconMaterial"],
.material-icons,
[class*="material-icons"],
[class^="material-icons"] {
    font-family: 'Material Symbols Outlined', 'Material Icons' !important;
    font-style: normal !important;
    font-weight: normal !important;
    line-height: 1 !important;
    white-space: nowrap !important;
    direction: ltr !important;
}

[data-testid="stIconMaterial"] {
    max-width: 28px !important;
    overflow: hidden !important;
}

/* ─────────────────────────────────────────────
   SIDEBAR CLEANUP
───────────────────────────────────────────── */
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"],
[data-testid="stSidebarNavSeparator"] {
    display: none !important;
}

/* ─────────────────────────────────────────────
   BASE LAYOUT
───────────────────────────────────────────── */
.main .block-container {
    max-width: 100% !important;
    padding: 1.5rem 2rem !important;
    box-sizing: border-box !important;
}

/* ─────────────────────────────────────────────
   TOUCH FRIENDLY INPUTS
───────────────────────────────────────────── */
input, textarea, select {
    font-size: 16px !important;
}

/* ─────────────────────────────────────────────
   BUTTONS
───────────────────────────────────────────── */
.main .stButton > button {
    min-height: 44px;
    border-radius: 8px;
}

/* ─────────────────────────────────────────────
   CHAT WIDTH SYSTEM — единый источник истины
───────────────────────────────────────────── */
[data-testid="stChatInputContainer"],
[data-testid="stChatInput"],
[data-testid="stChatMessage"],
[data-testid="stExpander"],
[data-testid="stVerticalBlockBorderWrapper"] {
    max-width: 820px !important;
    width: 820px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    box-sizing: border-box !important;
}

/* Sources строка (класс добавлен в chat.py) */
.chat-sources {
    max-width: 820px !important;
    width: 820px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    box-sizing: border-box !important;
}

/* ─────────────────────────────────────────────
   CHAT INPUT STYLING
───────────────────────────────────────────── */
[data-testid="stChatInput"],
[data-testid="stChatInputContainer"] {
    border-radius: 26px !important;
    background-color: #f0f2f6 !important;
    border: 1px solid #d9dde6 !important;
    overflow: hidden !important;
    box-shadow: none !important;
}

/* убрать розовый/фиолетовый focus на инпуте */
[data-testid="stChatInput"]:focus-within,
[data-testid="stChatInputContainer"]:focus-within,
[data-testid="stChatInput"] textarea:focus,
[data-testid="stChatInputContainer"] textarea:focus {
    border-color: #d9dde6 !important;
    box-shadow: none !important;
    outline: none !important;
}

/* textarea styling */
[data-testid="stChatInput"] textarea,
[data-testid="stChatInputContainer"] textarea {
    background-color: #f0f2f6 !important;
    color: #1a1a2e !important;
    caret-color: #1a1a2e !important;
    font-size: 0.975rem !important;
    line-height: 1.6 !important;
    border-radius: 26px !important;
    box-shadow: none !important;
    outline: none !important;
}

/* placeholder */
[data-testid="stChatInput"] textarea::placeholder {
    color: #8a93a6 !important;
}

/* ─────────────────────────────────────────────
   EXPANDER — убрать розовый бордер везде
───────────────────────────────────────────── */
[data-testid="stExpander"] details,
[data-testid="stExpander"] details:focus,
[data-testid="stExpander"] details:focus-within,
[data-testid="stExpander"] details:hover {
    border: 1px solid #d9dde6 !important;
    box-shadow: none !important;
    outline: none !important;
}

[data-testid="stExpander"] summary:focus,
[data-testid="stExpander"] summary:focus-visible {
    box-shadow: none !important;
    outline: none !important;
}

/* ─────────────────────────────────────────────
   CHAT MESSAGES (ChatGPT style bubbles)
───────────────────────────────────────────── */

[data-testid="stChatMessage"] {
    padding: 0.5rem 0.75rem !important;
    border-radius: 18px !important;
    margin-bottom: 0.35rem !important;
    word-break: break-word !important;
}

/* USER MESSAGE */
[data-testid="stChatMessage"][data-message-author-role="user"],
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background-color: #1f3a8a !important;
    color: #ffffff !important;

    border: none !important;
    margin-left: 3rem !important;

    width: calc(820px - 3rem) !important;
    max-width: calc(820px - 3rem) !important;

    border-radius: 18px !important;
}

/* текст внутри user */
[data-testid="stChatMessage"][data-message-author-role="user"] p,
[data-testid="stChatMessage"][data-message-author-role="user"] span {
    color: #ffffff !important;
}

/* ASSISTANT MESSAGE */
[data-testid="stChatMessage"][data-message-author-role="assistant"],
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background-color: #f3f4f6 !important;
    color: #111827 !important;

    border: 1px solid #e5e7eb !important;

    border-radius: 18px !important;

    width: 820px !important;
    max-width: 820px !important;

    margin-left: auto !important;
    margin-right: auto !important;
}

/* текст ассистента */
[data-testid="stChatMessage"][data-message-author-role="assistant"] p,
[data-testid="stChatMessage"][data-message-author-role="assistant"] span {
    color: #111827 !important;
}

/* аватарки оставить */
[data-testid="chatAvatarIcon-user"],
[data-testid="chatAvatarIcon-assistant"] {
    display: block !important;
    width: 28px !important;
    height: 28px !important;
    border-radius: 50% !important;
}

/* ─────────────────────────────────────────────
   TEXT STYLING
───────────────────────────────────────────── */
[data-testid="stChatMessage"] p {
    font-size: 0.965rem !important;
    line-height: 1.65 !important;
}

[data-testid="stChatMessage"] code {
    font-size: 0.875rem !important;
}
[data-testid="stChatMessage"] pre {
    font-size: 0.87rem !important;
    border-radius: 10px !important;
    line-height: 1.55 !important;
}

/* ─────────────────────────────────────────────
   WELCOME SCREEN
───────────────────────────────────────────── */
.aitu-welcome {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 58vh;
    text-align: center;
    gap: 0.75rem;
}

.aitu-welcome h1 {
    font-size: 2.15rem !important;
    font-weight: 650 !important;
    letter-spacing: -0.02em;
}

.aitu-welcome p {
    opacity: 0.55;
    font-size: 1.05rem !important;
}

/* ─────────────────────────────────────────────
   MOBILE RESPONSIVE
───────────────────────────────────────────── */
@media (max-width: 640px) {

    .main .block-container {
        padding: 0.75rem 0.6rem !important;
    }

    [data-testid="stChatMessage"],
    [data-testid="stChatInputContainer"],
    [data-testid="stChatInput"],
    [data-testid="stExpander"],
    [data-testid="stVerticalBlockBorderWrapper"] {
        width: 100% !important;
        max-width: 100% !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
    }

    .chat-sources {
        width: 100% !important;
        max-width: 100% !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
    }

    h1 { font-size: 1.6rem !important; }
    h2 { font-size: 1.3rem !important; }
    h3 { font-size: 1.1rem !important; }
}

</style>
"""


def inject_responsive_css() -> None:
    """Inject all global + chat + responsive styles."""
    st.markdown(RESPONSIVE_CSS, unsafe_allow_html=True)
