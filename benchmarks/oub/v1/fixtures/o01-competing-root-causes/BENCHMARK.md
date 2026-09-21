# O1 — Ambiguous duplicate-charge incident

Work only inside this workspace. Do not inspect OUB/PBM manifests, harness code, hidden graders, reference solutions, the other product's workspace, or prior benchmark results. Do not use outside research.

You are investigating a production incident in a fictional payment service.

Between 09:42 and 09:43 UTC, two customer orders were charged twice. Several explanations have been proposed:

- duplicate upstream submissions;
- two workers claiming the same job concurrently;
- database-pool exhaustion causing inconsistent state;
- a retry/idempotency failure around the payment gateway.

Your job is to determine what actually happened from the supplied evidence.

## Required investigation

Establish:

1. the primary root cause;
2. the triggering condition that made the latent defect observable;
3. the ordered causal chain from the original job to the duplicate charge;
4. why each major competing hypothesis is not the primary explanation;
5. the minimum controls that would prevent recurrence.

Do not modify the supplied evidence files.

## Required artifact: FINDINGS.json

Create `FINDINGS.json` with exactly these top-level keys:

```json
{
  "primary_cause": "<UPPER_SNAKE_CASE code>",
  "trigger": "<UPPER_SNAKE_CASE code>",
  "causal_chain": [
    "<UPPER_SNAKE_CASE step>",
    "..."
  ],
  "evidence_codes": ["<code>", "..."],
  "rejected_hypotheses": [
    {
      "hypothesis": "<UPPER_SNAKE_CASE code>",
      "evidence_codes": ["<code>", "..."]
    }
  ],
  "recommended_controls": ["<UPPER_SNAKE_CASE control>", "..."]
}
```

Use evidence codes that actually appear in the supplied files. Include only evidence you rely on.

The rejected hypotheses must address all three non-primary alternatives listed above.

## Required artifact: INCIDENT_REPORT.md

Create `INCIDENT_REPORT.md` with these exact Markdown headings:

- `## Root cause`
- `## Causal chain`
- `## Competing hypotheses`
- `## Recommended controls`

Explain the diagnosis in your own words and cite the evidence codes you relied on.

When the investigation is complete, stop.
