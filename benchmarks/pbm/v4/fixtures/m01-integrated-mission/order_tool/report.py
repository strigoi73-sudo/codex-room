from __future__ import annotations

from .money import dollars_to_cents


def summarize_orders(orders) -> dict:
    rows = list(orders)
    return {
        "count": len(rows),
        "total_cents": 0,
        "by_category_cents": {},
    }
