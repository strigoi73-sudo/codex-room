from __future__ import annotations

import argparse
import json
import platform
import shlex
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_PATH = REPO_ROOT / "benchmarks" / "oub" / "v2" / "sample.json"
PLAN_PATH = REPO_ROOT / "benchmarks" / "oub" / "v2" / "phase3_plan.json"
RESULT_ROOT = REPO_ROOT / "data" / "oub-v2" / "phase3"

ENVIRONMENT_MARKERS = (
    "could not resolve host",
    "network is unreachable",
    "connection timed out",
    "temporary failure in name resolution",
    "no space left on device",
    "failed to install package",
    "failed to create virtualenv",
)


def _run(
    args: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 600,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(args)}\n{proc.stdout[-4000:]}"
        )
    return proc


def _tail(text: str, lines: int = 18) -> str:
    parts = text.rstrip().splitlines()
    return "\n".join(parts[-lines:])


def _looks_like_environment_failure(output: str) -> bool:
    lowered = output.lower()
    return any(marker in lowered for marker in ENVIRONMENT_MARKERS)


def _load_contract() -> tuple[dict, dict]:
    sample = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    if plan["upstream_revision"] != sample["upstream"]["revision"]:
        raise RuntimeError("phase3 plan upstream revision does not match frozen sample")

    sample_keys = {
        (
            t["cooperbench_repo"],
            int(t["task_id"]),
            tuple(int(x) for x in t["features"]),
            t["base_commit"],
        )
        for t in sample["tasks"]
    }
    plan_keys = {
        (
            t["cooperbench_repo"],
            int(t["task_id"]),
            tuple(int(x) for x in t["features"]),
            t["base_commit"],
        )
        for t in plan["tasks"]
    }
    if sample_keys != plan_keys:
        raise RuntimeError("phase3 plan task identities do not match frozen sample")
    return sample, plan


def _verify_source_assets(cooperbench: Path, plan: dict) -> list[dict]:
    head = _run(
        ["git", "-C", str(cooperbench), "rev-parse", "HEAD"], check=True
    ).stdout.strip()
    if head != plan["upstream_revision"]:
        raise RuntimeError(
            f"CooperBench checkout mismatch: expected {plan['upstream_revision']}, got {head}"
        )

    verified: list[dict] = []
    for task in plan["tasks"]:
        for rel, expected in task["asset_git_blobs"].items():
            path = cooperbench / rel
            if not path.is_file():
                raise RuntimeError(f"missing frozen upstream asset: {rel}")
            actual = _run(["git", "hash-object", str(path)], check=True).stdout.strip()
            if actual != expected:
                raise RuntimeError(
                    f"asset blob mismatch for {rel}: expected {expected}, got {actual}"
                )
            verified.append({"path": rel, "git_blob": actual})
    return verified


def _docker_run(
    task_dir: Path,
    image: str,
    feature: int,
    *,
    combined: bool,
) -> subprocess.CompletedProcess[str]:
    test_rel = f"feature{feature}/tests.patch"
    runner_args = ["bash", "/tmp/runner.sh", test_rel]
    if combined:
        runner_args.append("combined.patch")

    shell = (
        "cp /patches/runner.sh /tmp/runner.sh && "
        "chmod +x /tmp/runner.sh && "
        + " ".join(shlex.quote(x) for x in runner_args)
    )
    mount = f"type=bind,source={task_dir.resolve()},target=/patches,readonly"
    return _run(
        [
            "docker",
            "run",
            "--rm",
            "--mount",
            mount,
            "--entrypoint",
            "bash",
            image,
            "-lc",
            shell,
        ],
        timeout=1200,
    )


def _base_failure_is_grading_signal(output: str) -> bool:
    lowered = output.lower()
    benchmark_defect_markers = (
        "test patch not found",
        "failed to apply test patch",
        "repository state may not match expected base commit",
        "no test was executed",
        "must be run from the typst repository root",
    )
    return not any(marker in lowered for marker in benchmark_defect_markers)


def _validate_task(cooperbench: Path, task: dict) -> dict:
    image = task["image"]
    task_dir = cooperbench / task["task_path"]

    pull = _run(["docker", "pull", image], timeout=1200)
    if pull.returncode != 0:
        return {
            "sample_id": task["sample_id"],
            "image": image,
            "status": "ENVIRONMENT_FAILURE",
            "note": "docker pull failed",
            "log_tail": _tail(pull.stdout),
        }

    base_probe = _run(
        [
            "docker",
            "run",
            "--rm",
            "--entrypoint",
            "git",
            image,
            "-C",
            "/workspace/repo",
            "rev-parse",
            "HEAD",
        ],
        timeout=120,
    )
    image_base_commit = (
        base_probe.stdout.strip().splitlines()[-1]
        if base_probe.returncode == 0 and base_probe.stdout.strip()
        else None
    )
    if base_probe.returncode != 0 or image_base_commit != task["base_commit"]:
        return {
            "sample_id": task["sample_id"],
            "image": image,
            "status": "ENVIRONMENT_FAILURE",
            "note": (
                "task image base commit mismatch: "
                f"expected {task['base_commit']}, got {image_base_commit}"
            ),
            "log_tail": _tail(base_probe.stdout),
        }

    image_probe = _run(
        [
            "docker",
            "image",
            "inspect",
            "--format",
            '{{.Id}}|{{join .RepoDigests ","}}',
            image,
        ],
        timeout=60,
    )
    image_identity = image_probe.stdout.strip() if image_probe.returncode == 0 else None

    checks = []
    task_status = "PASS"
    for feature in task["features"]:
        base = _docker_run(task_dir, image, int(feature), combined=False)
        combined = _docker_run(task_dir, image, int(feature), combined=True)

        base_ok = (
            base.returncode != 0
            and _base_failure_is_grading_signal(base.stdout)
            and not _looks_like_environment_failure(base.stdout)
        )
        combined_ok = combined.returncode == 0

        if (
            (base.returncode != 0 and _looks_like_environment_failure(base.stdout))
            or (
                combined.returncode != 0
                and _looks_like_environment_failure(combined.stdout)
            )
        ):
            task_status = "ENVIRONMENT_FAILURE"
        elif not base_ok or not combined_ok:
            if task_status != "ENVIRONMENT_FAILURE":
                task_status = "FAIL"

        checks.append(
            {
                "feature": int(feature),
                "base_rc": base.returncode,
                "base_rejects_feature_tests": base_ok,
                "base_log_tail": _tail(base.stdout),
                "combined_rc": combined.returncode,
                "combined_oracle_passes": combined_ok,
                "combined_log_tail": _tail(combined.stdout),
            }
        )
        print(
            f"  feature {feature}: "
            f"base={'PASS(rejected)' if base_ok else 'FAIL'}; "
            f"combined={'PASS' if combined_ok else 'FAIL'}",
            flush=True,
        )

    return {
        "sample_id": task["sample_id"],
        "image": image,
        "image_identity": image_identity,
        "image_base_commit": image_base_commit,
        "status": task_status,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="I-028 OUB v2 Phase-3 deterministic CooperBench validator"
    )
    parser.add_argument(
        "--describe",
        action="store_true",
        help="print the frozen validation plan without network or Docker work",
    )
    args = parser.parse_args()

    sample, plan = _load_contract()
    if args.describe:
        print(json.dumps({"sample": sample, "phase3_plan": plan}, indent=2))
        return 0

    git_check = _run(["git", "--version"])
    if git_check.returncode != 0:
        print("ERROR: git is required for Phase 3.", file=sys.stderr)
        return 3

    docker_check = _run(
        ["docker", "info", "--format", "{{.ServerVersion}}"], timeout=30
    )
    if docker_check.returncode != 0:
        print(
            "ERROR: a working Docker daemon is required for exact CooperBench "
            "task-image validation."
        )
        print(_tail(docker_check.stdout))
        print(
            "No system changes were made. This is an environment prerequisite, "
            "not a task failure."
        )
        return 3
    docker_version = docker_check.stdout.strip()

    started = datetime.now(timezone.utc)
    with tempfile.TemporaryDirectory(prefix="oub-v2-phase3-") as tmp:
        tmp_root = Path(tmp)
        cb = tmp_root / "CooperBench"
        _run(["git", "init", str(cb)], check=True)
        _run(
            ["git", "-C", str(cb), "remote", "add", "origin", plan["upstream_url"]],
            check=True,
        )
        _run(
            [
                "git",
                "-C",
                str(cb),
                "fetch",
                "--depth",
                "1",
                "origin",
                plan["upstream_revision"],
            ],
            timeout=1200,
            check=True,
        )
        _run(
            ["git", "-C", str(cb), "checkout", "--detach", "FETCH_HEAD"],
            check=True,
        )
        assets = _verify_source_assets(cb, plan)
        print(
            f"Frozen upstream assets: PASS "
            f"({len(assets)} blob identities verified)"
        )

        task_results = []
        for task in plan["tasks"]:
            print(
                f"\n{task['sample_id']}: "
                f"{task['cooperbench_repo']}/task{task['task_id']} "
                f"features {task['features']}"
            )
            task_results.append(_validate_task(cb, task))

    finished = datetime.now(timezone.utc)
    if any(t["status"] == "ENVIRONMENT_FAILURE" for t in task_results):
        overall = "ENVIRONMENT_FAILURE"
    elif all(t["status"] == "PASS" for t in task_results):
        overall = "PASS"
    else:
        overall = "FAIL"

    payload = {
        "schema": "oub-v2-phase3-validation-v1",
        "overall": overall,
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "host": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "docker_server": docker_version,
        },
        "phase1_contract_commit": sample["phase1_contract_commit"],
        "upstream_revision": plan["upstream_revision"],
        "verified_assets": assets,
        "tasks": task_results,
    }
    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    stamp = finished.strftime("%Y%m%dT%H%M%SZ")
    result_path = RESULT_ROOT / f"phase3-validation-{stamp}.json"
    result_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"\nPhase 3 result: {overall}")
    print(f"Result file: {result_path}")
    if overall == "ENVIRONMENT_FAILURE":
        print(
            "The frozen sample has not failed. Resolve or classify the environment "
            "prerequisite before any replacement decision."
        )
        return 3
    if overall != "PASS":
        print(
            "A failed selected task is not automatically replaceable; classify the "
            "failure under the frozen Phase-1 contract first."
        )
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
