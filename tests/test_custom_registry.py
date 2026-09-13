from __future__ import annotations

import hashlib
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
    inherit_room_custom_capabilities,
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



def test_inherited_binding_preserves_exact_identity_and_normal_registry_availability(
    tmp_path: Path,
) -> None:
    data_root, source_workspace = _make_room(tmp_path, "room_origin")
    receipt, registration, source_binding = _publish_and_bind(
        data_root,
        source_workspace,
        room_id="room_origin",
    )
    source_binding_path = (
        data_root / "custom-capabilities" / "bindings" / "room_origin" / "count_lines.json"
    )
    source_binding_bytes = source_binding_path.read_bytes()
    successor_workspace = data_root / "rooms" / "room_successor" / "shared"
    successor_workspace.mkdir(parents=True)

    inherited = inherit_room_custom_capabilities(
        data_root,
        "room_origin",
        "room_successor",
        "rollover_identity",
        reserved_capability_ids={"assert_file", "compare_files", "find_files", "search_text"},
    )
    repeated = inherit_room_custom_capabilities(
        data_root,
        "room_origin",
        "room_successor",
        "rollover_identity",
        reserved_capability_ids={"assert_file", "compare_files", "find_files", "search_text"},
    )

    binding = inherited["count_lines"]
    assert repeated["count_lines"].binding_sha256 == binding.binding_sha256
    assert binding.binding_schema_version == 2
    assert binding.registration == registration
    assert binding.receipt == receipt
    assert binding.package.package_sha256 == source_binding.package.package_sha256
    assert binding.package.implementation_sha256 == source_binding.package.implementation_sha256
    assert binding.inherited_from_room_id == "room_origin"
    assert binding.inherited_from_binding_sha256 == source_binding.binding_sha256
    assert source_binding_path.read_bytes() == source_binding_bytes

    listed = list_capabilities(successor_workspace)["capabilities"]
    custom = next(item for item in listed if item["id"] == "count_lines")
    assert custom["version"] == "1"
    assert custom["registration_sha256"] == registration.registration_sha256
    inspected = inspect_capability("count_lines", successor_workspace)["capability"]
    assert inspected["binding"] == {
        "schema_version": 2,
        "room_id": "room_successor",
        "binding_sha256": binding.binding_sha256,
        "registration_room_id": "room_origin",
        "inherited_from": {
            "room_id": "room_origin",
            "binding_sha256": source_binding.binding_sha256,
        },
    }
    result = invoke_capability(
        successor_workspace,
        "count_lines",
        {"text": "alpha\nbeta\ngamma\n"},
    )
    assert result["ok"] is True
    assert result["count"] == 3
    assert result["registration_sha256"] == registration.registration_sha256
    assert result["verification_sha256"] == receipt.verification_sha256


def test_inherited_bindings_preserve_multi_generation_lineage_and_multiple_capabilities(
    tmp_path: Path,
) -> None:
    data_root, origin_workspace = _make_room(tmp_path, "room_generation_one")
    _, first_registration, first_binding = _publish_and_bind(
        data_root,
        origin_workspace,
        room_id="room_generation_one",
    )
    _, second_registration, second_binding = _publish_and_bind(
        data_root,
        origin_workspace,
        room_id="room_generation_one",
        capability_id="count_words",
    )
    (data_root / "rooms" / "room_generation_two" / "shared").mkdir(parents=True)
    generation_two = inherit_room_custom_capabilities(
        data_root,
        "room_generation_one",
        "room_generation_two",
        "rollover_generation_two",
    )
    assert list(generation_two) == ["count_lines", "count_words"]
    assert generation_two["count_lines"].registration.registration_sha256 == (
        first_registration.registration_sha256
    )
    assert generation_two["count_words"].registration.registration_sha256 == (
        second_registration.registration_sha256
    )
    assert generation_two["count_lines"].inherited_from_binding_sha256 == first_binding.binding_sha256
    assert generation_two["count_words"].inherited_from_binding_sha256 == second_binding.binding_sha256

    (data_root / "rooms" / "room_generation_three" / "shared").mkdir(parents=True)
    generation_three = inherit_room_custom_capabilities(
        data_root,
        "room_generation_two",
        "room_generation_three",
        "rollover_generation_three",
    )
    third = generation_three["count_lines"]
    assert third.registration.room_id == "room_generation_one"
    assert third.registration.registration_sha256 == first_registration.registration_sha256
    assert third.inherited_from_room_id == "room_generation_two"
    assert (
        third.inherited_from_binding_sha256
        == generation_two["count_lines"].binding_sha256
    )


def test_inherited_binding_rejects_false_predecessor_link_even_with_rehashed_record(
    tmp_path: Path,
) -> None:
    data_root, origin_workspace = _make_room(tmp_path, "room_chain_origin")
    _publish_and_bind(data_root, origin_workspace, room_id="room_chain_origin")
    (data_root / "rooms" / "room_chain_successor" / "shared").mkdir(parents=True)
    inherit_room_custom_capabilities(
        data_root,
        "room_chain_origin",
        "room_chain_successor",
        "rollover_chain",
    )
    binding_path = (
        data_root
        / "custom-capabilities"
        / "bindings"
        / "room_chain_successor"
        / "count_lines.json"
    )
    raw = json.loads(binding_path.read_text(encoding="utf-8"))
    raw["inherited_from_binding_sha256"] = "0" * 64
    payload = {key: value for key, value in raw.items() if key != "binding_sha256"}
    raw["binding_sha256"] = hashlib.sha256(
        json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    binding_path.write_text(
        json.dumps(raw, ensure_ascii=True, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )

    with pytest.raises(CustomCapabilityRegistryError, match="does not match predecessor"):
        load_room_custom_capabilities(data_root, "room_chain_successor")

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


def test_host_settlement_replay_uses_existing_exact_binding_without_mutable_draft(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    data_root, workspace = _make_room(tmp_path, "room_replay")
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
    activity = [
        {
            "type": "deterministic_capability_registry",
            "status": "completed",
            "operation": "register",
            "capability": "count_lines",
            "registration_request": registered["registration_request"],
        }
    ]
    runtime = RoomRuntime(db=None, adapter=None, data_root=data_root)

    first = runtime._settle_custom_capability_registration_requests(
        "room_replay", activity
    )
    assert first[0]["status"] == "completed"

    (draft / "capability.py").write_text(_code(99), encoding="utf-8")
    replay = runtime._settle_custom_capability_registration_requests(
        "room_replay", activity
    )

    assert replay[0]["status"] == "completed"
    assert replay[0]["registration_sha256"] == first[0]["registration_sha256"]
    assert replay[0]["binding_sha256"] == first[0]["binding_sha256"]


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
