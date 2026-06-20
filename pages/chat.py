"""
pages/chat.py
-------------
Chat UI for the AI Assistant.
Pipeline order: safety → lang_detect → query_transform → embed →
                retrieve → rerank → generate (stream) → feedback
"""

import json
import os
import time
import uuid
from typing import Dict, Generator, List, Optional

import streamlit as st

st.set_page_config(
    page_title="AdaptIQ",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)


from utils.responsive import inject_responsive_css

inject_responsive_css()

from utils.db_init import get_connection, get_company, init_db
from utils.pendo import inject_pendo, track_event_server as pendo_track
from utils.db_lock import db_lock
from pipeline.safety import check_safety
from pipeline.lang_detect import detect_language
from pipeline.query_transform import transform_query
from pipeline.embeddings import embed_single
from pipeline.retriever import retrieve
from pipeline.reranker import rerank
from pipeline.generator import generate
from pipeline.feedback import save_feedback
from continual_learning.replay_buffer import add_entry
from utils.pendo import track_event

_PENDO_AGENT_ID = "iefyxIiGJ9ZNP5E3oLQ5ouGeBTw"
_PENDO_MODEL = os.getenv("GROQ_GENERATION_MODEL", "openai/gpt-oss-120b")


def _track_agent(event_type: str, metadata: dict) -> None:
    """Inject a pendo.trackAgent() call via JavaScript."""
    metadata_json = json.dumps(metadata)
    st.html(
        f"""<script>
        if (window.pendo && typeof window.pendo.trackAgent === 'function') {{
            window.pendo.trackAgent("{event_type}", {metadata_json});
        }}
        </script>"""
    )


# ── auth guard ────────────────────────────────────────────────────────────────


def _require_auth() -> bool:
    """Redirect to home if not logged in. Return True if authenticated."""
    if "user" not in st.session_state or not st.session_state.user:
        st.warning("Please log in first.")
        st.page_link("app.py", label="← Go to login")
        return False
    return True


# ── helpers ───────────────────────────────────────────────────────────────────


def _save_conversation(
    user_id: int,
    company_id: int,
    query: str,
    response: str,
    lang: str,
    sources: List[Dict],
) -> Optional[int]:
    """Persist a conversation record and return its ID."""
    try:
        with db_lock():
            conn = get_connection()
            cur = conn.execute(
                """INSERT INTO conversations
                   (user_id, company_id, query, response, lang, sources_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    user_id,
                    company_id,
                    query,
                    response,
                    lang,
                    json.dumps(sources, ensure_ascii=False),
                ),
            )
            conv_id = cur.lastrowid
            conn.commit()
            conn.close()
        return conv_id
    except Exception as exc:
        print(f"[chat] _save_conversation failed: {exc}")
        st.error(f"Could not save conversation: {exc}")
        return None


def _already_rated(conv_id: int) -> bool:
    """Return True if the user already submitted feedback for this conversation."""
    rated: set = st.session_state.get("rated_conversations", set())
    return conv_id in rated


def _mark_rated(conv_id: int) -> None:
    if "rated_conversations" not in st.session_state:
        st.session_state.rated_conversations = set()
    st.session_state.rated_conversations.add(conv_id)


def _render_sources(sources: List[Dict]) -> None:
    """Render source links visibly below the response."""
    if not sources:
        return

    # Deduplicate by URL/file so we don't show the same page multiple times
    seen: set = set()
    unique: List[Dict] = []
    for src in sources:
        meta = src.get("metadata", {})
        key = meta.get("website_url", "") or meta.get("source_file", "")
        if key and key not in seen:
            seen.add(key)
            unique.append(src)

    if not unique:
        return

    # Build compact inline link list
    parts = []
    for i, src in enumerate(unique, 1):
        meta = src.get("metadata", {})
        url = meta.get("website_url", "")
        file_ = meta.get("source_file", "")
        title = meta.get("title", "") or url or file_ or f"Source {i}"
        short_title = (title[:60] + "…") if len(title) > 60 else title
        if url:
            parts.append(f"[{i}. {short_title}]({url})")
        elif file_:
            parts.append(f"{i}. 📄 `{file_}`")

    if parts:
        st.markdown(
            "<div class='chat-sources' style='margin-top:6px; font-size:0.82em; color:#555;'>"
            "📎 <b>Sources:</b> " + " &nbsp;·&nbsp; ".join(parts) + "</div>",
            unsafe_allow_html=True,
        )

    # Detailed excerpts in a collapsible block
    with st.expander("Show excerpts", expanded=False):
        for i, src in enumerate(unique, 1):
            meta = src.get("metadata", {})
            url = meta.get("website_url", "")
            file_ = meta.get("source_file", "")
            title = meta.get("title", url or file_ or f"Source {i}")
            text = src.get("text", "")
            excerpt = text[:280].replace("\n", " ") + ("…" if len(text) > 280 else "")
            link_html = (
                f'<a href="{url}" target="_blank" style="font-size:0.82em;">🔗 Open page</a>'
                if url
                else (
                    f'<span style="font-size:0.82em;">📄 <code>{file_}</code></span>'
                    if file_
                    else ""
                )
            )
            excerpt_html = (
                f'<blockquote style="margin:2px 0 4px 0; padding:4px 8px; border-left:3px solid #ccc; color:#555; font-size:0.85em;">{excerpt}</blockquote>'
                if excerpt
                else ""
            )
            sep = (
                '<hr style="margin:6px 0; border:none; border-top:1px solid #e0e0e0;" />'
                if i < len(unique)
                else ""
            )
            st.markdown(
                f'<div style="margin:0; padding:2px 0;">'
                f'<strong style="font-size:0.9em;">{i}. {title}</strong>'
                f"{excerpt_html}"
                f"{link_html}"
                f"</div>{sep}",
                unsafe_allow_html=True,
            )


def _render_feedback_buttons(
    conv_id: int, user_id: int, chunk_ids: List[str], company_id: int, role: str,
    pendo_msg_id: Optional[str] = None,
) -> None:
    """Render star rating + comment feedback form once per message."""
    if _already_rated(conv_id):
        st.caption("✅ Feedback recorded")
        return

    stars_key = f"stars_{conv_id}"
    comment_key = f"comment_{conv_id}"

    print(f"[feedback] rendering form for conv_id={conv_id}")
    with st.expander("⭐ Rate this response"):
        stars = st.radio(
            "Your rating:",
            options=[1, 2, 3, 4, 5],
            index=2,
            format_func=lambda x: "⭐" * x,
            horizontal=True,
            key=stars_key,
        )
        comment = st.text_input(
            "Comment (optional)",
            placeholder="Share your thoughts…",
            key=comment_key,
        )
        if st.button("Submit feedback", key=f"submit_{conv_id}"):
            print(f"[feedback] submitted conv_id={conv_id} stars={stars} comment={comment!r}")
            score = 1 if stars >= 3 else -1
            ok = save_feedback(
                conv_id,
                user_id,
                score,
                chunk_ids,
                company_id,
                role,
                star_rating=stars,
                comment=comment or None,
            )
            if ok:
                track_event("feedback_submitted", {
                    "star_rating": stars,
                    "score": score,
                    "has_comment": bool(comment),
                    "conversation_id": conv_id,
                    "chunk_count": len(chunk_ids),
                    "role": role,
                    "company_id": company_id,
                })
                _mark_rated(conv_id)
                st.rerun()


# ── main pipeline call ────────────────────────────────────────────────────────


def _run_pipeline(
    raw_query: str,
    user: Dict,
    company_id: int,
    role: str,
) -> None:
    """Execute the full 8-step pipeline and render the response."""

    # 1. Safety
    is_safe, safety_msg = check_safety(
        raw_query,
        lang="en",
        company_id=company_id,
        user_id=user["id"],
    )
    if not is_safe:
        with st.chat_message("assistant"):
            st.markdown(safety_msg)
        st.session_state.messages.append({"role": "assistant", "content": safety_msg})
        return

    # 2. Language detection
    lang = detect_language(raw_query)

    # 3. Query transform
    transformed = transform_query(raw_query)

    # 4. Embed
    query_embedding = embed_single(transformed)

    # 5. Retrieve
    chunks = retrieve(query_embedding, company_id, role, top_k=10)

    # 6. Rerank → top-3
    top_chunks = rerank(transformed, chunks, top_n=3)

    # 7. Generate (stream)
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[-6:]
    ]

    full_response = ""
    with st.chat_message("assistant"):

        def _stream() -> Generator:
            nonlocal full_response
            for token in generate(transformed, top_chunks, lang, history):
                full_response += token
                yield token

        st.write_stream(_stream())

    # Show sources below the response (rendered outside chat_message block for unified width layout)
    _render_sources(top_chunks)

    # Track agent response
    response_msg_id = str(uuid.uuid4())
    _track_agent("agent_response", {
        "agentId": _PENDO_AGENT_ID,
        "conversationId": st.session_state.get("pendo_conversation_id", ""),
        "messageId": response_msg_id,
        "content": full_response,
        "modelUsed": _PENDO_MODEL,
    })

    # Persist conversation
    conv_id = _save_conversation(
        user_id=user["id"],
        company_id=company_id,
        query=raw_query,
        response=full_response,
        lang=lang,
        sources=top_chunks,
    )
    print(f"[chat] conv_id after save: {conv_id}")

    chunk_ids = [c["id"] for c in top_chunks]

    pendo_track(
        "chat_query_completed",
        visitor_id=user["id"],
        account_id=company_id,
        properties={
            "language": lang,
            "sources_count": len(top_chunks),
            "chunks_retrieved": len(chunks),
            "has_context_docs": bool(top_chunks),
            "company_id": company_id,
            "user_role": role,
            "response_length": len(full_response),
            "query_length": len(raw_query),
        },
    )
    # ── Pendo: track agent response ──────────────────────────────────────────
    _track_agent("agent_response", {
        "agentId": _PENDO_AGENT_ID,
        "conversationId": st.session_state.pendo_conversation_id,
        "messageId": f"agent_response_{conv_id or int(time.time() * 1000)}",
        "content": full_response,
        "modelUsed": os.getenv("GROQ_GENERATION_MODEL", "openai/gpt-oss-120b"),
    })

    # 8. Feedback buttons (rendered outside chat_message block for unified width layout)
    if conv_id:
        _render_feedback_buttons(conv_id, user["id"], chunk_ids, company_id, role, response_msg_id)

    # Add to replay buffer (background learning)
    try:
        quality = 0.7 if top_chunks else 0.2
        add_entry(company_id, raw_query, full_response, query_embedding, quality)
    except Exception as exc:
        print(f"[chat] Replay buffer write failed: {exc}")

    # Append assistant message to session history
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": full_response,
            "sources": top_chunks,
            "conv_id": conv_id,
            "chunk_ids": chunk_ids,
            "pendo_msg_id": response_msg_id,
        }
    )

    # ── Pendo: track completed chat query ────────────────────────────────
    track_event("chat_query_completed", {
        "query_length": len(raw_query),
        "language": lang,
        "num_sources": len(top_chunks),
        "has_sources": bool(top_chunks),
        "response_length": len(full_response),
        "conversation_id": conv_id,
        "role": role,
        "company_id": company_id,
    })


# ── page render ───────────────────────────────────────────────────────────────


def render() -> None:
    if not _require_auth():
        return

    user: Dict = st.session_state.user
    company_id: int = st.session_state.get("company_id", 1)
    role: str = user.get("role", "user")

    company_row = get_company(company_id)
    company = dict(company_row) if company_row else None
    inject_pendo(user=user, company=company)

    if role == "admin":
        from utils.sidebar import render_admin_sidebar

        render_admin_sidebar(user, on_admin_page=False)
    else:
        from utils.sidebar import render_user_sidebar

        render_user_sidebar(user)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "pendo_conversation_id" not in st.session_state:
        st.session_state.pendo_conversation_id = str(uuid.uuid4())

    # ── Welcome screen: use a placeholder so it clears immediately ───────────
    # The placeholder is emptied before rendering the user's first message,
    # ensuring the welcome text never coexists with chat content.
    welcome_placeholder = st.empty()

    if not st.session_state.messages:
        welcome_placeholder.markdown(
            """
            <div class="web-welcome">
                <h1>Welcome to AI Assistant</h1>
                <p>Ask me anything — I'm here to help.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Render existing messages
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(str(msg["content"]))
            if msg["role"] == "assistant":
                _render_sources(msg.get("sources", []))
                conv_id = msg.get("conv_id")
                chunk_ids = msg.get("chunk_ids", [])
                if conv_id:
                    _render_feedback_buttons(
                        conv_id, user["id"], chunk_ids, company_id, role,
                        msg.get("pendo_msg_id"),
                    )

    if raw_query := st.chat_input("Ask anything…"):
        # Clear the welcome screen immediately before showing any chat content
        welcome_placeholder.empty()

        _track_agent("prompt", {
            "agentId": _PENDO_AGENT_ID,
            "conversationId": st.session_state.pendo_conversation_id,
            "messageId": str(uuid.uuid4()),
            "content": raw_query,
        })

        st.session_state.messages.append({"role": "user", "content": raw_query})
        with st.chat_message("user"):
            st.markdown(raw_query)

        # ── Pendo: track user prompt ─────────────────────────────────────────
        _track_agent("prompt", {
            "agentId": _PENDO_AGENT_ID,
            "conversationId": st.session_state.pendo_conversation_id,
            "messageId": f"prompt_{int(time.time() * 1000)}",
            "content": raw_query,
        })

        _run_pipeline(raw_query, user, company_id, role)


render()
