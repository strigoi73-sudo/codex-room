from __future__ import annotations

import hashlib
from typing import Any


class GatewayTimeout(RuntimeError):
    pass


def charge_idempotency_key(job: dict[str, Any], attempt_started_at: str) -> str:
    # [S401] attempt_started_at is generated afresh for every gateway attempt.
    material = f"{job['order_id']}|{attempt_started_at}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def process_job(job: dict[str, Any], gateway: Any, clock: Any, sleep: Any, config: dict[str, Any]) -> str:
    # [S402] A claimed job stays owned by this worker while gateway attempts are retried.
    max_attempts = int(config["gateway_max_attempts"])
    retry_delay_ms = int(config["gateway_retry_delay_ms"])

    for attempt in range(1, max_attempts + 1):
        attempt_started_at = clock.now_iso()
        key = charge_idempotency_key(job, attempt_started_at)
        try:
            return gateway.charge(
                payment_intent_id=job["payment_intent_id"],
                order_id=job["order_id"],
                amount_cents=job["amount_cents"],
                idempotency_key=key,
                timeout_ms=int(config["gateway_timeout_ms"]),
            )
        except GatewayTimeout:
            if attempt == max_attempts:
                raise
            sleep(retry_delay_ms / 1000)

    raise AssertionError("unreachable")
