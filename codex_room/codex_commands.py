from __future__ import annotations

import ast
import base64
import json
import re
import threading
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


CATALOG_SCHEMA_VERSION = 1
SOURCE_REPOSITORY = "openai/codex"
SOURCE_PATH = "codex-rs/tui/src/slash_command.rs"
_VERSION_RE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z.+-]{0,63}$")
_BLOB_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_RUST_STRING = r'"(?:\\.|[^"\\])*"'


class CommandCatalogSyncError(RuntimeError):
    """The exact running Codex command catalog could not be established."""


def sdk_server_identity(metadata: Any) -> dict[str, str] | None:
    """Return the App Server identity exposed by the official Codex SDK."""
    if metadata is None:
        return None
    if isinstance(metadata, Mapping):
        server_info = metadata.get("serverInfo") or metadata.get("server_info")
    else:
        server_info = getattr(metadata, "serverInfo", None)
        if server_info is None:
            server_info = getattr(metadata, "server_info", None)
    if server_info is None:
        return None
    if isinstance(server_info, Mapping):
        name = server_info.get("name")
        version = server_info.get("version")
    else:
        name = getattr(server_info, "name", None)
        version = getattr(server_info, "version", None)
    if not isinstance(version, str) or not version.strip():
        return None
    identity = {"version": version.strip()}
    if isinstance(name, str) and name.strip():
        identity["name"] = name.strip()
    return identity


class CodexCommandCatalog:
    """Exact-version built-in slash-command catalog synchronized from Codex source."""

    def __init__(
        self,
        cache_dir: Path,
        *,
        fetch_json: Callable[[str], dict[str, Any]] | None = None,
        timeout_seconds: float = 5.0,
    ) -> None:
        self.cache_dir = cache_dir
        self._fetch_json = fetch_json or self._fetch_github_json
        self.timeout_seconds = timeout_seconds
        self._lock = threading.Lock()

    def resolve(self, runtime_version: str | None) -> dict[str, Any]:
        """Return only a catalog proven to match the running Codex version."""
        try:
            version = _normalize_version(runtime_version)
        except CommandCatalogSyncError as exc:
            return self._unavailable(runtime_version, "runtime_version_unavailable", str(exc))

        source_ref = f"rust-v{version}"
        with self._lock:
            cached = self._load_cache(version, source_ref)
            if cached is not None:
                return self._current(cached, loaded_from="cache")
            try:
                manifest = self._sync(version, source_ref)
            except Exception:
                return self._unavailable(
                    version,
                    "sync_failed",
                    f"Exact command catalog could not be synchronized for Codex {version}.",
                    source_ref=source_ref,
                )
            return self._current(manifest, loaded_from="upstream")

    def _load_cache(self, version: str, source_ref: str) -> dict[str, Any] | None:
        path = self._cache_path(version)
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not _manifest_matches(manifest, version=version, source_ref=source_ref):
            return None
        return manifest

    def _sync(self, version: str, source_ref: str) -> dict[str, Any]:
        query = urllib.parse.urlencode({"ref": source_ref})
        url = (
            f"https://api.github.com/repos/{SOURCE_REPOSITORY}/contents/"
            f"{SOURCE_PATH}?{query}"
        )
        payload = self._fetch_json(url)
        if payload.get("encoding") != "base64":
            raise CommandCatalogSyncError("Codex source response was not base64 encoded")
        source_blob_sha = payload.get("sha")
        encoded = payload.get("content")
        if not isinstance(source_blob_sha, str) or not _BLOB_SHA_RE.fullmatch(source_blob_sha):
            raise CommandCatalogSyncError("Codex source response lacked a valid blob SHA")
        if not isinstance(encoded, str) or not encoded:
            raise CommandCatalogSyncError("Codex source response lacked source content")
        try:
            source = base64.b64decode(encoded, validate=False).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise CommandCatalogSyncError("Codex source response could not be decoded") from exc

        commands = parse_slash_command_source(source)
        manifest = {
            "schema_version": CATALOG_SCHEMA_VERSION,
            "runtime_version": version,
            "source_repository": SOURCE_REPOSITORY,
            "source_ref": source_ref,
            "source_path": SOURCE_PATH,
            "source_blob_sha": source_blob_sha,
            "synchronized_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "catalog_scope": "built_in",
            "dynamic_overlays": [
                {
                    "kind": "model_service_tiers",
                    "source": "live_model_catalog",
                    "included": False,
                }
            ],
            "command_count": len(commands),
            "commands": commands,
        }
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path = self._cache_path(version)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return manifest

    def _cache_path(self, version: str) -> Path:
        safe_version = re.sub(r"[^0-9A-Za-z.+-]", "_", version)
        return self.cache_dir / f"codex-slash-commands-{safe_version}.json"

    def _fetch_github_json(self, url: str) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "Codex-Room",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.load(response)
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            raise CommandCatalogSyncError("Official Codex source could not be retrieved") from exc
        if not isinstance(payload, dict):
            raise CommandCatalogSyncError("Official Codex source returned an invalid payload")
        return payload

    @staticmethod
    def _current(manifest: dict[str, Any], *, loaded_from: str) -> dict[str, Any]:
        return {
            "status": "current",
            "runtime_version": manifest["runtime_version"],
            "loaded_from": loaded_from,
            "source_repository": manifest["source_repository"],
            "source_ref": manifest["source_ref"],
            "source_path": manifest["source_path"],
            "source_blob_sha": manifest["source_blob_sha"],
            "synchronized_at": manifest["synchronized_at"],
            "catalog_scope": manifest["catalog_scope"],
            "dynamic_overlays": manifest["dynamic_overlays"],
            "command_count": manifest["command_count"],
            "commands": manifest["commands"],
        }

    @staticmethod
    def _unavailable(
        runtime_version: str | None,
        code: str,
        reason: str,
        *,
        source_ref: str | None = None,
    ) -> dict[str, Any]:
        return {
            "status": "unavailable",
            "runtime_version": runtime_version,
            "source_ref": source_ref,
            "error_code": code,
            "reason": reason,
            "command_count": 0,
            "commands": [],
        }


def parse_slash_command_source(source: str) -> list[dict[str, Any]]:
    """Parse the authoritative built-in command enum and popup descriptions."""
    enum_body = _extract_braced_body(source, "pub enum SlashCommand")
    descriptions = _parse_descriptions(source)
    commands: list[dict[str, Any]] = []
    pending_attributes: list[str] = []

    for raw_line in enum_body.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("//"):
            continue
        if line.startswith("#["):
            pending_attributes.append(line)
            continue
        variant_match = re.fullmatch(r"([A-Z][A-Za-z0-9_]*)\s*,", line)
        if variant_match is None:
            continue

        variant = variant_match.group(1)
        attributes = " ".join(pending_attributes)
        pending_attributes.clear()
        to_string = re.search(r'to_string\s*=\s*"([^"]+)"', attributes)
        serializes = re.findall(r'serialize\s*=\s*"([^"]+)"', attributes)
        command = (
            to_string.group(1)
            if to_string is not None
            else serializes[0]
            if serializes
            else _camel_to_kebab(variant)
        )
        aliases = list(dict.fromkeys(value for value in serializes if value != command))
        description = descriptions.get(variant)
        if description is None:
            raise CommandCatalogSyncError(
                f"Codex slash-command parser found no description for {variant}"
            )
        commands.append(
            {
                "command": command,
                "display": f"/{command}",
                "variant": variant,
                "aliases": aliases,
                "description": description,
                "presentation_order": len(commands),
            }
        )

    if not commands:
        raise CommandCatalogSyncError("Codex slash-command enum contained no commands")
    return commands


def _parse_descriptions(source: str) -> dict[str, str]:
    body = _extract_braced_body(source, "pub fn description")
    mapping: dict[str, str] = {}
    arm_pattern = re.compile(
        rf"((?:SlashCommand::[A-Za-z0-9_]+\s*(?:\|\s*)?)+)"
        rf"=>\s*(?:\{{\s*)?({_RUST_STRING})\s*(?:\}})?\s*,",
        re.DOTALL,
    )
    for match in arm_pattern.finditer(body):
        variants = re.findall(r"SlashCommand::([A-Za-z0-9_]+)", match.group(1))
        try:
            description = ast.literal_eval(match.group(2))
        except (SyntaxError, ValueError) as exc:
            raise CommandCatalogSyncError("Codex command description could not be parsed") from exc
        for variant in variants:
            mapping[variant] = description
    return mapping


def _extract_braced_body(source: str, marker: str) -> str:
    marker_index = source.find(marker)
    if marker_index < 0:
        raise CommandCatalogSyncError(f"Codex source lacked {marker}")
    open_index = source.find("{", marker_index)
    if open_index < 0:
        raise CommandCatalogSyncError(f"Codex source lacked a body for {marker}")
    depth = 0
    for index in range(open_index, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[open_index + 1 : index]
    raise CommandCatalogSyncError(f"Codex source had an unterminated body for {marker}")


def _camel_to_kebab(value: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "-", value).lower()


def _normalize_version(runtime_version: str | None) -> str:
    if not isinstance(runtime_version, str) or not runtime_version.strip():
        raise CommandCatalogSyncError("Running Codex runtime version is unavailable.")
    version = runtime_version.strip()
    if not _VERSION_RE.fullmatch(version):
        raise CommandCatalogSyncError("Running Codex runtime version is not a safe release identifier.")
    return version


def _manifest_matches(
    manifest: Any,
    *,
    version: str,
    source_ref: str,
) -> bool:
    if not isinstance(manifest, dict):
        return False
    if manifest.get("schema_version") != CATALOG_SCHEMA_VERSION:
        return False
    if manifest.get("runtime_version") != version or manifest.get("source_ref") != source_ref:
        return False
    if manifest.get("source_repository") != SOURCE_REPOSITORY:
        return False
    if manifest.get("source_path") != SOURCE_PATH:
        return False
    sha = manifest.get("source_blob_sha")
    if not isinstance(sha, str) or not _BLOB_SHA_RE.fullmatch(sha):
        return False
    commands = manifest.get("commands")
    if not isinstance(commands, list) or not commands:
        return False
    if manifest.get("command_count") != len(commands):
        return False
    return True
