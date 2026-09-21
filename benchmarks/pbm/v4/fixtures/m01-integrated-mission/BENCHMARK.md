# Integrated fulfillment benchmark

Work only inside this workspace. Do not inspect PBM manifests, harness code, hidden graders, reference solutions, the other product's workspace, or prior benchmark results.

Your objective is to turn this small fulfillment repository into a correct, verified deliverable.

## 1. Escaped-field codec

Audit `order_tool/codec.py` against `CODEC_SPEC.md` and repair it completely.

## 2. Atomic inventory reservation

Repair `order_tool/inventory.py::reserve_inventory(inventory, requests)`.

Contract:

- `inventory` is a dictionary from non-empty string SKU to a non-negative integer quantity;
- `requests` is an iterable of dictionaries with exactly usable `sku` and `quantity` values;
- each SKU must be a non-empty string and each quantity must be a positive integer (bool is invalid);
- missing SKU, invalid data, or insufficient stock raises `ValueError`;
- on any failure, `inventory` must remain exactly unchanged;
- on success, mutate `inventory` once to the final remaining quantities and return that same dictionary;
- duplicate request rows for the same SKU are allowed and must be validated against their combined demand.

## 3. Order summary

Implement `order_tool/report.py::summarize_orders(orders)`.

Each order must contain:

- `id`: non-empty string, unique within the input;
- `category`: non-empty string, case-sensitive;
- `amount`: a decimal-dollar value accepted by the existing `dollars_to_cents`.

Return:

```json
{
  "count": 2,
  "total_cents": 1575,
  "by_category_cents": {
    "retail": 1575
  }
}
```

Invalid input raises `ValueError`. Do not mutate input orders.

## 4. Integrated CLI

Repair `order_tool/cli.py`.

Command:

```
python -m order_tool.cli INPUT_JSON [--output OUTPUT_JSON]
```

The input JSON object has:

- `inventory`: inventory dictionary;
- `reservations`: reservation rows for `reserve_inventory`;
- `orders`: order rows for `summarize_orders`.

On success output exactly one JSON object with keys:

- `remaining_inventory`;
- `summary`;
- `encoded_order_ids`, produced by the repaired codec from the order ids in input order.

Without `--output`, write the JSON to stdout followed by one newline. With `--output`, write it to that file and do not emit the result JSON on stdout.

The integrated operation must not mutate the parsed input object. On invalid input, print `error: <message>` to stderr, return exit code 2, and do not create or overwrite the requested output file.

Use only the Python standard library.

## 5. Evidence-backed storage decision

Read `storage_options.json`. Create `storage_decision.json` containing:

```json
{
  "backend": "<selected backend>",
  "evidence_codes": ["<code>", "..."]
}
```

Choose the backend that satisfies every listed required constraint. Evidence codes must come from the selected option's `evidence` entries and must substantively support the choice.

Do not use outside research.

## 6. Verification and completion artifacts

Run the public tests and any additional checks you consider useful.

Create `BENCHMARK_REPORT.md` with these exact Markdown headings:

- `## Investigation`
- `## Changes`
- `## Verification`
- `## Storage decision`

When all work and verification are complete, create `PBM_COMPLETE.json` exactly as:

```json
{
  "status": "complete",
  "verification": "passed"
}
```

Do not create that marker before completing your verification.
