# File responsibility: FreeCAD document revision file management (storage, extraction, lookup).
"""FreeCAD document revision file management."""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

from freecad.history_wb.domain.freecad_ports import FreeCadFileManagerPort

from ...utils import Log


if TYPE_CHECKING:
    from ...domain.git.git_service import GitService
    from ...domain.git.models import GitRepository


class PreparedRevision:
    """Context manager for a prepared document revision with automatic cleanup.

    Creates a temporary directory on construction, materializes and extracts
    the FCStd archive on entry, and removes the entire tree on exit.
    """

    def __init__(
        self,
        git_service: GitService,
        repo: GitRepository,
        git_path: str,
        revision: str,
    ) -> None:
        self._git_service = git_service
        self._repo = repo
        self._git_path = git_path
        self._revision = revision
        self._temp_dir = Path(tempfile.mkdtemp(prefix="history_wb_diff_"))
        self._path: Path | None = None

    def __enter__(self) -> Path | None:
        archive_path = self._temp_dir / Path(self._git_path).name
        extract_dir = self._temp_dir / "extracted"
        self._path = self._prepare(archive_path, extract_dir)
        return self._path

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        shutil.rmtree(self._temp_dir, ignore_errors=True)

    def _prepare(self, archive_path: Path, extract_dir: Path) -> Path | None:
        if not self._materialize(archive_path):
            return None
        if not self._extract_safely(archive_path, extract_dir):
            return None
        return extract_dir

    def _materialize(self, archive_path: Path) -> bool:
        revision = self._revision
        if revision == "working":
            return self._copy_working_tree_file(archive_path)
        if revision == "staging":
            return self._git_service.write_file_from_ref(self._repo, None, self._git_path, str(archive_path))
        return self._git_service.write_file_from_ref(self._repo, revision, self._git_path, str(archive_path))

    def _copy_working_tree_file(self, archive_path: Path) -> bool:
        try:
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(self._repo.absolute_path) / self._git_path, archive_path)
            return True
        except OSError as err:
            Log.warning(f"Failed to copy working tree file: {err}")
            return False

    def _extract_safely(self, archive_path: Path, extract_dir: Path) -> bool:
        extract_dir.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(archive_path, "r") as archive:
                for member in archive.infolist():
                    self._validate_member_path(extract_dir, member.filename)
                archive.extractall(extract_dir)
            return True
        except (OSError, zipfile.BadZipFile, ValueError) as err:
            Log.warning(f"Failed to extract document archive: {err}")
            return False

    def _validate_member_path(self, destination: Path, member_name: str) -> None:
        target = destination / member_name
        try:
            target.resolve().relative_to(destination.resolve())
        except ValueError as e:
            raise ValueError(f"Unsafe archive path: {member_name}") from e


class FreeCadFileManagerAdapter(FreeCadFileManagerPort):
    """Infrastructure adapter for FreeCAD document revision file management."""

    def __init__(self, git_service: GitService) -> None:
        self._git_service = git_service

    def prepare_document_at_revision(self, repo: GitRepository, git_path: str, revision: str) -> PreparedRevision:
        """Return a context manager that materializes and extracts the revision.

        The archive is copied/extracted on __enter__, and the temp directory
        is removed on __exit__.
        """
        return PreparedRevision(self._git_service, repo, git_path, revision)

    def find_extracted_file(self, extract_root: Path, file_name: str) -> Path | None:
        """Find file by name inside extracted document tree."""
        try:
            for path in extract_root.rglob(file_name):
                if path.name == file_name:
                    return path
            return None
        except OSError as err:
            Log.warning(f"Failed to search for file in extracted tree: {err}")
            return None
