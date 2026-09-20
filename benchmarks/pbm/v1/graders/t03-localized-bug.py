from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


workspace = Path(sys.argv[1])
checks: list[dict[str, object]] = []

try:
    spec = importlib.util.spec_from_file_location("pbm_t03_slug", workspace / "slug.py")
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)

    cases = {
        "  Hello, World!  ": "hello-world",
        "Café Déjà Vu": "cafe-deja-vu",
        "Crème brûlée": "creme-brulee",
        "one___two---three": "one-two-three",
        "": "",
    }
    for value, expected in cases.items():
        checks.append(
            {
                "name": f"case:{value!r}",
                "ok": module.normalize_slug(value) == expected,
            }
        )
    try:
        module.normalize_slug(123)
        type_ok = False
    except TypeError:
        type_ok = True
    checks.append({"name": "non_string_type_error", "ok": type_ok})
except Exception as exc:
    checks.append({"name": "module_loads", "ok": False, "detail": type(exc).__name__})

passed = sum(1 for item in checks if item["ok"])
score = round(100 * passed / len(checks))
print(json.dumps({"pass": passed == len(checks), "score": score, "checks": checks}))
