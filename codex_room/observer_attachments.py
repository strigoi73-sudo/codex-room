from __future__ import annotations

import base64
import binascii
import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4


MAX_OBSERVER_ATTACHMENTS = 4
MAX_OBSERVER_IMAGES = MAX_OBSERVER_ATTACHMENTS
MAX_OBSERVER_FILES = MAX_OBSERVER_ATTACHMENTS
MAX_OBSERVER_IMAGE_BYTES = 8 * 1024 * 1024
MAX_OBSERVER_FILE_BYTES = 8 * 1024 * 1024
MAX_OBSERVER_IMAGE_DATA_URL_CHARS = 12 * 1024 * 1024
MAX_OBSERVER_FILE_DATA_URL_CHARS = 12 * 1024 * 1024

_SUPPORTED_IMAGE_TYPES: dict[str, tuple[str, bytes]] = {
    "image/png": (".png", b"\x89PNG\r\n\x1a\n"),
    "image/jpeg": (".jpg", b"\xff\xd8\xff"),
    "image/webp": (".webp", b"RIFF"),
}
_ATTACHMENT_ID_RE = re.compile(r"^attachment_[0-9a-f]{32}$")
_MEDIA_TYPE_RE = re.compile(r"^[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+$")
_SAFE_SUFFIX_RE = re.compile(r"^\.[A-Za-z0-9]{1,16}$")


class ObserverAttachmentError(ValueError):
    """Observer attachment bytes or metadata are invalid or unavailable."""


@dataclass(frozen=True, slots=True)
class StoredObserverImage:
    attachment_id: str
    filename: str
    media_type: str
    size_bytes: int
    sha256: str
    path: Path

    def descriptor(self) -> dict[str, Any]:
        return {
            "id": self.attachment_id,
            "kind": "image",
            "filename": self.filename,
            "media_type": self.media_type,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }


@dataclass(frozen=True, slots=True)
class StoredObserverFile:
    attachment_id: str
    filename: str
    media_type: str
    size_bytes: int
    sha256: str
    path: Path

    def descriptor(self) -> dict[str, Any]:
        return {
            "id": self.attachment_id,
            "kind": "file",
            "filename": self.filename,
            "media_type": self.media_type,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }


def _attachment_root(data_root: Path, room_id: str) -> Path:
    return data_root / "rooms" / room_id / "attachments"


def _clean_filename(filename: str) -> str:
    clean = filename.strip()
    if not clean or len(clean) > 240:
        raise ObserverAttachmentError("Attachment filename must be 1-240 characters")
    if clean in {".", ".."} or "/" in clean or "\\" in clean or "\x00" in clean:
        raise ObserverAttachmentError("Attachment filename must not contain a path")
    return clean


def _generic_file_suffix(filename: str) -> str:
    suffix = Path(filename).suffix
    return suffix.lower() if _SAFE_SUFFIX_RE.fullmatch(suffix) else ".bin"


def _decode_base64_data_url(
    media_type: str,
    data_url: str,
    *,
    max_bytes: int,
    max_chars: int,
    label: str,
) -> bytes:
    if not _MEDIA_TYPE_RE.fullmatch(media_type):
        raise ObserverAttachmentError(f"Observer {label} has an invalid media type")
    if len(data_url) > max_chars:
        raise ObserverAttachmentError(
            f"Observer {label} payload exceeds {max_bytes} bytes"
        )
    prefix = f"data:{media_type};base64,"
    if not data_url.startswith(prefix):
        raise ObserverAttachmentError(
            f"Observer {label} data URL does not match its declared media type"
        )
    payload = data_url[len(prefix) :]
    try:
        raw = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ObserverAttachmentError(
            f"Observer {label} payload is not valid base64"
        ) from exc
    if not raw:
        raise ObserverAttachmentError(f"Observer {label} payload is empty")
    if len(raw) > max_bytes:
        raise ObserverAttachmentError(
            f"Observer {label} payload exceeds {max_bytes} bytes"
        )
    return raw


def _decode_image_data_url(media_type: str, data_url: str) -> bytes:
    if media_type not in _SUPPORTED_IMAGE_TYPES:
        raise ObserverAttachmentError(
            "Supported observer image types are PNG, JPEG, and WebP"
        )
    raw = _decode_base64_data_url(
        media_type,
        data_url,
        max_bytes=MAX_OBSERVER_IMAGE_BYTES,
        max_chars=MAX_OBSERVER_IMAGE_DATA_URL_CHARS,
        label="image",
    )

    if media_type == "image/png":
        valid_signature = raw.startswith(_SUPPORTED_IMAGE_TYPES[media_type][1])
    elif media_type == "image/jpeg":
        valid_signature = raw.startswith(_SUPPORTED_IMAGE_TYPES[media_type][1])
    else:
        valid_signature = (
            len(raw) >= 12
            and raw.startswith(b"RIFF")
            and raw[8:12] == b"WEBP"
        )
    if not valid_signature:
        raise ObserverAttachmentError(
            "Observer image bytes do not match the declared media type"
        )
    return raw


def _decode_file_data_url(media_type: str, data_url: str) -> bytes:
    if media_type in _SUPPORTED_IMAGE_TYPES:
        raise ObserverAttachmentError(
            "PNG, JPEG, and WebP attachments must use native observer image input"
        )
    return _decode_base64_data_url(
        media_type,
        data_url,
        max_bytes=MAX_OBSERVER_FILE_BYTES,
        max_chars=MAX_OBSERVER_FILE_DATA_URL_CHARS,
        label="file",
    )


def materialize_observer_images(
    data_root: Path,
    room_id: str,
    images: Iterable[Any],
) -> list[StoredObserverImage]:
    """Persist immutable observer images outside the shared agent workspace."""
    image_items = list(images)
    if len(image_items) > MAX_OBSERVER_IMAGES:
        raise ObserverAttachmentError(
            f"At most {MAX_OBSERVER_IMAGES} images may be attached to one observer message"
        )
    if not image_items:
        return []

    root = _attachment_root(data_root, room_id)
    root.mkdir(parents=True, exist_ok=True)
    stored: list[StoredObserverImage] = []
    temporary_paths: list[Path] = []
    try:
        for image in image_items:
            filename = _clean_filename(str(image.filename))
            media_type = str(image.media_type)
            raw = _decode_image_data_url(media_type, str(image.data_url))
            extension = _SUPPORTED_IMAGE_TYPES[media_type][0]
            attachment_id = f"attachment_{uuid4().hex}"
            final_path = root / f"{attachment_id}{extension}"
            temporary_path = root / f".{attachment_id}.tmp"
            temporary_paths.append(temporary_path)

            with temporary_path.open("xb") as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, final_path)
            temporary_paths.remove(temporary_path)

            stored.append(
                StoredObserverImage(
                    attachment_id=attachment_id,
                    filename=filename,
                    media_type=media_type,
                    size_bytes=len(raw),
                    sha256=hashlib.sha256(raw).hexdigest(),
                    path=final_path,
                )
            )
    except BaseException:
        for item in stored:
            item.path.unlink(missing_ok=True)
        for path in temporary_paths:
            path.unlink(missing_ok=True)
        raise
    return stored


def materialize_observer_files(
    data_root: Path,
    room_id: str,
    files: Iterable[Any],
) -> list[StoredObserverFile]:
    """Persist immutable generic observer files outside the shared agent workspace."""
    file_items = list(files)
    if len(file_items) > MAX_OBSERVER_FILES:
        raise ObserverAttachmentError(
            f"At most {MAX_OBSERVER_FILES} files may be attached to one observer message"
        )
    if not file_items:
        return []

    root = _attachment_root(data_root, room_id)
    root.mkdir(parents=True, exist_ok=True)
    stored: list[StoredObserverFile] = []
    temporary_paths: list[Path] = []
    try:
        for file_item in file_items:
            filename = _clean_filename(str(file_item.filename))
            media_type = str(file_item.media_type)
            raw = _decode_file_data_url(media_type, str(file_item.data_url))
            suffix = _generic_file_suffix(filename)
            attachment_id = f"attachment_{uuid4().hex}"
            final_path = root / f"{attachment_id}{suffix}"
            temporary_path = root / f".{attachment_id}.tmp"
            temporary_paths.append(temporary_path)

            with temporary_path.open("xb") as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, final_path)
            temporary_paths.remove(temporary_path)

            stored.append(
                StoredObserverFile(
                    attachment_id=attachment_id,
                    filename=filename,
                    media_type=media_type,
                    size_bytes=len(raw),
                    sha256=hashlib.sha256(raw).hexdigest(),
                    path=final_path,
                )
            )
    except BaseException:
        for item in stored:
            item.path.unlink(missing_ok=True)
        for path in temporary_paths:
            path.unlink(missing_ok=True)
        raise
    return stored


def remove_observer_images(images: Iterable[StoredObserverImage]) -> None:
    for image in images:
        image.path.unlink(missing_ok=True)


def remove_observer_files(files: Iterable[StoredObserverFile]) -> None:
    for file_item in files:
        file_item.path.unlink(missing_ok=True)


def _validate_descriptor_provenance(descriptor: dict[str, Any], label: str) -> tuple[str, int, str]:
    attachment_id = descriptor.get("id")
    if not isinstance(attachment_id, str) or not _ATTACHMENT_ID_RE.fullmatch(
        attachment_id
    ):
        raise ObserverAttachmentError(f"Observer {label} has an invalid attachment id")
    expected_size = descriptor.get("size_bytes")
    expected_sha256 = descriptor.get("sha256")
    if not isinstance(expected_size, int) or expected_size < 1:
        raise ObserverAttachmentError(f"Observer {label} has invalid size provenance")
    if (
        not isinstance(expected_sha256, str)
        or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256)
    ):
        raise ObserverAttachmentError(f"Observer {label} has invalid hash provenance")
    return attachment_id, expected_size, expected_sha256


def _verify_stored_bytes(
    path: Path,
    expected_size: int,
    expected_sha256: str,
    label: str,
) -> Path:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise ObserverAttachmentError(
            f"Observer {label} bytes are no longer available"
        ) from exc
    if len(raw) != expected_size or hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ObserverAttachmentError(
            f"Observer {label} bytes failed provenance verification"
        )
    return path


def resolve_observer_image_path(
    data_root: Path,
    room_id: str,
    descriptor: dict[str, Any],
) -> Path:
    """Resolve and verify one durable observer-image descriptor."""
    if descriptor.get("kind") != "image":
        raise ObserverAttachmentError("Observer attachment is not an image")
    attachment_id, expected_size, expected_sha256 = _validate_descriptor_provenance(
        descriptor, "image"
    )
    media_type = descriptor.get("media_type")
    if not isinstance(media_type, str) or media_type not in _SUPPORTED_IMAGE_TYPES:
        raise ObserverAttachmentError("Observer image has an unsupported media type")

    extension = _SUPPORTED_IMAGE_TYPES[media_type][0]
    path = _attachment_root(data_root, room_id) / f"{attachment_id}{extension}"
    return _verify_stored_bytes(path, expected_size, expected_sha256, "image")


def resolve_observer_file_path(
    data_root: Path,
    room_id: str,
    descriptor: dict[str, Any],
) -> Path:
    """Resolve and verify one durable generic observer-file descriptor."""
    if descriptor.get("kind") != "file":
        raise ObserverAttachmentError("Observer attachment is not a generic file")
    attachment_id, expected_size, expected_sha256 = _validate_descriptor_provenance(
        descriptor, "file"
    )
    filename = descriptor.get("filename")
    media_type = descriptor.get("media_type")
    if not isinstance(filename, str):
        raise ObserverAttachmentError("Observer file has an invalid filename")
    filename = _clean_filename(filename)
    if (
        not isinstance(media_type, str)
        or not _MEDIA_TYPE_RE.fullmatch(media_type)
        or media_type in _SUPPORTED_IMAGE_TYPES
    ):
        raise ObserverAttachmentError("Observer file has an unsupported media type")

    path = _attachment_root(data_root, room_id) / (
        f"{attachment_id}{_generic_file_suffix(filename)}"
    )
    return _verify_stored_bytes(path, expected_size, expected_sha256, "file")
