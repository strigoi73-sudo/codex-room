from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path


def load_orders(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def summarize(rows: list[dict[str, str]]) -> dict[str, object]:
    total = sum(Decimal(row["amount"]) for row in rows)
    return {
        "region": "ALL",
        "order_count": len(rows),
        "total_amount": float(total),
    }
