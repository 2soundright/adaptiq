"""
pipeline/query_transform.py
---------------------------
Step 3 of the RAG pipeline.
Uses llama-3.1-8b-instant via Groq to:
  1. Expand the query with context from the knowledge base.
  2. Strip injection phrases before they reach the retriever.
"""

import os
import re
from typing import List

from groq import Groq

_GROQ_TRANSFORM_MODEL = os.getenv("GROQ_TRANSFORM_MODEL", "llama-3.1-8b-instant")

# Phrases that indicate a prompt-injection attempt
_INJECTION_PATTERNS: List[str] = [
    r"ignore\s+(previous|all|prior)\s+(instructions?|prompts?|context)",
    r"system\s*:",
    r"you\s+are\s+now",
    r"forget\s+(everything|all|previous)",
    r"disregard\s+(all|previous|prior)",
    r"new\s+persona",
    r"act\s+as\s+if",
    r"pretend\s+(you\s+are|to\s+be)",
    r"override\s+(your|all)\s+(instructions?|rules?)",
]
_INJECTION_RE = re.compile(
    "|".join(_INJECTION_PATTERNS),
    flags=re.IGNORECASE,
)

_SYSTEM_PROMPT = """You are a query expansion assistant for AdaptIQ, an AI knowledge base assistant.

Your task:
1. Rewrite the user query to be more specific and retrieve better results from the knowledge base.

2. Return ONLY the rewritten query – no explanations, no extra text.

Rules:
- Keep the same language as the original query (EN / RU / KK)
- Do not add invented facts
- Make it 1-2 sentences maximum
- If the original query is already clear and specific, return it as-is"""


def strip_injections(text: str) -> str:
    """Remove known injection phrases from the text."""
    try:
        cleaned = _INJECTION_RE.sub("", text)
        # Collapse multiple spaces left after removal
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
        return cleaned if cleaned else text
    except Exception as exc:
        print(f"[query_transform] strip_injections error: {exc}")
        return text


def transform_query(query: str) -> str:
    """
    Sanitise and expand a raw user query.

    Returns:
        Transformed query string. Falls back to the sanitised original on error.
    """
    # Always strip injections first, regardless of API availability
    safe_query = strip_injections(query)
    if not safe_query.strip():
        return query

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        print("[query_transform] GROQ_API_KEY not set – skipping expansion.")
        return safe_query

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=_GROQ_TRANSFORM_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": safe_query},
            ],
            temperature=0.3,
            max_tokens=256,
        )
        expanded = response.choices[0].message.content.strip()
        # One final injection pass on the model's output
        return strip_injections(expanded) if expanded else safe_query
    except Exception as exc:
        print(f"[query_transform] Groq API error, using safe_query: {exc}")
        return safe_query
