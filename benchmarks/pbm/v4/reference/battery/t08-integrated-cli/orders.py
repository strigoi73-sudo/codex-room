from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path


def load_orders(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def summarize(
    rows: list[dict[str, str]],
    region: str | None = None,
) -> dict[str, object]:
    selected = rows
    output_region = "ALL"

    if region is not None:
        target = region.casefold()
        matching = [row for row in rows if row["region"].casefold() == target]
        if not matching:
            raise ValueError(f"unknown region: {region}")
        output_region = matching[0]["region"]
        selected = matching

    total = sum((Decimal(row["amount"]) for row in selected), Decimal("0"))
    return {
        "region": output_region,
        "order_count": len(selected),
        "total_amount": float(total),
    }
