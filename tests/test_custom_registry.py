from __future__ import annotations

import json
from pathlib import Path

import pytest

from codex_room.capabilities import (
    CapabilityUsageError,
    invoke_capability,
    inspect_capability,
    list_capabilities,
    main,
)
from codex_room.custom_capabilities import DRAFTS_PATH
from codex_room.custom_capability_registration import (
    publish_verified_custom_capability,
    verify_custom_capability_draft,
)
from codex_room.orchestrator import RoomRuntime
from codex_room.custom_registry import (
    CustomCapabilityRegistryError,
    bind_custom_registration,
    invoke_bound_custom_capability,
    load_room_custom_capabilities,
    resolve_room_capability_context,
)


def _manifest(capability_id: str = "count_lines", *, version: str = "1") -> dict:
    return {
        "schema_version": 1,
        "id": capability_id,
        "version": version,
        "description": "Count lines in explicit input text.",
        "scope": "lineage",
        "runtime": {
            "kind": "python",
            "entrypoint": "capability.py",
            "protocol": "stdio-json-v1",
        },
        "input_schema": {
            "type": "object",
            "required": ["text"],
            "properties": {"text": {"type": "string"}},
        },
        "output_schema": {
            "type": "object",
            "required": ["ok", "count"],
            "properties": {
                "ok": {"type": "boolean"},
                "count": {"type": "integer"},
            },
        },
        "durable_result_fields": ["count"],
        "permissions": {
            "workspace_read": False,
            "workspace_write": False,
            "network": False,
            "external_process": False,
        },
        "side_effects": "none",
    }


def _code(delta: int = 0) -> str:
    return (
        "import json, sys\n"
        "request = json.load(sys.stdin)\n"
        f"count = len(request['text'].splitlines()) + {delta}\n"
        "print(json.dumps({'ok': True, 'count': count}, sort_keys=True))\n"
    )


def _make_room(tmp_path: Path, room_id: str = "room_custom") -> tuple[Path, Path]:
    data_root = tmp_path / "data"
    workspace = data_root / "rooms" / room_id / "shared"
    workspace.mkdir(parents=True)
    return data_root, workspace


def _write_draft(
    workspace: Path,
    *,
    capability_id: str = "count_lines",
    version: str = "1",
    delta: int = 0,
) -> Path:
    root = workspace.joinpath(*DRAFTS_PATH.parts, capability_id)
    root.mkdir(parents=True, exist_ok=True)
    (root / "manifest.json").write_text(
        json.dumps(
            _manifest(capability_id, version=version),
            sort_keys=True,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    (root / "capability.py").write_text(_code(delta), encoding="utf-8")
    return root


def _cases(delta: int = 0) -> list[dict]:
    return [
        {
            "name": "basic",
            "input": {"text": "one\ntwo\n"},
            "expected_output": {"ok": True, "count": 2 + delta},
        }
    ]


def _publish_and_bind(
    data_root: Path,
    workspace: Path,
    *,
    room_id: str = "room_custom",
    capability_id: str = "count_lines",
    version: str = "1",
    delta: int = 0,
):
    _write_draft(
        workspace,
        capability_id=capability_id,
        version=version,
        delta=delta,
    )
    receipt = verify_custom_capability_draft(
        workspace,
        capability_id,
        _cases(delta),
    )
    registration = publish_verified_custom_capability(
        workspace,
        data_root,
        room_id,
        capability_id,
        receipt,
    )
    binding = bind_custom_registration(
        data_root,
        room_id,
        registration.registration_sha256,
        reserved_capability_ids={
            "assert_file",
            "compare_files",
            "find_files",
            "search_text",
        },
    )
    return receipt, registration, binding


def test_room_context_resolves_only_canonical_workspace_layout(tmp_path: Path) -> None:
    data_root, workspace = _make_room(tmp_path)

    context = resolve_room_capability_context(workspace)

    assert context is not None
    assert context.workspace == workspace.resolve()
    assert context.data_root == data_root.resolve()
    assert context.room_id == "room_custom"
    assert resolve_room_capability_context(tmp_path) is None


def test_binding_resolves_exact_verified_registration(tmp_path: Path) -> None:
    data_root, workspace = _make_room(tmp_path)
    receipt, registration, binding = _publish_and_bind(data_root, workspace)

    loaded = load_room_custom_capabilities(
        data_root,
        "room_custom",
        reserved_capability_ids={"assert_file"},
    )

    assert loaded["count_lines"].binding_sha256 == binding.binding_sha256
    assert loaded["count_lines"].registration == registration
    assert loaded["count_lines"].receipt == receipt
    assert loaded["count_lines"].package.package_sha256 == registration.package_sha256


def test_binding_is_single_assignment_but_same_exact_binding_is_idempotent(
    tmp_path: Path,
) -> None:
    data_root, workspace = _make_room(tmp_path)
    _, first, binding = _publish_and_bind(data_root, workspace)

    repeated = bind_custom_registration(
        data_root,
        "room_custom",
        first.registration_sha256,
    )
    assert repeated.binding_sha256 == binding.binding_sha256

    draft = workspace.joinpath(*DRAFTS_PATH.parts, "count_lines")
    (draft / "manifest.json").write_text(
        json.dumps(_manifest(version="2"), sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    (draft / "capability.py").write_text(_code(1), encoding="utf-8")
    receipt = verify_custom_capability_draft(workspace, "count_lines", _cases(1))
    second = publish_verified_custom_capability(
        workspace,
        data_root,
        "room_custom",
        "count_lines",
        receipt,
    )

    with pytest.raises(CustomCapabilityRegistryError, match="different Room binding"):
        bind_custom_registration(
            data_root,
            "room_custom",
            second.registration_sha256,
        )


def test_binding_rejects_core_id_collision(tmp_path: Path) -> None:
    data_root, workspace = _make_room(tmp_path)
    _write_draft(workspace, capability_id="assert_file")
    receipt = verify_custom_capability_draft(
        workspace,
        "assert_file",
        _cases(),
    )
    registration = publish_verified_custom_capability(
        workspace,
        data_root,
        "room_custom",
        "assert_file",
        receipt,
    )

    with pytest.raises(CustomCapabilityRegistryError, match="reserved CORE"):
        bind_custom_registration(
            data_root,
            "room_custom",
            registration.registration_sha256,
            reserved_capability_ids={"assert_file"},
        )


def test_custom_invocation_uses_immutable_published_bytes_not_mutable_draft(
    tmp_path: Path,
) -> None:
    data_root, workspace = _make_room(tmp_path)
    _, _, binding = _publish_and_bind(data_root, workspace)
    draft = workspace.joinpath(*DRAFTS_PATH.parts, "count_lines", "capability.py")
    draft.write_text(
        "import json\nprint(json.dumps({'ok': True, 'count': 999}))\n",
        encoding="utf-8",
    )
    context = resolve_room_capability_context(workspace)
    assert context is not None

    result = invoke_bound_custom_capability(
        context,
        binding,
        {"text": "one\ntwo\nthree\n"},
    )

    assert result["ok"] is True
    assert result["count"] == 3
    assert result["capability"] == "count_lines"
    assert result["capability_version"] == "1"
    assert result["implementation_sha256"] == binding.package.implementation_sha256
    assert result["package_sha256"] == binding.package.package_sha256
    assert result["registration_sha256"] == binding.registration.registration_sha256
    assert result["verification_sha256"] == binding.receipt.verification_sha256
    assert result["durable_result_fields"] == ["count"]


def test_registry_rejects_corrupt_published_package_before_invocation(tmp_path: Path) -> None:
    data_root, workspace = _make_room(tmp_path)
    _, registration, _ = _publish_and_bind(data_root, workspace)
    published = (
        data_root
        / "custom-capabilities"
        / "packages"
        / registration.package_sha256
        / "capability.py"
    )
    published.write_text("print('corrupt')", encoding="utf-8")

    with pytest.raises(CustomCapabilityRegistryError):
        load_room_custom_capabilities(data_root, "room_custom")


def test_dynamic_registry_lists_inspects_and_invokes_bound_custom_capability(
    tmp_path: Path,
) -> None:
    data_root, workspace = _make_room(tmp_path)
    _, registration, _ = _publish_and_bind(data_root, workspace)

    registry = list_capabilities(workspace)
    ids = [item["id"] for item in registry["capabilities"]]
    assert ids == [
        "assert_file",
        "compare_files",
        "count_lines",
        "find_files",
        "search_text",
    ]
    custom_summary = next(item for item in registry["capabilities"] if item["id"] == "count_lines")
    assert custom_summary["origin"] == "custom"
    assert custom_summary["scope"] == "lineage"
    assert custom_summary["registration_sha256"] == registration.registration_sha256

    inspected = inspect_capability("count_lines", workspace)["capability"]
    assert inspected["id"] == "count_lines"
    assert inspected["verification"]["status"] == "verified"
    assert inspected["verification"]["registration_sha256"] == registration.registration_sha256
    assert inspected["permission_enforcement"]["per_capability_enforcement"] is False

    result = invoke_capability(
        workspace,
        "count_lines",
        {"text": "alpha\nbeta\ngamma\n"},
    )
    assert result["ok"] is True
    assert result["count"] == 3
    assert result["registration_sha256"] == registration.registration_sha256


def test_custom_invocation_enforces_declared_basic_input_type(tmp_path: Path) -> None:
    data_root, workspace = _make_room(tmp_path)
    _publish_and_bind(data_root, workspace)

    with pytest.raises(CapabilityUsageError, match="declared type string"):
        invoke_capability(workspace, "count_lines", {"text": 123})


def test_cli_register_request_then_host_settlement_activates_one_registry(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    data_root, workspace = _make_room(tmp_path, "room_cli")
    _write_draft(workspace)
    cases_file = workspace / ".codex-room" / "count_lines_cases.json"
    cases_file.parent.mkdir(exist_ok=True)
    cases_file.write_text(json.dumps(_cases()), encoding="utf-8")
    monkeypatch.chdir(workspace)

    assert main(
        [
            "register",
            "count_lines",
            "--cases-file",
            ".codex-room/count_lines_cases.json",
        ]
    ) == 0
    registered = json.loads(capsys.readouterr().out.strip())
    assert registered["operation"] == "register"
    assert registered["ok"] is True
    assert registered["state"] == "verification_passed_host_pending"
    assert registered["capability_id"] == "count_lines"

    assert main(["list"]) == 0
    listed_before = json.loads(capsys.readouterr().out.strip())
    assert "count_lines" not in [item["id"] for item in listed_before["capabilities"]]

    runtime = RoomRuntime(db=None, adapter=None, data_root=data_root)
    outcomes = runtime._settle_custom_capability_registration_requests(
        "room_cli",
        [
            {
                "type": "deterministic_capability_registry",
                "status": "completed",
                "operation": "register",
                "capability": "count_lines",
                "registration_request": registered["registration_request"],
            }
        ],
    )
    assert outcomes[0]["status"] == "completed"
    assert outcomes[0]["capability"] == "count_lines"
    assert len(outcomes[0]["registration_sha256"]) == 64

    assert main(["list"]) == 0
    listed = json.loads(capsys.readouterr().out.strip())
    assert "count_lines" in [item["id"] for item in listed["capabilities"]]

    assert main(["inspect", "count_lines"]) == 0
    inspected = json.loads(capsys.readouterr().out.strip())
    assert inspected["capability"]["origin"] == "custom"

    assert main(
        [
            "invoke",
            "count_lines",
            "--input-json",
            '{"text":"one\\ntwo\\n"}',
        ]
    ) == 0
    invoked = json.loads(capsys.readouterr().out.strip())
    assert invoked["ok"] is True
    assert invoked["count"] == 2
    assert len(invoked["registration_sha256"]) == 64


def test_host_settlement_rejects_draft_changed_after_sandbox_verification(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    data_root, workspace = _make_room(tmp_path, "room_race")
    draft = _write_draft(workspace)
    cases_file = workspace / ".codex-room" / "count_lines_cases.json"
    cases_file.parent.mkdir(exist_ok=True)
    cases_file.write_text(json.dumps(_cases()), encoding="utf-8")
    monkeypatch.chdir(workspace)

    assert main(
        [
            "register",
            "count_lines",
            "--cases-file",
            ".codex-room/count_lines_cases.json",
        ]
    ) == 0
    registered = json.loads(capsys.readouterr().out.strip())
    (draft / "capability.py").write_text(_code(99), encoding="utf-8")

    runtime = RoomRuntime(db=None, adapter=None, data_root=data_root)
    outcomes = runtime._settle_custom_capability_registration_requests(
        "room_race",
        [
            {
                "type": "deterministic_capability_registry",
                "status": "completed",
                "operation": "register",
                "capability": "count_lines",
                "registration_request": registered["registration_request"],
            }
        ],
    )

    assert outcomes[0]["status"] == "error"
    assert "does not match" in outcomes[0]["error"]
    assert load_room_custom_capabilities(data_root, "room_race") == {}
