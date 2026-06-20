"""
pipeline/lang_detect.py
-----------------------
Step 2 of the RAG pipeline.
Detects the language of an input string and normalises it to
one of the three supported codes: 'en', 'ru', 'kk'.
Falls back to 'en' on any error.
"""

from typing import Literal

from langdetect import detect, LangDetectException

SupportedLang = Literal["en", "ru", "kk"]

# langdetect returns 'ko' for Kazakh sometimes; include extra aliases
_KK_ALIASES = {"kk", "ky"}
_RU_ALIASES = {"ru", "bg", "mk", "sr"}  # Cyrillic neighbours → treat as RU


def detect_language(text: str) -> SupportedLang:
    """
    Detect the dominant language of *text*.

    Returns:
        'en' | 'ru' | 'kk'  (defaults to 'en' on any failure)
    """
    if not text or not text.strip():
        return "en"

    try:
        code = detect(text.strip())
    except LangDetectException:
        return "en"
    except Exception as exc:
        print(f"[lang_detect] Unexpected error: {exc}")
        return "en"

    if code in _KK_ALIASES:
        return "kk"
    if code in _RU_ALIASES:
        return "ru"
    return "en"


# ── no-docs fallback messages ─────────────────────────────────────────────────
NO_DOCS_MSG: dict = {
    "en": "This information was not found in the available documents.",
    "ru": "Эта информация не найдена в доступных документах.",
    "kk": "Бұл ақпарат қолжетімді құжаттарда табылмады.",
}


def no_docs_message(lang: SupportedLang) -> str:
    """Return the 'no documents found' reply in the correct language."""
    return NO_DOCS_MSG.get(lang, NO_DOCS_MSG["en"])
