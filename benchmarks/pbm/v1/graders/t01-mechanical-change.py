from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


workspace = Path(sys.argv[1])
checks: list[dict[str, object]] = []

try:
    spec = importlib.util.spec_from_file_location("pbm_t01_settings", workspace / "settings.py")
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    checks.append({"name": "default_constant_is_5", "ok": module.DEFAULT_RETRY_LIMIT == 5})
    checks.append({"name": "public_function_returns_5", "ok": module.get_retry_limit() == 5})
except Exception as exc:
    checks.append({"name": "module_loads", "ok": False, "detail": type(exc).__name__})

passed = sum(1 for item in checks if item["ok"])
score = round(100 * passed / len(checks))
print(json.dumps({"pass": passed == len(checks), "score": score, "checks": checks}))
