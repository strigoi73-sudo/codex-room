from __future__ import annotations

import json
import sys
from pathlib import Path


workspace = Path(sys.argv[1])
fixture = Path(__file__).resolve().parents[1] / "fixtures" / "t06-constrained-design"
checks: list[dict[str, object]] = []
must = [
    "no_external_service",
    "append_only",
    "human_inspectable",
    "retention_30_days",
    "recovery_point_5_minutes",
]

try:
    decision = json.loads((workspace / "decision.json").read_text(encoding="utf-8"))
    checks.append({"name": "selected_option", "ok": decision.get("selected_option") == "segmented-jsonl"})
    checks.append({"name": "monthly_cost", "ok": decision.get("monthly_cost_usd") == 15})
    checks.append(
        {
            "name": "satisfied_must",
            "ok": sorted(decision.get("satisfied_must") or []) == sorted(must),
        }
    )
    checks.append(
        {
            "name": "rationale_present",
            "ok": isinstance(decision.get("rationale"), str)
            and bool(decision["rationale"].strip()),
        }
    )
except Exception as exc:
    checks.append({"name": "decision_loads", "ok": False, "detail": type(exc).__name__})

for rel in ("requirements.json", "options.json"):
    checks.append(
        {
            "name": f"immutable:{rel}",
            "ok": (workspace / rel).read_bytes() == (fixture / rel).read_bytes(),
        }
    )

passed = sum(1 for item in checks if item["ok"])
score = round(100 * passed / len(checks))
print(json.dumps({"pass": passed == len(checks), "score": score, "checks": checks}))
