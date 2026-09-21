# Escaped-field codec

The wire format represents a **non-empty** list of string fields.

- Fields are separated by an unescaped vertical bar (`|`).
- Within a field, a literal backslash is encoded as two backslashes.
- Within a field, a literal vertical bar is encoded as backslash + vertical-bar.
- `encode(fields)` accepts an iterable of strings.
- Passing an empty iterable to `encode` is invalid and raises `ValueError`.
- `decode(text)` returns the original non-empty list of strings.
- Empty fields are significant. Therefore `decode("") == [""]`, and `encode([""]) == ""`.
- A dangling terminal backslash is invalid and raises `ValueError`.
- An escape other than backslash-backslash or backslash-vertical-bar is invalid and raises `ValueError`.
- Non-string fields passed to `encode), and non-string `text` passed to `decode`, raise `TypeError`.

These rules deliberately make the empty-list case unambiguous: it is not representable and `encode([])` must fail.
