# File responsibility: This module provides the FindActiveGitRepositoryAction class
# which is responsible for finding the active git repository from open FreeCAD documents.
# It iterates through all open documents, skipping unsaved ones, and uses GitService
# to find the first document that is in a git repository.
"""Application action for finding active git repository."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ....domain.freecad_ports import FreeCadPort
from ....domain.git.git_service import GitService
from ....utils import Log
from ..result_models import Result


if TYPE_CHECKING:
    from ....domain.git.models import GitRepository


class FindActiveGitRepositoryAction:
    """Find git repository from open FreeCAD documents.

    This action determines the active git repository by:
    1. Getting all open documents from FreeCAD
    2. Iterating through them, skipping unsaved documents
    3. Using GitService to find the git repository for each saved document
    4. Returning the first repository found

    Attributes:
        _freecad_port: The FreeCadPort instance for FreeCAD operations.
        _git_service: The GitService instance for git repository detection.
    """

    def __init__(
        self,
        freecad_port: FreeCadPort,
        git_service: GitService,
    ) -> None:
        """Initialize the action with required dependencies.

        Args:
            freecad_port: Port interface for FreeCAD document operations.
            git_service: Service for git repository detection.
        """
        self._freecad_port = freecad_port
        self._git_service = git_service

    def execute(self, current_repository: GitRepository | None = None) -> Result:
        """Find active git repository from open documents.

        Uses sticky repository logic: once a repository is detected, it is
        retained as long as at least one open document belongs to it. This
        prevents accidental switches when multiple files from different
        repositories are open simultaneously.

        Args:
            current_repository: The currently active repository, if any.
                When provided, returned immediately if any open document
                belongs to it.

        Returns:
            Result with GitRepository if found, or failure result with error message.
        """
        docs = self._freecad_port.get_all_open_documents()
        if not docs:
            return Result.failure("No documents are open")

        first_repo: GitRepository | None = None
        for doc in docs:
            doc_path = doc.FileName
            if not doc_path:
                Log.debug("Skipping unsaved document")
                continue

            repo = self._git_service.get_repository(doc_path)
            if repo is None:
                continue

            # Sticky repo: return current immediately if we encounter it
            if current_repository is not None and repo.absolute_path == current_repository.absolute_path:
                Log.debug(f"Keeping current repository: {current_repository.name}")
                return Result.success(current_repository)

            # Track first repo found as fallback
            if first_repo is None:
                first_repo = repo

        if first_repo is None:
            return Result.failure("No git repository found for open documents")

        Log.info(f"Git repository detected: {first_repo.name} ({first_repo.absolute_path})")
        return Result.success(first_repo)
