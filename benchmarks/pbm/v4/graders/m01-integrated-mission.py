from __future__ import annotations

import copy
import importlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


workspace = Path(sys.argv[1]).resolve()
checks: list[dict[str, object]] = []


def add(name: str, ok: bool, detail: str | None = None) -> None:
    item: dict[str, object] = {"name": name, "ok": bool(ok)}
    if detail:
        item["detail"] = detail
    checks.append(item)


sys.path.insert(0, str(workspace))

try:
    public = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    add("public_tests", public.returncode == 0, (public.stderr or public.stdout)[-500:])
except Exception as exc:
    add("public_tests", False, type(exc).__name__)

try:
    codec = importlib.import_module("order_tool.codec")
    cases = [
        [""],
        ["a", "b", ""],
        ["a|b", "c\\d", ""],
        ["\\", "|", "x\\|y"],
    ]
    ok = all(codec.decode(codec.encode(fields)) == fields for fields in cases)
    try:
        codec.encode([])
        ok = False
    except ValueError:
        pass
    for invalid in ("abc\\", "abc\\q"):
        try:
            codec.decode(invalid)
            ok = False
        except ValueError:
            pass
    for call in (lambda: codec.encode(["ok", 3]), lambda: codec.decode(3)):
        try:
            call()
            ok = False
        except TypeError:
            pass
    add("codec_contract", ok)
except Exception as exc:
    add("codec_contract", False, type(exc).__name__)

try:
    inventory_mod = importlib.import_module("order_tool.inventory")
    inventory = {"a": 5, "b": 1}
    original = copy.deepcopy(inventory)
    ok = True
    try:
        inventory_mod.reserve_inventory(
            inventory,
            [{"sku": "a", "quantity": 3}, {"sku": "b", "quantity": 2}],
        )
        ok = False
    except ValueError:
        pass
    ok = ok and inventory == original
    try:
        inventory_mod.reserve_inventory(
            inventory,
            [{"sku": "a", "quantity": 3}, {"sku": "a", "quantity": 3}],
        )
        ok = False
    except ValueError:
        pass
    ok = ok and inventory == original
    result = inventory_mod.reserve_inventory(
        inventory,
        [{"sku": "a", "quantity": 2}, {"sku": "a", "quantity": 1}],
    )
    ok = ok and result is inventory and inventory == {"a": 2, "b": 1}
    add("inventory_atomicity", ok)
except Exception as exc:
    add("inventory_atomicity", False, type(exc).__name__)

try:
    report = importlib.import_module("order_tool.report")
    orders = [
        {"id": "o1", "category": "Retail", "amount": "10.01"},
        {"id": "o2", "category": "Retail", "amount": "2.99"},
        {"id": "o3", "category": "retail", "amount": "1.00"},
    ]
    original = copy.deepcopy(orders)
    expected = {
        "count": 3,
        "total_cents": 1400,
        "by_category_cents": {"Retail": 1300, "retail": 100},
    }
    ok = report.summarize_orders(orders) == expected and orders == original
    bad_sets = [
        [
            {"id": "dup", "category": "x", "amount": "1.00"},
            {"id": "dup", "category": "x", "amount": "2.00"},
        ],
        [{"id": "x", "category": "", "amount": "1.00"}],
        [{"id": "x", "category": "x", "amount": "1.001"}],
    ]
    for bad in bad_sets:
        try:
            report.summarize_orders(bad)
            ok = False
        except ValueError:
            pass
    add("summary_contract", ok)
except Exception as exc:
    add("summary_contract", False, type(exc).__name__)

sample_payload = {
    "inventory": {"a": 5, "b": 2},
    "reservations": [{"sku": "a", "quantity": 2}, {"sku": "b", "quantity": 1}],
    "orders": [
        {"id": "o|1", "category": "retail", "amount": "12.50"},
        {"id": "o\\2", "category": "wholesale", "amount": "3.25"},
    ],
}
expected_result = {
    "remaining_inventory": {"a": 3, "b": 1},
    "summary": {
        "count": 2,
        "total_cents": 1575,
        "by_category_cents": {"retail": 1250, "wholesale": 325},
    },
    "encoded_order_ids": "o\\|1|o\\\\2",
}

try:
    cli = importlib.import_module("order_tool.cli")
    payload = copy.deepcopy(sample_payload)
    original = copy.deepcopy(payload)
    result = cli.run_payload(payload)
    ok = result == expected_result and payload == original
    empty_payload = copy.deepcopy(sample_payload)
    empty_payload["orders"] = []
    empty_original = copy.deepcopy(empty_payload)
    try:
        cli.run_payload(empty_payload)
        ok = False
    except ValueError:
        pass
    ok = ok and empty_payload == empty_original
    add("payload_integration", ok)
except Exception as exc:
    add("payload_integration", False, type(exc).__name__)

try:
    with tempfile.TemporaryDirectory() as td:
        source = Path(td) / "input.json"
        source.write_text(json.dumps(sample_payload), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-m", "order_tool.cli", str(source)],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        parsed = json.loads(proc.stdout) if proc.returncode == 0 else None
        add("cli_stdout", proc.returncode == 0 and parsed == expected_result and proc.stdout.endswith("\n"))
except Exception as exc:
    add("cli_stdout", False, type(exc).__name__)

try:
    with tempfile.TemporaryDirectory() as td:
        source = Path(td) / "input.json"
        target = Path(td) / "out.json"
        source.write_text(json.dumps(sample_payload), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-m", "order_tool.cli", str(source), "--output", str(target)],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        parsed = json.loads(target.read_text(encoding="utf-8")) if target.exists() else None
        add("cli_output_file", proc.returncode == 0 and parsed == expected_result and not proc.stdout.strip())
except Exception as exc:
    add("cli_output_file", False, type(exc).__name__)

try:
    with tempfile.TemporaryDirectory() as td:
        source = Path(td) / "bad.json"
        target = Path(td) / "out.json"
        bad = copy.deepcopy(sample_payload)
        bad["reservations"] = [{"sku": "a", "quantity": 999}]
        source.write_text(json.dumps(bad), encoding="utf-8")
        target.write_text("sentinel\n", encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-m", "order_tool.cli", str(source), "--output", str(target)],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        add(
            "cli_error_atomicity",
            proc.returncode == 2
            and proc.stderr.startswith("error: ")
            and target.read_text(encoding="utf-8") == "sentinel\n",
        )
except Exception as exc:
    add("cli_error_atomicity", False, type(exc).__name__)

try:
    decision = json.loads((workspace / "storage_decision.json").read_text(encoding="utf-8"))
    options = json.loads((workspace / "storage_options.json").read_text(encoding="utf-8"))
    codes = decision.get("evidence_codes")
    selected = next(
        (item for item in options["options"] if item.get("backend") == decision.get("backend")),
        None,
    )
    required = set(options["required_constraints"])
    valid_codes = {
        item["code"]
        for item in (selected or {}).get("evidence", [])
        if isinstance(item, dict) and isinstance(item.get("code"), str)
    }
    add(
        "storage_decision",
        decision.get("backend") == "sqlite"
        and selected is not None
        and required.issubset(set(selected.get("supports") or []))
        and isinstance(codes, list)
        and {"stdlib", "offline", "transactions", "concurrent_readers"}.issubset(set(codes))
        and set(codes).issubset(valid_codes),
    )
except Exception as exc:
    add("storage_decision", False, type(exc).__name__)

try:
    report_text = (workspace / "BENCHMARK_REPORT.md").read_text(encoding="utf-8")
    marker = json.loads((workspace / "PBM_COMPLETE.json").read_text(encoding="utf-8"))
    headings = [
        "## Investigation",
        "## Changes",
        "## Verification",
        "## Storage decision",
    ]
    add(
        "completion_artifacts",
        all(item in report_text for item in headings)
        and marker == {"status": "complete", "verification": "passed"},
    )
except Exception as exc:
    add("completion_artifacts", False, type(exc).__name__)

passed = sum(1 for item in checks if item["ok"])
score = round(100 * passed / len(checks))
print(json.dumps({"pass": passed == len(checks), "score": score, "checks": checks}))
