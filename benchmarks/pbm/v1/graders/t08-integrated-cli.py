from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


workspace = Path(sys.argv[1])
python = sys.executable
checks: list[dict[str, object]] = []


def run(*extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [python, "report.py", "--input", "orders.csv", *extra],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


all_run = run()
try:
    all_payload = json.loads(all_run.stdout)
except json.JSONDecodeError:
    all_payload = None
checks.append(
    {
        "name": "all_regions",
        "ok": all_run.returncode == 0
        and all_payload
        == {"region": "ALL", "order_count": 4, "total_amount": 37.67},
    }
)

north_run = run("--region", "NORTH")
try:
    north_payload = json.loads(north_run.stdout)
except json.JSONDecodeError:
    north_payload = None
checks.append(
    {
        "name": "case_insensitive_region",
        "ok": north_run.returncode == 0
        and north_payload
        == {"region": "North", "order_count": 2, "total_amount": 10.4},
    }
)

missing_run = run("--region", "East")
checks.append(
    {
        "name": "unknown_region_fails",
        "ok": missing_run.returncode != 0
        and "unknown region" in missing_run.stderr.lower(),
    }
)

passed = sum(1 for item in checks if item["ok"])
score = round(100 * passed / len(checks))
print(json.dumps({"pass": passed == len(checks), "score": score, "checks": checks}))
