from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


workspace = Path(sys.argv[1])
checks: list[dict[str, object]] = []

try:
    spec = importlib.util.spec_from_file_location(
        "pbm_t05_reservations", workspace / "reservations.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)

    stock = {"AbC-1": 5, "XYZ": 2}
    remaining = module.reserve(stock, "abc-1", 2)
    checks.append(
        {
            "name": "case_insensitive_success",
            "ok": remaining == 3 and stock == {"AbC-1": 3, "XYZ": 2},
        }
    )

    failures = [
        ("ABC-1", 0, ValueError),
        ("ABC-1", True, ValueError),
        ("ABC-1", 99, ValueError),
        ("missing", 1, KeyError),
    ]
    atomic_ok = True
    for sku, quantity, expected_error in failures:
        before = dict(stock)
        try:
            module.reserve(stock, sku, quantity)
            atomic_ok = False
        except expected_error:
            pass
        except Exception:
            atomic_ok = False
        if stock != before:
            atomic_ok = False
    checks.append({"name": "failures_are_atomic_and_typed", "ok": atomic_ok})
except Exception as exc:
    checks.append({"name": "module_loads", "ok": False, "detail": type(exc).__name__})

passed = sum(1 for item in checks if item["ok"])
score = round(100 * passed / len(checks))
print(json.dumps({"pass": passed == len(checks), "score": score, "checks": checks}))
