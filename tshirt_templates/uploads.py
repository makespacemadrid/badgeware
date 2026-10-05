"""Upload helpers for user-provided badge artwork."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from time import time
from uuid import uuid4
import xml.etree.ElementTree as ET

from PIL import Image, UnidentifiedImageError

from .badges import Badge, IMAGE_EXTENSIONS

UPLOAD_BADGE_PREFIX = "upload:"
MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MIN_RECOMMENDED_IMAGE_PIXELS = 64
MAX_RECOMMENDED_IMAGE_PIXELS = 4096


def cleanup_stale_uploads(
    upload_folder: str | Path, max_age_days: float = 30, *, dry_run: bool = False
) -> list[str]:
    """Remove supported upload assets older than ``max_age_days`` and return their names."""

    folder = Path(upload_folder)
    if not folder.exists():
        return []
    cutoff = time() - max(0.0, max_age_days) * 86400
    stale = [
        path for path in folder.iterdir()
        if path.is_file() and is_allowed_upload(path.name) and path.stat().st_mtime < cutoff
    ]
    for path in stale:
        if not dry_run:
            path.unlink()
    return sorted(path.name for path in stale)


@dataclass(frozen=True)
class UploadWarning:
    """A non-fatal upload validation warning shown to users and API clients."""

    filename: str
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"filename": self.filename, "code": self.code, "message": self.message}


@dataclass(frozen=True)
class UploadSaveResult:
    """Saved upload badges plus non-fatal warnings collected while validating them."""

    badges: list[Badge]
    warnings: list[UploadWarning]


def is_allowed_upload(filename: str) -> bool:
    """Return whether a filename has a supported image extension."""

    return Path(filename).suffix.lower() in IMAGE_EXTENSIONS


def _safe_filename(filename: str) -> str:
    stem = Path(filename).stem.replace(" ", "-") or "badge"
    suffix = Path(filename).suffix.lower()
    safe_stem = "".join(character for character in stem if character.isalnum() or character in {"-", "_"})
    return f"{uuid4().hex}-{safe_stem or 'badge'}{suffix}"


def _humanize_upload(filename: str) -> str:
    stem = Path(filename).stem
    if "-" in stem:
        possible_uuid, original = stem.split("-", 1)
        if len(possible_uuid) == 32:
            stem = original
    return stem.replace("_", " ").replace("-", " ").title() or "Uploaded Badge"


def _dimension_warnings(filename: str, width: int | None, height: int | None) -> list[UploadWarning]:
    if width is None or height is None:
        return [
            UploadWarning(
                filename,
                "missing_dimensions",
                "Could not determine image dimensions; verify the artwork size before printing.",
            )
        ]
    if width < MIN_RECOMMENDED_IMAGE_PIXELS or height < MIN_RECOMMENDED_IMAGE_PIXELS:
        return [
            UploadWarning(
                filename,
                "small_dimensions",
                f"Image is only {width}×{height}px and may print softly at badge size.",
            )
        ]
    if width > MAX_RECOMMENDED_IMAGE_PIXELS or height > MAX_RECOMMENDED_IMAGE_PIXELS:
        return [
            UploadWarning(
                filename,
                "large_dimensions",
                f"Image is {width}×{height}px; consider resizing it before uploading to keep PDFs compact.",
            )
        ]
    return []


def _svg_dimensions(root: ET.Element) -> tuple[int | None, int | None]:
    width = _svg_length_to_pixels(root.attrib.get("width"))
    height = _svg_length_to_pixels(root.attrib.get("height"))
    if (width is None or height is None) and root.attrib.get("viewBox"):
        parts = root.attrib["viewBox"].replace(",", " ").split()
        if len(parts) == 4:
            try:
                width = width or round(float(parts[2]))
                height = height or round(float(parts[3]))
            except ValueError:
                pass
    return width, height


def _svg_length_to_pixels(value: str | None) -> int | None:
    if not value:
        return None
    cleaned = value.strip().lower()
    multiplier = 1.0
    unit_multipliers = {"px": 1.0, "pt": 96.0 / 72.0, "cm": 96.0 / 2.54, "mm": 96.0 / 25.4, "in": 96.0}
    for suffix, suffix_multiplier in unit_multipliers.items():
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
            multiplier = suffix_multiplier
            break
    try:
        amount = float(cleaned) * multiplier
    except ValueError:
        return None
    return round(amount) if amount > 0 else None


def validate_upload_content(filename: str, content: bytes) -> list[UploadWarning] | None:
    """Validate uploaded image bytes and return warnings, or None for invalid content."""

    if not filename or not is_allowed_upload(filename):
        return None
    if not content or len(content) > MAX_UPLOAD_BYTES:
        return None

    extension = Path(filename).suffix.lower()
    if extension == ".svg":
        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            return None
        if root.tag.rsplit("}", 1)[-1].lower() != "svg":
            return None
        width, height = _svg_dimensions(root)
        return _dimension_warnings(filename, width, height)

    try:
        with Image.open(BytesIO(content)) as image:
            width, height = image.size
            image.verify()
    except (OSError, UnidentifiedImageError):
        return None
    return _dimension_warnings(filename, width, height)


def upload_warnings_to_dicts(warnings: list[UploadWarning]) -> list[dict[str, str]]:
    """Serialize upload warnings for templates and JSON responses."""

    return [warning.to_dict() for warning in warnings]


def upload_badge_from_filename(filename: str, upload_folder: str | Path) -> Badge:
    """Build a Badge for a previously saved upload filename."""

    upload_path = Path(upload_folder) / filename
    return Badge(
        id=f"{UPLOAD_BADGE_PREFIX}{filename}",
        name=_humanize_upload(filename),
        path=f"uploaded/{filename}",
        raw_url=f"/uploads/{filename}",
        extension=upload_path.suffix.lower(),
        local_path=str(upload_path),
    )


def list_uploaded_badges(upload_folder: str | Path) -> list[Badge]:
    """Return saved user uploads as selectable badge assets."""

    folder = Path(upload_folder)
    if not folder.exists():
        return []

    return sorted(
        [upload_badge_from_filename(path.name, folder) for path in folder.iterdir() if path.is_file() and is_allowed_upload(path.name)],
        key=lambda badge: (badge.name.lower(), badge.path.lower()),
    )


def _saved_upload_path(filename: str, upload_folder: str | Path) -> Path | None:
    if not filename or Path(filename).name != filename or not is_allowed_upload(filename):
        return None
    upload_path = Path(upload_folder) / filename
    if not upload_path.is_file():
        return None
    return upload_path


def delete_uploaded_badge(filename: str, upload_folder: str | Path) -> bool:
    """Delete one saved upload by filename without allowing path traversal."""

    upload_path = _saved_upload_path(filename, upload_folder)
    if upload_path is None:
        return False
    upload_path.unlink()
    return True


def replace_uploaded_badge_bytes_with_warnings(
    filename: str, content: bytes, upload_folder: str | Path
) -> tuple[Badge | None, list[UploadWarning]]:
    """Replace one existing upload in place and return its Badge record and warnings."""

    upload_path = _saved_upload_path(filename, upload_folder)
    if upload_path is None:
        return None, []
    warnings = validate_upload_content(upload_path.name, content)
    if warnings is None:
        return None, []
    upload_path.write_bytes(content)
    return upload_badge_from_filename(upload_path.name, upload_path.parent), warnings


def replace_uploaded_badge_bytes(
    filename: str, content: bytes, upload_folder: str | Path
) -> Badge | None:
    """Replace one existing upload in place and return its Badge record."""

    badge, _warnings = replace_uploaded_badge_bytes_with_warnings(filename, content, upload_folder)
    return badge


def save_uploaded_badge_bytes_with_warnings(
    filename: str, content: bytes, upload_folder: str | Path
) -> tuple[Badge | None, list[UploadWarning]]:
    """Persist one uploaded badge from raw bytes with validation warnings."""

    warnings = validate_upload_content(filename, content)
    if warnings is None:
        return None, []

    folder = Path(upload_folder)
    folder.mkdir(parents=True, exist_ok=True)
    saved_filename = _safe_filename(filename)
    (folder / saved_filename).write_bytes(content)
    return upload_badge_from_filename(saved_filename, folder), warnings


def save_uploaded_badge_bytes(
    filename: str, content: bytes, upload_folder: str | Path
) -> Badge | None:
    """Persist one uploaded badge from raw bytes and return its Badge record."""

    badge, _warnings = save_uploaded_badge_bytes_with_warnings(filename, content, upload_folder)
    return badge


def save_uploaded_badges_with_warnings(files, upload_folder: str | Path) -> UploadSaveResult:
    """Persist uploaded badge files and return badge records plus warnings."""

    saved: list[Badge] = []
    warnings: list[UploadWarning] = []

    for upload in files:
        original_name = getattr(upload, "filename", "") or ""
        if not original_name:
            continue
        if not is_allowed_upload(original_name):
            warnings.append(
                UploadWarning(
                    original_name,
                    "unsupported_format",
                    "Upload ignored because only SVG, PNG, JPG, and JPEG artwork is supported.",
                )
            )
            continue

        upload.seek(0, 2)
        size = upload.tell()
        upload.seek(0)
        if size <= 0:
            warnings.append(UploadWarning(original_name, "empty_file", "Upload ignored because the file is empty."))
            continue
        if size > MAX_UPLOAD_BYTES:
            warnings.append(
                UploadWarning(original_name, "file_too_large", "Upload ignored because it exceeds the size limit.")
            )
            continue

        content = upload.read()
        badge, upload_warnings = save_uploaded_badge_bytes_with_warnings(
            original_name, content, upload_folder
        )
        if badge:
            saved.append(badge)
            warnings.extend(upload_warnings)
        else:
            warnings.append(
                UploadWarning(
                    original_name,
                    "invalid_image",
                    "Upload ignored because the artwork could not be validated as SVG, PNG, JPG, or JPEG.",
                )
            )

    return UploadSaveResult(saved, warnings)


def save_uploaded_badges(files, upload_folder: str | Path) -> list[Badge]:
    """Persist uploaded badge files and return their Badge records."""

    return save_uploaded_badges_with_warnings(files, upload_folder).badges
