from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def dollars_to_cents(value: object) -> int:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("invalid amount") from exc
    if not amount.is_finite():
        raise ValueError("invalid amount")
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def summarize_transactions(rows):
    raise NotImplementedError
