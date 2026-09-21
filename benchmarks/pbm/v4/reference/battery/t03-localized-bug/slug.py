from __future__ import annotations

import re
import unicodedata


def normalize_slug(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("value must be a string")
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    asciiish = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return re.sub(r"[^a-z0-9]+", "-", asciiish).strip("-")
