from __future__ import annotations

import json
import sys
from pathlib import Path


workspace = Path(sys.argv[1])
fixture = Path(__file__).resolve().parents[1] / "fixtures" / "t02-bounded-investigation"
checks: list[dict[str, object]] = []

expected = {
    "connect_timeout_seconds": 4,
    "read_timeout_seconds": 11,
    "request_timeout_seconds": 15,
    "maximum_attempts": 3,
    "evidence_files": [
        "config/defaults.json",
        "docs/ops.md",
        "src/service.py",
    ],
}

try:
    observed = json.loads((workspace / "analysis.json").read_text(encoding="utf-8"))
    normalized = dict(observed)
    if isinstance(normalized.get("evidence_files"), list):
        normalized["evidence_files"] = sorted(normalized["evidence_files"])
    checks.append({"name": "analysis_values", "ok": normalized == expected})
except Exception as exc:
    checks.append({"name": "analysis_values", "ok": False, "detail": type(exc).__name__})

for rel in ("config/defaults.json", "src/service.py", "docs/ops.md"):
    checks.append(
        {
            "name": f"immutable:{rel}",
            "ok": (workspace / rel).read_bytes() == (fixture / rel).read_bytes(),
        }
    )

passed = sum(1 for item in checks if item["ok"])
score = round(100 * passed / len(checks))
print(json.dumps({"pass": passed == len(checks), "score": score, "checks": checks}))
