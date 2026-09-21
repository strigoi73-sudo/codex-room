# Incident report

## Root cause

The payment worker generated the gateway idempotency key from the durable order id plus a fresh per-attempt timestamp [S401]. The first attempts for the affected orders timed out in the worker [W103], but the gateway audit shows that those first requests had already been accepted [G201, G203]. Because a retry generated a different key [W104], the gateway treated the retry as a new charge rather than the same idempotent operation [G202, G204]. This matches the gateway contract: deduplication applies only when the caller reuses the same idempotency key [R501].

## Causal chain

For each affected order, the gateway accepted the first charge before the client had a successful response [G201, G203]. The worker then hit its 800 ms client timeout [W103], an outcome the operating notes explicitly classify as ambiguous [R502]. The retry began as a new attempt and therefore produced a different key [S401, W104]. The gateway accepted that second key as a distinct charge [G202, G204].

## Competing hypotheses

Duplicate upstream submission is not supported: the ingress scan found no duplicate order or payment-intent submissions in the incident window [I205]. Concurrent worker double-claim is not supported: both affected jobs have one durable claim and no lease overlap [J301, J302]. Database-pool exhaustion is not the primary cause: the pool was healthy shortly before the incident [D301], while the visible saturation warning appears later at 09:43:40 [D304], after the duplicate charge sequence had already occurred.

## Recommended controls

Use the durable payment intent as the stable idempotency identity for every retry of the same intended charge, as permitted by the gateway notes [R503]. In addition, treat a timeout as an ambiguous outcome and reconcile the original request before issuing any retry that cannot prove it preserves the same idempotency identity [R502].
