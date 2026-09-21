from __future__ import annotations

from decimal import Decimal, InvalidOperation


def dollars_to_cents(value) -> int:
    if isinstance(value, bool):
        raise ValueError("amount must be a decimal-dollar value")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("amount must be a decimal-dollar value") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError("amount must be finite and non-negative")
    cents = amount * 100
    if cents != cents.to_integral_value():
        raise ValueError("amount may not contain fractions of a cent")
    return int(cents)
