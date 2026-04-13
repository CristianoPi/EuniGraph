from __future__ import annotations

import re
import unicodedata

NORMALIZATION_PATTERN = re.compile(r"[^a-z0-9]+")


def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )
    normalized = NORMALIZATION_PATTERN.sub(" ", normalized.casefold()).strip()
    return " ".join(normalized.split())
