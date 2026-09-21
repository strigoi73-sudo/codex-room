from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

from .codec import encode
from .inventory import reserve_inventory
from .report import summarize_orders


def run_payload(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("input must be a JSON object")
    working = copy.deepcopy(payload)
    inventory = working.get("inventory")
    reservations = working.get("reservations")
    orders = working.get("orders")
    if not isinstance(inventory, dict):
        raise ValueError("inventory is required")
    if reservations is None:
        raise ValueError("reservations are required")
    if not isinstance(orders, list) or not orders:
        raise ValueError("orders must be a non-empty list")
    reserve_inventory(inventory, reservations)
    summary = summarize_orders(orders)
    ids = [row["id"] for row in orders]
    return {
        "remaining_inventory": inventory,
        "summary": summary,
        "encoded_order_ids": encode(ids),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        with open(args.input_json, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        result = run_payload(payload)
        text = json.dumps(result, sort_keys=True) + "\n"
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
        return 0
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
