from __future__ import annotations

import argparse
import json
import sys

from orders import load_orders, summarize


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--region")
    args = parser.parse_args()

    try:
        payload = summarize(load_orders(args.input), args.region)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
