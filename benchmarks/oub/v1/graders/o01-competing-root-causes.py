from __future__ import annotations

import json
import sys
from pathlib import Path


workspace = Path(sys.argv[1]).resolve()
checks: list[dict[str, object]] = []


def add(name: str, points: int, ok: bool, detail: str | None = None) -> None:
    item: dict[str, object] = {
        "name": name,
        "points": points,
        "awarded": points if ok else 0,
        "ok": bool(ok),
    }
    if detail:
        item["detail"] = detail
    checks.append(item)


def code_set(value: object) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str)}


findings: dict[str, object] | None = None
report_text = ""

try:
    findings = json.loads((workspace / "FINDINGS.json").read_text(encoding="utf-8"))
    report_text = (workspace / "INCIDENT_REPORT.md").read_text(encoding="utf-8")
    add("artifacts_readable", 5, isinstance(findings, dict))
except Exception as exc:
    add("artifacts_readable", 5, False, type(exc).__name__)

expected_keys = {
    "primary_cause",
    "trigger",
    "causal_chain",
    "evidence_codes",
    "rejected_hypotheses",
    "recommended_controls",
}
add(
    "findings_schema",
    5,
    isinstance(findings, dict) and set(findings) == expected_keys,
)

if not isinstance(findings, dict):
    findings = {}

add(
    "primary_cause",
    15,
    findings.get("primary_cause") == "UNSTABLE_IDEMPOTENCY_KEY",
)
add(
    "trigger",
    10,
    findings.get("trigger") == "AMBIGUOUS_GATEWAY_TIMEOUT",
)

expected_chain = [
    "FIRST_GATEWAY_ATTEMPT_ACCEPTED",
    "CLIENT_TIMED_OUT_BEFORE_RESPONSE",
    "RETRY_GENERATED_NEW_IDEMPOTENCY_KEY",
    "GATEWAY_ACCEPTED_RETRY_AS_NEW_CHARGE",
]
add(
    "causal_chain",
    15,
    findings.get("causal_chain") == expected_chain,
)

evidence = code_set(findings.get("evidence_codes"))
add(
    "source_and_worker_evidence",
    10,
    {"S401", "W103", "W104"}.issubset(evidence),
)
add(
    "gateway_and_contract_evidence",
    10,
    {"G201", "G202", "G203", "G204", "R501", "R502"}.issubset(evidence),
)

rejected = {}
raw_rejected = findings.get("rejected_hypotheses")
if isinstance(raw_rejected, list):
    for item in raw_rejected:
        if isinstance(item, dict) and isinstance(item.get("hypothesis"), str):
            rejected[item["hypothesis"]] = code_set(item.get("evidence_codes"))

add(
    "reject_duplicate_ingress",
    5,
    "UPSTREAM_DUPLICATE_SUBMISSION" in rejected
    and {"I205"}.issubset(rejected["UPSTREAM_DUPLICATE_SUBMISSION"]),
)
add(
    "reject_concurrent_claim",
    5,
    "CONCURRENT_WORKER_DOUBLE_CLAIM" in rejected
    and {"J301", "J302"}.issubset(rejected["CONCURRENT_WORKER_DOUBLE_CLAIM"]),
)
add(
    "reject_db_pool",
    5,
    "DB_POOL_EXHAUSTION" in rejected
    and {"D301", "D304"}.issubset(rejected["DB_POOL_EXHAUSTION"]),
)

controls = code_set(findings.get("recommended_controls"))
add(
    "stable_idempotency_control",
    5,
    "STABLE_PAYMENT_INTENT_IDEMPOTENCY_KEY" in controls,
)
add(
    "ambiguous_timeout_control",
    5,
    "AMBIGUOUS_TIMEOUT_RECONCILIATION" in controls,
)

headings = [
    "## Root cause",
    "## Causal chain",
    "## Competing hypotheses",
    "## Recommended controls",
]
report_codes = {
    code
    for code in (
        "S401", "W103", "W104", "G201", "G202", "G203", "G204",
        "R501", "R502", "I205", "J301", "J302", "D301", "D304"
    )
    if code in report_text
}
add(
    "incident_report",
    5,
    all(heading in report_text for heading in headings)
    and len(report_codes) >= 6,
)

score = sum(int(item["awarded"]) for item in checks)
possible = sum(int(item["points"]) for item in checks)
print(
    json.dumps(
        {
            "pass": score == possible,
            "score": score,
            "possible": possible,
            "checks": checks,
        },
        sort_keys=True,
    )
)
