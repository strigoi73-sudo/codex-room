from __future__ import annotations

import argparse
import json

from .report import summarize_orders


def run_payload(payload: dict) -> dict:
    return {"summary": summarize_orders(payload["orders"])}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    with open(args.input_json, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    result = run_payload(payload)
    text = json.dumps(result, sort_keys=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
