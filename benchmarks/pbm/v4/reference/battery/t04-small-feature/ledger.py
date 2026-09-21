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
    count = 0
    total_cents = 0
    by_category_cents: dict[str, int] = {}

    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid row")
        category = row.get("category")
        if not isinstance(category, str) or not category.strip():
            raise ValueError("invalid category")
        if "amount" not in row:
            raise ValueError("invalid amount")
        cents = dollars_to_cents(row["amount"])
        count += 1
        total_cents += cents
        by_category_cents[category] = by_category_cents.get(category, 0) + cents

    return {
        "count": count,
        "total_cents": total_cents,
        "by_category_cents": by_category_cents,
    }
