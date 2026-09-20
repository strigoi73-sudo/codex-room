from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path


workspace = Path(sys.argv[1])
checks: list[dict[str, object]] = []

try:
    spec = importlib.util.spec_from_file_location("pbm_t04_ledger", workspace / "ledger.py")
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)

    rows = [
        {"category": "Food", "amount": "1.25"},
        {"category": "Travel", "amount": 2},
        {"category": "Food", "amount": "0.335"},
    ]
    original = copy.deepcopy(rows)
    expected = {
        "count": 3,
        "total_cents": 359,
        "by_category_cents": {"Food": 159, "Travel": 200},
    }
    checks.append({"name": "summary", "ok": module.summarize_transactions(rows) == expected})
    checks.append({"name": "input_not_mutated", "ok": rows == original})

    invalid_cases = [
        [{"category": "", "amount": "1.00"}],
        [{"amount": "1.00"}],
        [{"category": "X", "amount": "not-a-number"}],
    ]
    invalid_ok = True
    for case in invalid_cases:
        try:
            module.summarize_transactions(case)
            invalid_ok = False
        except ValueError:
            pass
    checks.append({"name": "invalid_rows_raise_value_error", "ok": invalid_ok})
except Exception as exc:
    checks.append({"name": "module_loads", "ok": False, "detail": type(exc).__name__})

passed = sum(1 for item in checks if item["ok"])
score = round(100 * passed / len(checks))
print(json.dumps({"pass": passed == len(checks), "score": score, "checks": checks}))
