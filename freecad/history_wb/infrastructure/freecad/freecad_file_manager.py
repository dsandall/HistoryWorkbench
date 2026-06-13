# File responsibility: FreeCAD document revision BREP byte lookup.
"""FreeCAD document revision BREP byte lookup."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from freecad.history_wb.domain.freecad_ports import BrepLookupResult, FreeCadFileManagerPort

from ...utils import Log


if TYPE_CHECKING:
    from ...domain.git.git_service import GitService
    from ...domain.git.models import GitRepository


class FreeCadFileManagerAdapter(FreeCadFileManagerPort):
    """Infrastructure adapter for FreeCAD document revision BREP byte lookup."""

    def __init__(self, git_service: GitService) -> None:
        self._git_service = git_service

    def get_brep(self, repo: GitRepository, git_path: str, revision: str, brep_name: str) -> BrepLookupResult:
        """Return BREP bytes from one FCStd revision without extracting files."""
        archive_bytes = self._read_revision_bytes(repo, git_path, revision)
        if archive_bytes is None:
            return BrepLookupResult(document_exists=False, brep=None)

        try:
            with zipfile.ZipFile(io.BytesIO(archive_bytes), "r") as archive:
                member_name = self._find_archive_member(archive, brep_name)
                if member_name is None:
                    return BrepLookupResult(document_exists=True, brep=None)
                return BrepLookupResult(document_exists=True, brep=archive.read(member_name))
        except (OSError, zipfile.BadZipFile, KeyError) as err:
            Log.warning(f"Failed to read BREP from document archive: {err}")
            return BrepLookupResult(document_exists=True, brep=None)

    def _read_revision_bytes(self, repo: GitRepository, git_path: str, revision: str) -> bytes | None:
        if revision == "working":
            return self._read_working_tree_file(repo, git_path)
        if revision == "staging":
            return self._git_service.get_file_bytes_from_ref(repo, None, git_path)
        return self._git_service.get_file_bytes_from_ref(repo, revision, git_path)

    def _read_working_tree_file(self, repo: GitRepository, git_path: str) -> bytes | None:
        try:
            return (Path(repo.absolute_path) / git_path).read_bytes()
        except OSError as err:
            Log.warning(f"Failed to read working tree file: {err}")
            return None

    def _find_archive_member(self, archive: zipfile.ZipFile, brep_name: str) -> str | None:
        for member in archive.infolist():
            if PurePosixPath(member.filename).name == brep_name:
                return member.filename
        return None
