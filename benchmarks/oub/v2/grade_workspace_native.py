from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
V2_ROOT = REPO_ROOT / "benchmarks" / "oub" / "v2"
MANIFEST_PATH = V2_ROOT / "manifest.json"


class GradeError(RuntimeError):
    pass


def run(
    args: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 1800,
    text: bool = True,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
        text=text,
    )


def tail(value: str, lines: int = 30) -> str:
    return "\n".join(value.rstrip().splitlines()[-lines:])


def load_manifest() -> dict[str, Any]:
    value = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if value.get("schema") != "oub-v2-manifest-v1":
        raise GradeError("unexpected OUB v2 manifest schema")
    return value


def task_by_id(manifest: dict[str, Any], task_id: str) -> dict[str, Any]:
    for task in manifest.get("tasks") or []:
        if isinstance(task, dict) and task.get("id") == task_id:
            return task
    raise GradeError(f"unknown OUB v2 task: {task_id}")


def git_output(workspace: Path, *args: str) -> str:
    result = run(["git", "-C", str(workspace), *args])
    if result.returncode != 0:
        raise GradeError(
            f"git {' '.join(args)} failed in {workspace}: {tail(result.stdout)}"
        )
    return result.stdout


def exact_head(workspace: Path) -> str:
    return git_output(workspace, "rev-parse", "HEAD").strip()


def changed_paths(workspace: Path, base_commit: str) -> list[str]:
    tracked = [
        line.strip()
        for line in git_output(
            workspace, "diff", "--name-only", base_commit, "--"
        ).splitlines()
        if line.strip()
    ]
    raw = run(
        [
            "git",
            "-C",
            str(workspace),
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        text=False,
    )
    if raw.returncode != 0:
        raise GradeError("unable to enumerate candidate untracked files")
    untracked = [
        item.decode("utf-8", errors="surrogateescape")
        for item in raw.stdout.split(b"\0")
        if item
    ]
    return sorted(set(tracked + untracked))


def candidate_patch(workspace: Path, base_commit: str) -> bytes:
    result = run(
        ["git", "-C", str(workspace), "diff", "--binary", base_commit, "--"],
        text=False,
    )
    if result.returncode != 0:
        raise GradeError("unable to capture candidate diff")
    return bytes(result.stdout)


def untracked_paths(workspace: Path) -> list[str]:
    result = run(
        [
            "git",
            "-C",
            str(workspace),
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        text=False,
    )
    if result.returncode != 0:
        raise GradeError("unable to enumerate candidate untracked files")
    return [
        item.decode("utf-8", errors="surrogateescape")
        for item in result.stdout.split(b"\0")
        if item
    ]


def clone_base(source: Path, destination: Path, base_commit: str) -> None:
    clone = run(
        ["git", "clone", "--no-hardlinks", "--quiet", str(source), str(destination)],
        timeout=1200,
    )
    if clone.returncode != 0:
        raise GradeError(f"grading clone failed: {tail(clone.stdout)}")
    checkout = run(
        ["git", "checkout", "--detach", base_commit],
        cwd=destination,
    )
    if checkout.returncode != 0:
        raise GradeError(f"base checkout failed: {tail(checkout.stdout)}")
    if exact_head(destination) != base_commit:
        raise GradeError("grading clone did not resolve the frozen base commit")


def reset_repo(repo: Path, base_commit: str) -> None:
    reset = run(["git", "reset", "--hard", base_commit], cwd=repo)
    if reset.returncode != 0:
        raise GradeError(tail(reset.stdout))
    clean = run(
        ["git", "clean", "-fd", "-e", ".venv/", "-e", "target/"],
        cwd=repo,
    )
    if clean.returncode != 0:
        raise GradeError(tail(clean.stdout))


def apply_patch(repo: Path, patch: Path) -> tuple[bool, str]:
    check = run(["git", "apply", "--check", str(patch)], cwd=repo)
    if check.returncode != 0:
        return False, tail(check.stdout)
    applied = run(["git", "apply", str(patch)], cwd=repo)
    if applied.returncode != 0:
        return False, tail(applied.stdout)
    return True, ""


def apply_candidate(
    repo: Path,
    source: Path,
    patch_bytes: bytes,
    untracked: list[str],
) -> None:
    if patch_bytes:
        patch_path = repo.parent / "candidate.patch"
        patch_path.write_bytes(patch_bytes)
        ok, detail = apply_patch(repo, patch_path)
        if not ok:
            raise GradeError(f"candidate diff could not be replayed: {detail}")

    for rel in untracked:
        if rel in {"BENCHMARK.md", "OUB_COMPLETE.json"}:
            continue
        src = source / rel
        dst = repo / rel
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        elif src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def venv_python(repo: Path) -> Path:
    return repo / ".venv" / "bin" / "python"


def setup_python_task(repo: Path, task: dict[str, Any]) -> dict[str, str]:
    version = str(task["native_runtime"]["python"])
    create = run(["uv", "venv", "--python", version, ".venv"], cwd=repo, timeout=600)
    if create.returncode != 0:
        raise GradeError(f"uv venv failed: {tail(create.stdout)}")
    python = venv_python(repo)

    if task["id"] == "o2-1":
        deps = run(
            ["uv", "pip", "install", "--python", str(python), "-r", "pyproject.toml"],
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
                raise GradeError(
                    "LlamaIndex dependency install failed: "
                    + tail(deps.stdout + "\n" + editable.stdout, 50)
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
        install = run(
            ["uv", "pip", "install", "--python", str(python), "-e", ".[test]"],
            cwd=repo,
            timeout=1200,
        )
        if install.returncode != 0:
            fallback = run(
                ["uv", "pip", "install", "--python", str(python), "-e", "."],
                cwd=repo,
                timeout=1200,
            )
            if fallback.returncode != 0:
                raise GradeError(
                    "dirty-equals dependency install failed: "
                    + tail(install.stdout + "\n" + fallback.stdout, 50)
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
        raise GradeError(f"test dependency install failed: {tail(extras.stdout, 50)}")

    env = os.environ.copy()
    env["PATH"] = f"{python.parent}:{env.get('PATH', '')}"
    return env


def run_python_tests(
    repo: Path,
    task: dict[str, Any],
    env: dict[str, str],
) -> subprocess.CompletedProcess:
    command = list(task["native_runtime"]["test_command"])
    command[0] = str(venv_python(repo))
    return run(command, cwd=repo, env=env, timeout=1200)


def typst_blocks(test_patch: Path) -> list[str]:
    pattern = re.compile(r"^\+--- ([A-Za-z0-9_-]+) ---$")
    blocks: set[str] = set()
    for line in test_patch.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            blocks.add(match.group(1))
    return sorted(blocks)


def run_typst_tests(
    repo: Path,
    task: dict[str, Any],
    test_patch: Path,
) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["RUSTUP_TOOLCHAIN"] = str(task["native_runtime"]["toolchain"])

    build = run(
        ["cargo", "build", "--package", "typst", "--package", "typst-cli"],
        cwd=repo,
        env=env,
        timeout=1800,
    )
    if build.returncode != 0:
        return build

    outputs = [build.stdout]
    returncode = 0
    blocks = typst_blocks(test_patch)
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


def grade(workspace: Path, task_id: str) -> dict[str, Any]:
    manifest = load_manifest()
    task = task_by_id(manifest, task_id)
    base_commit = str(task["base_commit"])

    if not workspace.is_dir() or not (workspace / ".git").exists():
        raise GradeError("workspace is not a Git working tree")
    source_head = exact_head(workspace)
    ancestor = run(
        ["git", "-C", str(workspace), "merge-base", "--is-ancestor", base_commit, "HEAD"]
    )
    if ancestor.returncode not in {0, 1}:
        raise GradeError("unable to establish candidate lineage")
    if ancestor.returncode == 1 and source_head != base_commit:
        raise GradeError(
            "candidate HEAD no longer descends from the frozen base commit"
        )

    patch_bytes = candidate_patch(workspace, base_commit)
    untracked = untracked_paths(workspace)
    changes = changed_paths(workspace, base_commit)

    home = Path.home()
    os.environ["PATH"] = (
        f"{home / '.local' / 'bin'}:{home / '.cargo' / 'bin'}:"
        + os.environ.get("PATH", "")
    )

    with tempfile.TemporaryDirectory(prefix=f"oub-v2-grade-{task_id}-") as td:
        root = Path(td)
        repo = root / "candidate"
        clone_base(workspace, repo, base_commit)

        python_env: dict[str, str] | None = None
        if task["native_runtime"]["kind"] == "python":
            python_env = setup_python_task(repo, task)

        feature_results: list[dict[str, Any]] = []
        for feature in task["features"]:
            reset_repo(repo, base_commit)
            apply_candidate(repo, workspace, patch_bytes, untracked)
            test_patch = V2_ROOT / str(feature["tests_file"])
            ok, patch_detail = apply_patch(repo, test_patch)
            if not ok:
                feature_results.append(
                    {
                        "feature": int(feature["id"]),
                        "pass": False,
                        "returncode": None,
                        "failure_kind": "official_test_patch_apply_failed",
                        "log_tail": patch_detail,
                    }
                )
                continue

            if task["native_runtime"]["kind"] == "python":
                assert python_env is not None
                result = run_python_tests(repo, task, python_env)
            else:
                result = run_typst_tests(repo, task, test_patch)

            feature_results.append(
                {
                    "feature": int(feature["id"]),
                    "pass": result.returncode == 0,
                    "returncode": int(result.returncode),
                    "failure_kind": None if result.returncode == 0 else "official_tests_failed",
                    "log_tail": tail(result.stdout, 40),
                }
            )

    passed = sum(1 for item in feature_results if item["pass"])
    return {
        "schema": "oub-v2-grade-v1",
        "task_id": task_id,
        "base_commit": base_commit,
        "candidate_head": source_head,
        "changed_paths": changes,
        "passed_features": passed,
        "total_features": len(feature_results),
        "pass": passed == len(feature_results),
        "features": feature_results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OUB v2 isolated WSL workspace grader")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--workspace", required=True)
    args = parser.parse_args(argv)

    try:
        result = grade(Path(args.workspace), args.task_id)
    except (GradeError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(
            json.dumps(
                {
                    "schema": "oub-v2-grade-v1",
                    "task_id": args.task_id,
                    "infrastructure_error": str(exc),
                    "pass": False,
                },
                sort_keys=True,
            )
        )
        return 3

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
