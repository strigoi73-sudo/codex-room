from __future__ import annotations

from .money import dollars_to_cents


def summarize_orders(orders) -> dict:
    try:
        rows = list(orders)
    except TypeError as exc:
        raise ValueError("orders must be iterable") from exc
    total = 0
    by_category: dict[str, int] = {}
    seen_ids: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("order must be a dictionary")
        order_id = row.get("id")
        category = row.get("category")
        if not isinstance(order_id, str) or not order_id:
            raise ValueError("order id must be a non-empty string")
        if order_id in seen_ids:
            raise ValueError("order id must be unique")
        seen_ids.add(order_id)
        if not isinstance(category, str) or not category:
            raise ValueError("category must be a non-empty string")
        try:
            cents = dollars_to_cents(row.get("amount"))
        except ValueError as exc:
            raise ValueError("invalid order amount") from exc
        total += cents
        by_category[category] = by_category.get(category, 0) + cents
    return {
        "count": len(rows),
        "total_cents": total,
        "by_category_cents": by_category,
    }
