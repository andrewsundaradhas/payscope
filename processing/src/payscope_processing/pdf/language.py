from __future__ import annotations

from lingua import Language, LanguageDetectorBuilder


_DETECTOR = LanguageDetectorBuilder.from_languages(
    Language.ENGLISH,
    Language.SPANISH,
    Language.FRENCH,
    Language.GERMAN,
    Language.ITALIAN,
    Language.PORTUGUESE,
).build()


def detect_language(text: str) -> str | None:
    """
    Offline deterministic language detection.
    Returns ISO 639-1 code where available (e.g., 'en').
    """
    t = (text or "").strip()
    if len(t) < 20:
        return None
    lang = _DETECTOR.detect_language_of(t)
    if lang is None:
        return None
    return lang.iso_code_639_1.name.lower()




