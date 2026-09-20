from __future__ import annotations


def encode(fields) -> str:
    return "|".join(field.replace("|", "\\|") for field in fields)


def decode(text: str) -> list[str]:
    return text.split("|")
