from __future__ import annotations

import re

NORMALIZATION_PATTERN = re.compile(r"[^a-z0-9]+")


def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    normalized = NORMALIZATION_PATTERN.sub(" ", value.casefold()).strip()
    return " ".join(normalized.split())
