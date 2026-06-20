"""
pipeline/generator.py
---------------------
Step 7 of the RAG pipeline.
Uses openai/gpt-oss-120b via Groq with streaming.
Yields text chunks so the caller can feed them to st.write_stream.
If no context documents are found, returns the appropriate no-docs message.
"""

import os
from typing import Dict, Generator, List, Optional

from groq import Groq

from pipeline.lang_detect import SupportedLang, no_docs_message

_GROQ_GENERATION_MODEL = os.getenv("GROQ_GENERATION_MODEL", "openai/gpt-oss-120b")

_SYSTEM_TEMPLATE = """You are AdaptIQ, an expert AI assistant.
Use the provided context documents as your primary source.
If the context does not fully cover the question, supplement with your general knowledge — but stay factual and helpful.
Always answer in the same language as the user's question.
Be concise, accurate, and helpful.

Context:
{context}"""

_SYSTEM_TEMPLATE_NO_DOCS = """You are AdaptIQ, a knowledgeable AI assistant.
No specific documents are available for this question, so answer using your general knowledge.
Be helpful, factual, and engaging.
Always answer in the same language as the user's question."""


def _build_context(chunks: List[Dict]) -> str:
    """Combine retrieved chunks into a single context block."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        meta   = chunk.get("metadata", {})
        source = meta.get("source_file") or meta.get("website_url", "unknown")
        text   = chunk.get("text", "").strip()
        parts.append(f"[{i}] (source: {source})\n{text}")
    return "\n\n".join(parts)


def generate(
    query: str,
    chunks: List[Dict],
    lang: SupportedLang = "en",
    conversation_history: Optional[List[Dict]] = None,
) -> Generator[str, None, None]:
    """
    Stream the LLM response token-by-token.

    Yields:
        str chunks that can be consumed by st.write_stream.

    Falls back to the no-docs message if chunks are empty or API is unavailable.
    """
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        yield "[generator] GROQ_API_KEY not set – cannot generate a response."
        return

    # ── Build system prompt ───────────────────────────────────────────────────
    if chunks:
        context    = _build_context(chunks)
        system_msg = _SYSTEM_TEMPLATE.format(context=context)
    else:
        system_msg = _SYSTEM_TEMPLATE_NO_DOCS

    messages: List[Dict] = [{"role": "system", "content": system_msg}]

    # Optionally include recent conversation turns for follow-up context
    if conversation_history:
        for turn in conversation_history[-4:]:   # last 2 exchanges
            messages.append(turn)

    messages.append({"role": "user", "content": query})

    try:
        client = Groq(api_key=api_key)
        stream = client.chat.completions.create(
            model=_GROQ_GENERATION_MODEL,
            messages=messages,
            temperature=0.4,
            max_tokens=1024,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                yield content

    except Exception as exc:
        print(f"[generator] Groq streaming error: {exc}")
        yield no_docs_message(lang)


def generate_full(
    query: str,
    chunks: List[Dict],
    lang: SupportedLang = "en",
    conversation_history: Optional[List[Dict]] = None,
) -> str:
    """
    Non-streaming version – collects the full response and returns it as a string.
    Useful for background tasks and feedback analysis.
    """
    parts = list(generate(query, chunks, lang, conversation_history))
    return "".join(parts)
