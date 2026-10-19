"""
tests/unit/test_media_service.py
---------------------------------
Unit tests for media_service.py.
Tests file naming and path building without actually touching an HTTP upload.
"""
import io
import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch

from app.services import media_service


class FakeUploadFile:
    """Minimal stand-in for FastAPI's UploadFile."""
    def __init__(self, filename: str, content: bytes, content_type: str):
        self.filename = filename
        self.content_type = content_type
        self.file = io.BytesIO(content)


def test_save_upload_file_creates_file_with_uuid_name(tmp_path):
    """Saved file should have a UUID hex name (not a timestamp)."""
    with patch.object(media_service.settings, "UPLOAD_DIR", str(tmp_path)):
        fake = FakeUploadFile("photo.jpg", b"JPEG_CONTENT", "image/jpeg")
        rel_path, content_type, size = media_service.save_upload_file(fake, pet_id=42)

    filename = os.path.basename(rel_path)
    name_part, ext = os.path.splitext(filename)
    # UUID hex is 32 hex chars
    assert len(name_part) == 32
    assert all(c in "0123456789abcdef" for c in name_part)
    assert ext == ".jpg"


def test_save_upload_file_returns_relative_path(tmp_path):
    """Stored path must be relative (starts with 'pets/'), not absolute."""
    with patch.object(media_service.settings, "UPLOAD_DIR", str(tmp_path)):
        fake = FakeUploadFile("clip.mp4", b"MP4_DATA", "video/mp4")
        rel_path, _, _ = media_service.save_upload_file(fake, pet_id=7)

    assert rel_path.startswith("pets/7/")
    assert not os.path.isabs(rel_path)


def test_save_upload_file_correct_content_type(tmp_path):
    with patch.object(media_service.settings, "UPLOAD_DIR", str(tmp_path)):
        fake = FakeUploadFile("scan.png", b"PNG_DATA", "image/png")
        _, content_type, _ = media_service.save_upload_file(fake, pet_id=1)
    assert content_type == "image/png"


def test_save_upload_file_correct_size(tmp_path):
    content = b"A" * 1000
    with patch.object(media_service.settings, "UPLOAD_DIR", str(tmp_path)):
        fake = FakeUploadFile("data.bin", content, "application/octet-stream")
        _, _, size = media_service.save_upload_file(fake, pet_id=1)
    assert size == 1000


def test_save_upload_file_fallback_extension_for_no_filename(tmp_path):
    """Files with no extension should fall back to .bin."""
    with patch.object(media_service.settings, "UPLOAD_DIR", str(tmp_path)):
        fake = FakeUploadFile("", b"DATA", "application/octet-stream")
        rel_path, _, _ = media_service.save_upload_file(fake, pet_id=1)
    assert rel_path.endswith(".bin")


def test_resolve_abs_path(tmp_path):
    with patch.object(media_service.settings, "UPLOAD_DIR", str(tmp_path)):
        abs_path = media_service.resolve_abs_path("pets/1/abc.jpg")
    assert abs_path == os.path.join(str(tmp_path), "pets/1/abc.jpg")


def test_two_uploads_same_second_get_different_names(tmp_path):
    """UUID-based naming must produce unique filenames even for simultaneous uploads."""
    with patch.object(media_service.settings, "UPLOAD_DIR", str(tmp_path)):
        fake1 = FakeUploadFile("photo.jpg", b"DATA1", "image/jpeg")
        fake2 = FakeUploadFile("photo.jpg", b"DATA2", "image/jpeg")
        path1, _, _ = media_service.save_upload_file(fake1, pet_id=1)
        path2, _, _ = media_service.save_upload_file(fake2, pet_id=1)
    assert path1 != path2
