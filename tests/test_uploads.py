from io import BytesIO
import os
import time

from tshirt_templates.uploads import (
    MAX_UPLOAD_BYTES,
    delete_uploaded_badge,
    is_allowed_upload,
    list_uploaded_badges,
    replace_uploaded_badge_bytes,
    save_uploaded_badge_bytes,
    save_uploaded_badge_bytes_with_warnings,
    save_uploaded_badges,
    save_uploaded_badges_with_warnings,
    cleanup_stale_uploads,
)


class FakeUpload(BytesIO):
    def __init__(self, filename: str, content: bytes):
        super().__init__(content)
        self.filename = filename

    def save(self, destination):
        with open(destination, "wb") as output:
            output.write(self.getvalue())


def test_is_allowed_upload_accepts_supported_images_only():
    assert is_allowed_upload("badge.svg")
    assert is_allowed_upload("badge.PNG")
    assert is_allowed_upload("photo.jpeg")
    assert not is_allowed_upload("notes.pdf")


def test_save_uploaded_badge_bytes_validates_and_persists(tmp_path):
    saved = save_uploaded_badge_bytes("team logo.svg", b"<svg></svg>", tmp_path)

    assert saved is not None
    assert saved.id.startswith("upload:")
    assert saved.name == "Team Logo"
    assert saved.local_path is not None
    assert (tmp_path / saved.id.removeprefix("upload:")).read_bytes() == b"<svg></svg>"


def test_save_uploaded_badge_bytes_rejects_invalid_inputs(tmp_path):
    assert save_uploaded_badge_bytes("notes.txt", b"plain text", tmp_path) is None
    assert save_uploaded_badge_bytes("empty.svg", b"", tmp_path) is None
    assert save_uploaded_badge_bytes("huge.svg", b"x" * (MAX_UPLOAD_BYTES + 1), tmp_path) is None
    assert save_uploaded_badge_bytes("fake.png", b"not an image", tmp_path) is None
    assert list(tmp_path.iterdir()) == []


def test_save_uploaded_badge_bytes_with_warnings_reports_small_dimensions(tmp_path):
    badge, warnings = save_uploaded_badge_bytes_with_warnings(
        "tiny.svg", b'<svg viewBox="0 0 32 32"></svg>', tmp_path
    )

    assert badge is not None
    assert warnings[0].code == "small_dimensions"
    assert "32×32px" in warnings[0].message


def test_save_uploaded_badges_persists_and_lists_files(tmp_path):
    saved = save_uploaded_badges(
        [FakeUpload("my badge.svg", b"<svg></svg>"), FakeUpload("notes.txt", b"nope")],
        tmp_path,
    )

    assert len(saved) == 1
    assert saved[0].id.startswith("upload:")
    assert saved[0].name == "My Badge"
    assert saved[0].raw_url.startswith("/uploads/")
    assert saved[0].local_path is not None

    listed = list_uploaded_badges(tmp_path)

    assert listed == saved


def test_save_uploaded_badges_with_warnings_reports_rejected_files(tmp_path):
    result = save_uploaded_badges_with_warnings(
        [FakeUpload("ok.svg", b"<svg></svg>"), FakeUpload("fake.png", b"not an image")],
        tmp_path,
    )

    assert len(result.badges) == 1
    assert [warning.code for warning in result.warnings] == ["missing_dimensions", "invalid_image"]


def test_delete_uploaded_badge_removes_file_and_rejects_traversal(tmp_path):
    saved = save_uploaded_badge_bytes("team.svg", b"<svg></svg>", tmp_path)
    assert saved is not None
    filename = saved.id.removeprefix("upload:")

    assert delete_uploaded_badge(filename, tmp_path) is True
    assert not (tmp_path / filename).exists()
    assert delete_uploaded_badge(filename, tmp_path) is False
    assert delete_uploaded_badge("../team.svg", tmp_path) is False


def test_replace_uploaded_badge_bytes_updates_existing_file(tmp_path):
    saved = save_uploaded_badge_bytes("team.svg", b"<svg>old</svg>", tmp_path)
    assert saved is not None
    filename = saved.id.removeprefix("upload:")

    replaced = replace_uploaded_badge_bytes(filename, b"<svg>new</svg>", tmp_path)

    assert replaced is not None
    assert replaced.id == saved.id
    assert (tmp_path / filename).read_bytes() == b"<svg>new</svg>"
    assert replace_uploaded_badge_bytes("../team.svg", b"<svg></svg>", tmp_path) is None
    assert replace_uploaded_badge_bytes(filename, b"", tmp_path) is None


def test_cleanup_stale_uploads_supports_dry_run_and_deletion(tmp_path):
    stale = tmp_path / "stale.svg"
    recent = tmp_path / "recent.png"
    ignored = tmp_path / "notes.txt"
    stale.write_text("<svg></svg>")
    recent.write_bytes(b"png")
    ignored.write_text("keep")
    old = time.time() - 40 * 86400
    os.utime(stale, (old, old))

    assert cleanup_stale_uploads(tmp_path, 30, dry_run=True) == ["stale.svg"]
    assert stale.exists()
    assert cleanup_stale_uploads(tmp_path, 30) == ["stale.svg"]
    assert not stale.exists()
    assert recent.exists() and ignored.exists()
