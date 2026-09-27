from __future__ import annotations

import json
import os
import platform
import re
import shutil
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
    "failed to download",
    "failed to get",
    "spurious network error",
    "connection reset",
    "connection refused",
)


def run(
    args: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 1800,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )


def tail(text: str, lines: int = 20) -> str:
    return "\n".join(text.rstrip().splitlines()[-lines:])


def environment_failure(output: str) -> bool:
    lowered = output.lower()
    return any(marker in lowered for marker in ENVIRONMENT_MARKERS)


def load_contract() -> tuple[dict, dict]:
    sample = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    if plan["upstream_revision"] != sample["upstream"]["revision"]:
        raise RuntimeError("Phase-3 plan does not match the frozen CooperBench revision")

    sample_keys = {
        (
            t["sample_id"],
            t["cooperbench_repo"],
            int(t["task_id"]),
            tuple(int(x) for x in t["features"]),
            t["base_commit"],
        )
        for t in sample["tasks"]
    }
    plan_keys = {
        (
            t["sample_id"],
            t["cooperbench_repo"],
            int(t["task_id"]),
            tuple(int(x) for x in t["features"]),
            t["base_commit"],
        )
        for t in plan["tasks"]
    }
    if sample_keys != plan_keys:
        raise RuntimeError("Phase-3 plan task identities do not match the frozen sample")
    return sample, plan


def materialize_exact_repo(url: str, commit: str, destination: Path) -> None:
    init = run(["git", "init", str(destination)])
    if init.returncode != 0:
        raise RuntimeError(init.stdout)
    remote = run(["git", "-C", str(destination), "remote", "add", "origin", url])
    if remote.returncode != 0:
        raise RuntimeError(remote.stdout)
    fetch = run(
        ["git", "-C", str(destination), "fetch", "--depth", "1", "origin", commit],
        timeout=1200,
    )
    if fetch.returncode != 0:
        raise RuntimeError(fetch.stdout)
    checkout = run(
        ["git", "-C", str(destination), "checkout", "--detach", "FETCH_HEAD"]
    )
    if checkout.returncode != 0:
        raise RuntimeError(checkout.stdout)
    actual = run(["git", "-C", str(destination), "rev-parse", "HEAD"])
    if actual.returncode != 0 or actual.stdout.strip() != commit:
        raise RuntimeError(
            f"exact-commit mismatch: expected {commit}, got {actual.stdout.strip()}"
        )


def verify_assets(cooperbench: Path, plan: dict) -> list[dict]:
    actual_head = run(["git", "-C", str(cooperbench), "rev-parse", "HEAD"])
    if (
        actual_head.returncode != 0
        or actual_head.stdout.strip() != plan["upstream_revision"]
    ):
        raise RuntimeError("Frozen CooperBench checkout identity mismatch")

    verified: list[dict] = []
    for task in plan["tasks"]:
        for rel, expected in task["asset_git_blobs"].items():
            path = cooperbench / rel
            if not path.is_file():
                raise RuntimeError(f"missing frozen asset: {rel}")
            result = run(["git", "hash-object", str(path)])
            actual = result.stdout.strip()
            if result.returncode != 0 or actual != expected:
                raise RuntimeError(
                    f"asset mismatch for {rel}: expected {expected}, got {actual}"
                )
            verified.append({"path": rel, "git_blob": actual})
    return verified


def reset_repo(repo: Path, base_commit: str) -> None:
    reset = run(["git", "reset", "--hard", base_commit], cwd=repo)
    if reset.returncode != 0:
        raise RuntimeError(reset.stdout)
    clean = run(["git", "clean", "-fd", "-e", ".venv/", "-e", "target/"], cwd=repo)
    if clean.returncode != 0:
        raise RuntimeError(clean.stdout)


def apply_patch(repo: Path, patch: Path) -> None:
    check = run(["git", "apply", "--check", str(patch)], cwd=repo)
    if check.returncode != 0:
        raise RuntimeError(
            f"patch does not apply: {patch}\n{tail(check.stdout, 30)}"
        )
    applied = run(["git", "apply", str(patch)], cwd=repo)
    if applied.returncode != 0:
        raise RuntimeError(f"failed to apply {patch}\n{tail(applied.stdout, 30)}")


def venv_python(repo: Path) -> Path:
    return repo / ".venv" / "bin" / "python"


def setup_python_task(repo: Path, task: dict) -> dict[str, str]:
    version = task["native_runtime"]["python"]
    create = run(["uv", "venv", "--python", version, ".venv"], cwd=repo, timeout=600)
    if create.returncode != 0:
        raise RuntimeError(f"uv venv failed\n{tail(create.stdout, 40)}")

    python = venv_python(repo)
    if task["sample_id"] == "o2-1":
        deps = run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(python),
                "-r",
                "pyproject.toml",
            ],
            cwd=repo,
            timeout=1200,
        )
        if deps.returncode != 0:
            editable = run(
                ["uv", "pip", "install", "--python", str(python), "-e", "."],
                cwd=repo,
                timeout=1200,
            )
            if editable.returncode != 0:
                raise RuntimeError(
                    "LlamaIndex dependency install failed\n"
                    + tail(deps.stdout + "\n" + editable.stdout, 60)
                )
        extras = run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(python),
                "pytest",
                "pytest-xdist",
                "pytest-asyncio",
                "openai",
            ],
            cwd=repo,
            timeout=1200,
        )
    else:
        extras = run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(python),
                "-e",
                ".[test]",
            ],
            cwd=repo,
            timeout=1200,
        )
        if extras.returncode != 0:
            fallback = run(
                ["uv", "pip", "install", "--python", str(python), "-e", "."],
                cwd=repo,
                timeout=1200,
            )
            if fallback.returncode != 0:
                raise RuntimeError(
                    "dirty-equals package install failed\n"
                    + tail(extras.stdout + "\n" + fallback.stdout, 60)
                )
        extras = run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(python),
                "pytest",
                "pytest-xdist",
                "pytest-mock",
            ],
            cwd=repo,
            timeout=1200,
        )

    if extras.returncode != 0:
        raise RuntimeError(f"test dependency install failed\n{tail(extras.stdout, 60)}")

    env = os.environ.copy()
    env["PATH"] = f"{python.parent}:{env.get('PATH', '')}"
    return env


def run_python_tests(repo: Path, task: dict, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    python = str(venv_python(repo))
    command = list(task["native_runtime"]["test_command"])
    command[0] = python
    return run(command, cwd=repo, env=env, timeout=1200)


def typst_blocks(test_patch: Path) -> list[str]:
    block_re = re.compile(r"^\+--- ([A-Za-z0-9_-]+) ---$")
    blocks: set[str] = set()
    for line in test_patch.read_text(encoding="utf-8").splitlines():
        match = block_re.match(line)
        if match:
            blocks.add(match.group(1))
    return sorted(blocks)


def run_typst_tests(repo: Path, task: dict, test_patch: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["RUSTUP_TOOLCHAIN"] = task["native_runtime"]["toolchain"]

    build = run(
        ["cargo", "build", "--package", "typst", "--package", "typst-cli"],
        cwd=repo,
        env=env,
        timeout=1800,
    )
    if build.returncode != 0:
        return build

    blocks = typst_blocks(test_patch)
    outputs: list[str] = [build.stdout]
    returncode = 0
    if not blocks:
        result = run(
            ["cargo", "test", "-p", "typst-tests"],
            cwd=repo,
            env=env,
            timeout=1800,
        )
        outputs.append(result.stdout)
        returncode = result.returncode
    else:
        for block in blocks:
            result = run(
                ["cargo", "test", "-p", "typst-tests", "--", block],
                cwd=repo,
                env=env,
                timeout=1800,
            )
            outputs.append(f"\n=== block {block} ===\n{result.stdout}")
            if result.returncode != 0:
                returncode = result.returncode
    return subprocess.CompletedProcess(
        args=["cargo", "test", "-p", "typst-tests"],
        returncode=returncode,
        stdout="".join(outputs),
        stderr=None,
    )


def test_once(
    repo: Path,
    task: dict,
    task_assets: Path,
    feature: int,
    *,
    combined: bool,
    python_env: dict[str, str] | None,
) -> subprocess.CompletedProcess[str]:
    reset_repo(repo, task["base_commit"])
    if combined:
        apply_patch(repo, task_assets / "combined.patch")
    test_patch = task_assets / f"feature{feature}" / "tests.patch"
    apply_patch(repo, test_patch)

    if task["native_runtime"]["kind"] == "python":
        assert python_env is not None
        return run_python_tests(repo, task, python_env)
    return run_typst_tests(repo, task, test_patch)


def classify_base(result: subprocess.CompletedProcess[str]) -> bool:
    return result.returncode != 0 and not environment_failure(result.stdout)


def validate_task(work: Path, cooperbench: Path, task: dict) -> dict:
    repo = work / task["sample_id"] / "repo"
    repo.parent.mkdir(parents=True, exist_ok=True)
    materialize_exact_repo(task["project_url"], task["base_commit"], repo)
    task_assets = cooperbench / task["task_path"]

    python_env: dict[str, str] | None = None
    if task["native_runtime"]["kind"] == "python":
        python_env = setup_python_task(repo, task)

    checks: list[dict] = []
    status = "PASS"
    for feature in task["features"]:
        print(f"  feature {feature}: base check", flush=True)
        base = test_once(
            repo,
            task,
            task_assets,
            int(feature),
            combined=False,
            python_env=python_env,
        )
        base_ok = classify_base(base)

        print(f"  feature {feature}: combined oracle check", flush=True)
        combined = test_once(
            repo,
            task,
            task_assets,
            int(feature),
            combined=True,
            python_env=python_env,
        )
        combined_ok = combined.returncode == 0

        if environment_failure(base.stdout) or environment_failure(combined.stdout):
            status = "ENVIRONMENT_FAILURE"
        elif not base_ok or not combined_ok:
            if status != "ENVIRONMENT_FAILURE":
                status = "FAIL"

        print(
            f"  feature {feature}: "
            f"base={'PASS(rejected)' if base_ok else 'FAIL'}; "
            f"combined={'PASS' if combined_ok else 'FAIL'}",
            flush=True,
        )
        checks.append(
            {
                "feature": int(feature),
                "base_rc": base.returncode,
                "base_rejects_feature_tests": base_ok,
                "base_log_tail": tail(base.stdout),
                "combined_rc": combined.returncode,
                "combined_oracle_passes": combined_ok,
                "combined_log_tail": tail(combined.stdout),
            }
        )

    reset_repo(repo, task["base_commit"])
    return {
        "sample_id": task["sample_id"],
        "project_url": task["project_url"],
        "base_commit": task["base_commit"],
        "runtime": task["native_runtime"],
        "status": status,
        "checks": checks,
    }


def main() -> int:
    if platform.system() != "Linux":
        print("ERROR: native Phase-3 validation must run under Linux/WSL.")
        return 3

    required = ["git", "uv"]
    missing = [name for name in required if shutil.which(name) is None]
    if missing:
        print("ERROR: missing native prerequisites: " + ", ".join(missing))
        return 3

    sample, plan = load_contract()
    if any(
        task["native_runtime"]["kind"] == "rust" for task in plan["tasks"]
    ):
        rust_missing = [name for name in ("cargo", "rustc") if shutil.which(name) is None]
        if rust_missing:
            print("ERROR: missing Rust prerequisites: " + ", ".join(rust_missing))
            return 3

    started = datetime.now(timezone.utc)
    with tempfile.TemporaryDirectory(prefix="oub-v2-phase3-native-") as tmp:
        root = Path(tmp)
        cooperbench = root / "CooperBench"
        try:
            materialize_exact_repo(
                plan["upstream_url"], plan["upstream_revision"], cooperbench
            )
            assets = verify_assets(cooperbench, plan)
        except (RuntimeError, subprocess.TimeoutExpired, OSError) as exc:
            print(f"ERROR: frozen CooperBench source validation failed: {exc}")
            return 3

        print(f"Frozen upstream assets: PASS ({len(assets)} blob identities verified)")
        task_results: list[dict] = []
        for task in plan["tasks"]:
            print(
                f"\n{task['sample_id']}: "
                f"{task['cooperbench_repo']}/task{task['task_id']} "
                f"features {task['features']}",
                flush=True,
            )
            try:
                task_results.append(validate_task(root, cooperbench, task))
            except (RuntimeError, subprocess.TimeoutExpired, OSError) as exc:
                task_results.append(
                    {
                        "sample_id": task["sample_id"],
                        "status": "ENVIRONMENT_FAILURE",
                        "note": f"{type(exc).__name__}: {exc}",
                    }
                )

    finished = datetime.now(timezone.utc)
    if any(t["status"] == "ENVIRONMENT_FAILURE" for t in task_results):
        overall = "ENVIRONMENT_FAILURE"
    elif all(t["status"] == "PASS" for t in task_results):
        overall = "PASS"
    else:
        overall = "FAIL"

    payload = {
        "schema": "oub-v2-phase3-validation-v1",
        "backend": "wsl-native",
        "overall": overall,
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "host": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "uv": run(["uv", "--version"]).stdout.strip(),
            "rustc": (
                run(["rustc", "--version"]).stdout.strip()
                if shutil.which("rustc")
                else None
            ),
        },
        "phase1_contract_commit": sample["phase1_contract_commit"],
        "upstream_revision": plan["upstream_revision"],
        "verified_assets": assets,
        "tasks": task_results,
    }

    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    stamp = finished.strftime("%Y%m%dT%H%M%SZ")
    result_path = RESULT_ROOT / f"phase3-validation-{stamp}.json"
    result_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"\nPhase 3 result: {overall}")
    print(f"Result file: {result_path}")
    if overall == "ENVIRONMENT_FAILURE":
        print("The frozen sample has not failed; the native environment did.")
        return 3
    if overall != "PASS":
        print("A selected task failed the deterministic gate; classify before replacement.")
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
