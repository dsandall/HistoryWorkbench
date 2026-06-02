# File responsibility: Handle reviewed staging and unstaging flows for document diff presenter.
"""Handle reviewed staging and unstaging flows for document diff presenter."""

from dataclasses import dataclass
from typing import Literal

from ....application.actions.result_models import DocumentDiffResult
from ....application.actions.stage_documents import StageDocumentsAction
from ....application.actions.unstage_documents import UnstageDocumentsAction
from ....domain.diff.models import DiffState
from ....domain.git.models import GitRepository
from ....domain.snapshots.models import Snapshot
from ....utils import Log
from ...views.history.models import HistorySelection
from .document_mapper import compute_stage_button_state
from .result_store import DocumentDiffResultStore


@dataclass(frozen=True)
class StagingDisplayState:
    """Describe presenter display updates after staging flow completes."""

    clear_property_diff: bool = False
    clear_doc_diff: bool = False
    remaining_document_results: list[DocumentDiffResult] | None = None
    refresh_mode: Literal["none", "working_tree", "staging"] = "none"


class DocumentDiffStagingHandler:
    """Own stage and unstage flows for document diff presenter."""

    def __init__(
        self,
        store: DocumentDiffResultStore,
        stage_documents_action: StageDocumentsAction,
        unstage_documents_action: UnstageDocumentsAction,
    ) -> None:
        """Store action dependencies and result cache."""
        self._store = store
        self._stage_documents = stage_documents_action
        self._unstage_documents = unstage_documents_action

    def stage_document(self, repo: GitRepository, git_path: str) -> StagingDisplayState:
        """Stage one working-tree document from cached presenter state."""
        document_result = self._store.require_document_result(git_path)

        # Deleted documents stage by path only and never need snapshot payload.
        if document_result.document_state == DiffState.DELETED:
            result = self._stage_documents.execute(repo, [], deleted_paths=[git_path])
            if not result.is_success:
                Log.warning(f"Failed to stage deleted document: {result.message}")
                return StagingDisplayState()

            Log.info(f"Successfully staged deletion of {git_path}")
            return self._build_working_tree_removal_state(git_path)

        working_snapshot = self._require_working_snapshot(git_path)
        result = self._stage_documents.execute(repo, [working_snapshot], deleted_paths=[])
        if not result.is_success:
            Log.warning(f"Failed to stage document: {result.message}")
            return StagingDisplayState()

        Log.info(f"Successfully staged {git_path}")
        return self._build_working_tree_removal_state(git_path)

    def stage_all(self, repo: GitRepository) -> StagingDisplayState:
        """Stage every currently stageable working-tree document."""
        snapshots: list[Snapshot] = []
        deleted_paths: list[str] = []

        for document_result in self._store.get_document_results():
            if not compute_stage_button_state(document_result, True):
                continue

            # Deleted docs stage by git path, not by serialized snapshot payload.
            if document_result.document_state == DiffState.DELETED:
                deleted_paths.append(document_result.git_path)
                continue

            snapshots.append(self._require_working_snapshot(document_result.git_path))

        # Empty batch is normal when no stageable rows remain.
        if not snapshots and not deleted_paths:
            return StagingDisplayState()

        result = self._stage_documents.execute(repo, snapshots, deleted_paths=deleted_paths)
        if not result.is_success:
            Log.warning(f"Failed to stage documents: {result.message}")
            return StagingDisplayState()

        Log.info(f"Successfully staged {len(snapshots) + len(deleted_paths)} documents")
        return StagingDisplayState(clear_doc_diff=True, refresh_mode="working_tree")

    def remove_document_from_reviewed(self, repo: GitRepository, git_path: str) -> StagingDisplayState:
        """Unstage one reviewed document path."""
        result = self._unstage_documents.execute(repo, [git_path])
        if not result.is_success:
            Log.warning(f"Failed to remove document from reviewed: {result.message}")
            return StagingDisplayState()

        Log.info(f"Removed reviewed document: {git_path}")
        return StagingDisplayState(clear_property_diff=True, refresh_mode="staging")

    def remove_all_from_reviewed(
        self,
        repo: GitRepository,
        current_selection: HistorySelection | None,
    ) -> StagingDisplayState:
        """Unstage all reviewed documents and choose follow-up refresh."""
        result = self._unstage_documents.execute(repo, None)
        if not result.is_success:
            Log.warning(f"Failed to remove all reviewed files: {result.message}")
            return StagingDisplayState()

        Log.info("Removed all reviewed files")

        if current_selection is None:
            return StagingDisplayState(clear_property_diff=True)

        if current_selection.item_kind == "STAGING":
            return StagingDisplayState(clear_property_diff=True, refresh_mode="staging")

        if current_selection.item_kind == "WORKING_TREE":
            return StagingDisplayState(clear_property_diff=True, refresh_mode="working_tree")

        return StagingDisplayState(clear_property_diff=True)

    def _build_working_tree_removal_state(self, git_path: str) -> StagingDisplayState:
        """Remove staged path from cache and describe next presenter state."""
        remaining_results = self._store.remove_path(git_path)
        if not remaining_results:
            return StagingDisplayState(clear_doc_diff=True)

        return StagingDisplayState(
            clear_property_diff=True,
            remaining_document_results=remaining_results,
        )

    def _require_working_snapshot(self, git_path: str) -> Snapshot:
        """Return new-side snapshot for stageable working-tree row."""
        diff_result = self._store.require_diff_result(git_path)
        if diff_result.new_snapshot is None:
            raise RuntimeError(f"Working snapshot missing from cache for {git_path}")
        return diff_result.new_snapshot
