# File responsibility: Unit tests for FreeCadFileManagerAdapter file management operations.
"""Unit tests for FreeCadFileManagerAdapter."""

from __future__ import annotations

import zipfile
from pathlib import Path

from freecad.history_wb.infrastructure.freecad.freecad_file_manager import (
    FreeCadFileManagerAdapter,
    PreparedRevision,
)
from tests.fakes.fake_git_port import FakeGitPort


def _create_fcstd_archive(path: Path, files: dict[str, str]) -> None:
    """Create a fake FCStd archive with the given files."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)


class TestFindExtractedFile:
    """Tests for FreeCadFileManagerAdapter.find_extracted_file()."""

    def test_returns_file_path_when_file_exists(self, tmp_path: Path) -> None:
        fake_port = FakeGitPort()
        adapter = FreeCadFileManagerAdapter(git_service=fake_port)

        extract_root = tmp_path / "extracted"
        target_file = extract_root / "PartData" / "Pad.Shape.brp"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text("BREP_DATA", encoding="utf-8")

        result = adapter.find_extracted_file(extract_root, "Pad.Shape.brp")

        assert result == target_file

    def test_returns_none_when_file_not_found(self, tmp_path: Path) -> None:
        fake_port = FakeGitPort()
        adapter = FreeCadFileManagerAdapter(git_service=fake_port)

        extract_root = tmp_path / "extracted"
        other_file = extract_root / "PartData" / "Other.Shape.brp"
        other_file.parent.mkdir(parents=True, exist_ok=True)
        other_file.write_text("BREP_DATA", encoding="utf-8")

        result = adapter.find_extracted_file(extract_root, "Pad.Shape.brp")

        assert result is None

    def test_returns_none_when_extract_root_is_empty(self, tmp_path: Path) -> None:
        fake_port = FakeGitPort()
        adapter = FreeCadFileManagerAdapter(git_service=fake_port)

        extract_root = tmp_path / "empty_extract"
        extract_root.mkdir(parents=True, exist_ok=True)

        result = adapter.find_extracted_file(extract_root, "Pad.Shape.brp")

        assert result is None

    def test_finds_file_in_nested_directory(self, tmp_path: Path) -> None:
        fake_port = FakeGitPort()
        adapter = FreeCadFileManagerAdapter(git_service=fake_port)

        extract_root = tmp_path / "extracted"
        target_file = extract_root / "PartData" / "SubDir" / "Pad.Shape.brp"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text("BREP_DATA", encoding="utf-8")

        result = adapter.find_extracted_file(extract_root, "Pad.Shape.brp")

        assert result == target_file


class TestPreparedRevision:
    """Tests for PreparedRevision context manager."""

    def test_extracts_valid_archive_and_returns_path(self, tmp_path: Path) -> None:
        fake_port = FakeGitPort()
        fake_port.add_git_repo(str(tmp_path))
        archive_path = tmp_path / "test.FCStd"
        _create_fcstd_archive(archive_path, {"PartData/test.Shape.brp": "BREP"})
        fake_port.set_file_bytes("abc123", "test.FCStd", archive_path.read_bytes())
        fake_port.set_resolved_ref("abc123", "abc123" * 8)

        adapter = FreeCadFileManagerAdapter(git_service=fake_port)
        repo = type("Repo", (), {"absolute_path": str(tmp_path)})()
        ctx = adapter.prepare_document_at_revision(repo, "test.FCStd", "abc123")

        assert isinstance(ctx, PreparedRevision)

        with ctx as extract_root:
            assert extract_root is not None
            assert (extract_root / "PartData" / "test.Shape.brp").exists()

        # Temp directory cleaned up after exit
        assert not ctx._temp_dir.exists()

    def test_returns_none_for_corrupt_archive(self, tmp_path: Path) -> None:
        fake_port = FakeGitPort()
        fake_port.add_git_repo(str(tmp_path))
        archive_path = tmp_path / "corrupt.FCStd"
        archive_path.write_bytes(b"Not a valid zip file content")
        fake_port.set_file_bytes("abc123", "corrupt.FCStd", archive_path.read_bytes())
        fake_port.set_resolved_ref("abc123", "abc123" * 8)

        adapter = FreeCadFileManagerAdapter(git_service=fake_port)
        repo = type("Repo", (), {"absolute_path": str(tmp_path)})()
        ctx = adapter.prepare_document_at_revision(repo, "corrupt.FCStd", "abc123")

        with ctx as extract_root:
            assert extract_root is None

        assert not ctx._temp_dir.exists()

    def test_returns_none_for_archive_with_unsafe_paths(self, tmp_path: Path) -> None:
        fake_port = FakeGitPort()
        fake_port.add_git_repo(str(tmp_path))
        archive_path = tmp_path / "unsafe.FCStd"
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.writestr("../escape.txt", "escaped content")
        fake_port.set_file_bytes("abc123", "unsafe.FCStd", archive_path.read_bytes())
        fake_port.set_resolved_ref("abc123", "abc123" * 8)

        adapter = FreeCadFileManagerAdapter(git_service=fake_port)
        repo = type("Repo", (), {"absolute_path": str(tmp_path)})()
        ctx = adapter.prepare_document_at_revision(repo, "unsafe.FCStd", "abc123")

        with ctx as extract_root:
            assert extract_root is None
            assert not (tmp_path / "escape.txt").exists()

        assert not ctx._temp_dir.exists()

    def test_returns_none_when_git_write_fails(self, tmp_path: Path) -> None:
        fake_port = FakeGitPort()
        fake_port.add_git_repo(str(tmp_path))

        adapter = FreeCadFileManagerAdapter(git_service=fake_port)
        repo = type("Repo", (), {"absolute_path": str(tmp_path)})()
        ctx = adapter.prepare_document_at_revision(repo, "missing.FCStd", "abc123")

        with ctx as extract_root:
            assert extract_root is None

        assert not ctx._temp_dir.exists()

    def test_working_revision_copies_from_working_tree(self, tmp_path: Path) -> None:
        fake_port = FakeGitPort()
        archive_path = tmp_path / "test.FCStd"
        _create_fcstd_archive(archive_path, {"PartData/test.Shape.brp": "BREP"})

        adapter = FreeCadFileManagerAdapter(git_service=fake_port)
        repo = type("Repo", (), {"absolute_path": str(tmp_path)})()
        ctx = adapter.prepare_document_at_revision(repo, "test.FCStd", "working")

        with ctx as extract_root:
            assert extract_root is not None
            assert (extract_root / "PartData" / "test.Shape.brp").exists()

    def test_staging_revision_writes_from_index(self, tmp_path: Path) -> None:
        fake_port = FakeGitPort()
        fake_port.add_git_repo(str(tmp_path))
        archive_path = tmp_path / "test.FCStd"
        _create_fcstd_archive(archive_path, {"PartData/test.Shape.brp": "BREP"})
        fake_port.set_file_bytes(None, "test.FCStd", archive_path.read_bytes())

        adapter = FreeCadFileManagerAdapter(git_service=fake_port)
        repo = type("Repo", (), {"absolute_path": str(tmp_path)})()
        ctx = adapter.prepare_document_at_revision(repo, "test.FCStd", "staging")

        with ctx as extract_root:
            assert extract_root is not None
            assert (extract_root / "PartData" / "test.Shape.brp").exists()
