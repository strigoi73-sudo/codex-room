# Escaped-field codec

The wire format represents a list of string fields.

- Fields are separated by an unescaped vertical bar (`|`).
- Within a field, a literal backslash is encoded as two backslashes.
- Within a field, a literal vertical bar is encoded as backslash + vertical bar.
- `encode(fields)` accepts an iterable of strings and returns one wire-format string.
- `decode(text)` returns the original list of strings.
- Empty fields are significant and must be preserved. Therefore `decode("") == [""]`.
- A dangling terminal backslash is invalid and must raise `ValueError`.
- An escape sequence other than backslash-backslash or backslash-vertical-bar is invalid and must raise `ValueError`.
- Non-string fields passed to `encode`, and non-string text passed to `decode`, raise `TypeError`.
