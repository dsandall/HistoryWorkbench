# File responsibility: Unit tests for FreeCadFileManagerAdapter BREP lookup.
"""Unit tests for FreeCadFileManagerAdapter."""

from __future__ import annotations

import zipfile
from pathlib import Path

from freecad.history_wb.domain.git.git_service import GitService
from freecad.history_wb.domain.git.models import GitRepository
from freecad.history_wb.infrastructure.freecad.freecad_file_manager import FreeCadFileManagerAdapter
from tests.fakes.fake_git_port import FakeGitPort


def _create_fcstd_archive(path: Path, files: dict[str, str]) -> None:
    """Create a fake FCStd archive with the given files."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)


class TestGetBrep:
    """Tests for FreeCadFileManagerAdapter.get_brep()."""

    def test_returns_brep_bytes_from_commit_archive(self, tmp_path: Path) -> None:
        fake_port = FakeGitPort()
        archive_path = tmp_path / "test.FCStd"
        _create_fcstd_archive(archive_path, {"PartData/test.Shape.brp": "BREP"})
        fake_port.set_file_bytes("abc123", "test.FCStd", archive_path.read_bytes())

        adapter = FreeCadFileManagerAdapter(git_service=GitService(fake_port))
        repo = GitRepository(name="repo", absolute_path=str(tmp_path))

        result = adapter.get_brep(repo, "test.FCStd", "abc123", "test.Shape.brp")

        assert result.document_exists is True
        assert result.brep == b"BREP"

    def test_returns_none_brep_when_member_missing(self, tmp_path: Path) -> None:
        fake_port = FakeGitPort()
        archive_path = tmp_path / "test.FCStd"
        _create_fcstd_archive(archive_path, {"PartData/Other.Shape.brp": "BREP"})
        fake_port.set_file_bytes("abc123", "test.FCStd", archive_path.read_bytes())

        adapter = FreeCadFileManagerAdapter(git_service=GitService(fake_port))
        repo = GitRepository(name="repo", absolute_path=str(tmp_path))

        result = adapter.get_brep(repo, "test.FCStd", "abc123", "test.Shape.brp")

        assert result.document_exists is True
        assert result.brep is None

    def test_returns_missing_document_when_git_read_fails(self, tmp_path: Path) -> None:
        fake_port = FakeGitPort()
        adapter = FreeCadFileManagerAdapter(git_service=GitService(fake_port))
        repo = GitRepository(name="repo", absolute_path=str(tmp_path))

        result = adapter.get_brep(repo, "missing.FCStd", "abc123", "test.Shape.brp")

        assert result.document_exists is False
        assert result.brep is None

    def test_returns_none_brep_for_corrupt_archive(self, tmp_path: Path) -> None:
        fake_port = FakeGitPort()
        fake_port.set_file_bytes("abc123", "corrupt.FCStd", b"not a zip")

        adapter = FreeCadFileManagerAdapter(git_service=GitService(fake_port))
        repo = GitRepository(name="repo", absolute_path=str(tmp_path))

        result = adapter.get_brep(repo, "corrupt.FCStd", "abc123", "test.Shape.brp")

        assert result.document_exists is True
        assert result.brep is None

    def test_working_revision_reads_working_tree_archive(self, tmp_path: Path) -> None:
        fake_port = FakeGitPort()
        archive_path = tmp_path / "test.FCStd"
        _create_fcstd_archive(archive_path, {"PartData/test.Shape.brp": "BREP"})

        adapter = FreeCadFileManagerAdapter(git_service=GitService(fake_port))
        repo = GitRepository(name="repo", absolute_path=str(tmp_path))

        result = adapter.get_brep(repo, "test.FCStd", "working", "test.Shape.brp")

        assert result.document_exists is True
        assert result.brep == b"BREP"

    def test_staging_revision_reads_index_archive(self, tmp_path: Path) -> None:
        fake_port = FakeGitPort()
        archive_path = tmp_path / "test.FCStd"
        _create_fcstd_archive(archive_path, {"PartData/test.Shape.brp": "BREP"})
        fake_port.set_file_bytes(None, "test.FCStd", archive_path.read_bytes())

        adapter = FreeCadFileManagerAdapter(git_service=GitService(fake_port))
        repo = GitRepository(name="repo", absolute_path=str(tmp_path))

        result = adapter.get_brep(repo, "test.FCStd", "staging", "test.Shape.brp")

        assert result.document_exists is True
        assert result.brep == b"BREP"
