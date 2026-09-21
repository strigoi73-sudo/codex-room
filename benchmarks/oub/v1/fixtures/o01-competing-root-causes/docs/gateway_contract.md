# Payment gateway operating notes

[R501] The gateway's idempotency guarantee is keyed only by the caller-supplied `idempotency_key`. Repeating an otherwise identical charge with a different key is treated as a new charge.

[R502] A client-side timeout is an ambiguous outcome. The request may have been rejected before commit, or it may have committed and only the response was lost or delayed. Retrying an ambiguous request is safe only when the retry preserves the original idempotency identity or first reconciles the original request outcome.

[R503] `payment_intent_id` is a durable identifier created before job enqueue and is stable across worker retries for the same intended charge. It is approved for use as the stable idempotency identity for one payment intent.
