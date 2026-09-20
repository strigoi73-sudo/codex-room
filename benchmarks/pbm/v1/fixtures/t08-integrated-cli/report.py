from __future__ import annotations

import argparse
import json

from orders import load_orders, summarize


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    print(json.dumps(summarize(load_orders(args.input)), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
