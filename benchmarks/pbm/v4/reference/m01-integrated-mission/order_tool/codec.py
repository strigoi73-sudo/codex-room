from __future__ import annotations


def encode(fields) -> str:
    encoded: list[str] = []
    saw_any = False
    for field in fields:
        saw_any = True
        if not isinstance(field, str):
            raise TypeError("fields must contain only strings")
        encoded.append(field.replace("\\", "\\\\").replace("|", "\\|"))
    if not saw_any:
        raise ValueError("fields must be non-empty")
    return "|".join(encoded)


def decode(text: str) -> list[str]:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    fields: list[str] = []
    current: list[str] = []
    escaped = False
    for char in text:
        if escaped:
            if char not in {"\\", "|"}:
                raise ValueError("invalid escape")
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
        elif char == "|":
            fields.append("".join(current))
            current = []
        else:
            current.append(char)
    if escaped:
        raise ValueError("dangling escape")
    fields.append("".join(current))
    return fields
