from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


workspace = Path(sys.argv[1])
checks: list[dict[str, object]] = []

try:
    spec = importlib.util.spec_from_file_location("pbm_t07_codec", workspace / "codec.py")
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)

    cases = [
        [""],
        ["a", "b", ""],
        ["a|b", r"c\d", ""],
        [r"\", "|", r"x\|y"],
    ]
    for fields in cases:
        checks.append(
            {
                "name": f"roundtrip:{fields!r}",
                "ok": module.decode(module.encode(fields)) == fields,
            }
        )

    invalid_decode_ok = True
    for text in ("abc\\", r"abc\q"):
        try:
            module.decode(text)
            invalid_decode_ok = False
        except ValueError:
            pass
    checks.append({"name": "invalid_escapes_rejected", "ok": invalid_decode_ok})

    type_ok = True
    try:
        module.encode(["ok", 3])
        type_ok = False
    except TypeError:
        pass
    try:
        module.decode(3)
        type_ok = False
    except TypeError:
        pass
    checks.append({"name": "type_errors", "ok": type_ok})
except Exception as exc:
    checks.append({"name": "module_loads", "ok": False, "detail": type(exc).__name__})

passed = sum(1 for item in checks if item["ok"])
score = round(100 * passed / len(checks))
print(json.dumps({"pass": passed == len(checks), "score": score, "checks": checks}))
