# File responsibility: Diff result presenter for UI.
#
# Coordinates diff loading, action handling, and view updates.
# Delegates pure presentation mapping to focused presenter helper modules.
"""Diff result presenter for UI.

This module provides the DiffPresenter class that transforms domain-level
diff results into UI-friendly presentation models.
"""

from collections.abc import Callable
from pathlib import Path

from ...application.actions.create_document_diffs import CreateDocumentDiffsAction
from ...application.actions.get_committed_file_paths import GetCommittedFilePathsAction
from ...application.actions.get_open_eligible_documents import GetOpenEligibleDocumentsAction
from ...application.actions.get_staged_file_paths import GetStagedFilePathsAction
from ...application.actions.open_document import OpenDocumentAction
from ...application.actions.open_visual_diff import (
    OpenVisualDiffAction,
    OpenVisualDiffRequest,
    VisualDiffRequestType,
)
from ...application.actions.restore_documents import (
    RestoreDocumentsAction,
    RestoreDocumentsRequest,
    RestoreScope,
    RestoreSource,
)
from ...application.actions.result_models import (
    CreateDocumentDiffsRequest,
    DocumentDiffMode,
    DocumentDiffResult,
)
from ...application.actions.stage_documents import StageDocumentsAction
from ...application.actions.unstage_documents import UnstageDocumentsAction
from ...domain.diff.engine import DiffResult
from ...domain.diff.models import DiffState
from ...domain.freecad_ports import DocumentLike
from ...domain.git.models import GitRepository
from ...domain.settings import SettingsRepository
from ...domain.snapshots.models import Snapshot
from ...utils import Log, translate
from ..protocols.diff_view import DiffView
from ..state import UIState
from ..views.history.models import HistorySelection
from .document_diff.document_mapper import build_document_presentations, compute_stage_button_state
from .document_diff.summary_state import (
    SummaryButtonState,
    build_summary_button_state,
    count_summary_counts,
)
from .property_diff.property_mapper import transform_property_diffs


class DiffPresenter:
    """Transform DiffResult into presentation models and call view methods.

    This presenter transforms domain-level diff results into UI-friendly
    presentation models, then calls view protocol methods to trigger
    the actual UI rendering.

    Dependencies are injected for testability.
    """

    def __init__(
        self,
        view: DiffView,
        ui_state: UIState,
        get_eligible_docs_action: GetOpenEligibleDocumentsAction,
        create_document_diffs_action: CreateDocumentDiffsAction,
        stage_documents_action: StageDocumentsAction,
        unstage_documents_action: UnstageDocumentsAction,
        get_staged_file_paths_action: GetStagedFilePathsAction,
        get_committed_file_paths_action: GetCommittedFilePathsAction,
        open_visual_feature_diff_action: OpenVisualDiffAction,
        open_document_action: OpenDocumentAction,
        restore_documents_action: RestoreDocumentsAction,
        settings_repo: SettingsRepository | None = None,
    ) -> None:
        """Initialize with required dependencies.

        Args:
            view: DiffView implementation to display diff results
            ui_state: UI state holder containing git repository info
            get_eligible_docs_action: Action to get eligible open documents
            create_document_diffs_action: Action to orchestrate document diffs by mode
            stage_documents_action: Action to stage documents to git
            settings_repo: Settings repository for runtime precision (optional, uses default if None)
        """
        from ...domain.config import FLOAT_PRECISION as DEFAULT_FLOAT_PRECISION

        self._view = view
        self._ui_state = ui_state
        self._get_eligible_docs = get_eligible_docs_action
        self._create_document_diffs = create_document_diffs_action
        self._stage_documents = stage_documents_action
        self._unstage_documents = unstage_documents_action
        self._open_visual_feature_diff = open_visual_feature_diff_action
        self._open_document = open_document_action
        self._restore_documents = restore_documents_action
        self._get_staged_file_paths = get_staged_file_paths_action
        self._get_committed_file_paths = get_committed_file_paths_action
        self._settings_repo = settings_repo
        self._default_precision = DEFAULT_FLOAT_PRECISION
        self._diff_results_by_path: dict[str, DiffResult] = {}
        self._document_results_by_path: dict[str, DocumentDiffResult] = {}
        self._current_history_selection: HistorySelection | None = None
        self._focus_history_window_callback: Callable[[], None] | None = None

        # Wire up the callback for history selection
        self._view.set_user_history_selection_requested_callback(self.on_history_item_selected)

        # Wire Stage All callback
        self._view.set_stage_all_callback(self.on_stage_all_clicked)
        self._view.set_remove_all_button_callback(self.on_remove_all_from_reviewed_clicked)
        self._view.set_remove_from_reviewed_button_callback(self.on_remove_from_reviewed_button_clicked)
        self._view.set_remove_all_from_reviewed_callback(self.on_remove_all_from_reviewed_clicked)
        self._view.set_mark_all_reviewed_from_in_progress_callback(self.on_stage_all_clicked)
        self._view.set_restore_button_callback(self.on_restore_document_clicked)
        self._view.set_restore_all_button_callback(self.on_restore_all_clicked)
        self._view.set_restore_all_from_history_context_callback(self.on_restore_all_from_history_context)
        self._view.set_open_document_for_comparison_callback(self.on_open_document_for_comparison_clicked)

    def on_open_document_for_comparison_clicked(self, git_path: str) -> None:
        """Open missing working-tree document in FreeCAD, then recompute Current Files diff."""
        repo = self._ui_state.git_repository
        if repo is None:
            Log.warning("No git repository detected")
            return
        document_path = str(Path(repo.absolute_path) / git_path)
        result = self._open_document.execute(document_path)
        if not result.is_success:
            if result.message:
                Log.warning(result.message)
            return
        self._on_working_tree_selected()
        if self._focus_history_window_callback is not None:
            self._focus_history_window_callback()

    def set_focus_history_window_callback(self, callback: Callable[[], None]) -> None:
        """Set callback that focuses history host window after async FreeCAD actions."""
        self._focus_history_window_callback = callback

    def _get_precision(self) -> int:
        """Get the current float precision from settings or use default.

        Returns:
            The float precision value (decimal places) from settings,
            or the default if settings repo is not available.
        """
        if self._settings_repo is not None:
            try:
                settings = self._settings_repo.get_settings()
                return settings.float_precision
            except (AttributeError, RuntimeError):
                # If settings retrieval fails, fall back to default
                pass
        return self._default_precision

    def on_history_item_selected(self, selection: HistorySelection) -> None:
        """Handle single item selection from history list.

        Args:
            selection: HistorySelection containing item_kind and optional commit_hash
        """
        self._current_history_selection = selection
        if selection.item_kind == "WORKING_TREE":
            self._on_working_tree_selected()
        elif selection.item_kind == "STAGING":
            self._on_staging_selected()
        elif selection.item_kind == "COMMIT":
            self._on_commit_selected(selection.commit_hash)

    def clear_property_diff(self) -> None:
        """Clear property diff panel content."""
        self._view.clear_property_diff()

    def clear_doc_diff(self) -> None:
        """Clear document diff data and document/property diff panels."""
        self._diff_results_by_path.clear()
        self._view.clear_doc_diffs()

    def _on_working_tree_selected(self) -> None:
        """Handle Working Tree item selection.

        For each candidate path:
        1. Include every eligible open document
        2. Include every dirty FCStd path from git, including deleted files
        3. Display status-only rows when no snapshot diff can be computed
        """
        repo = self._ui_state.git_repository
        if repo is None:
            Log.warning("No git repository detected")
            self.clear_doc_diff()
            return

        eligible_docs = self._get_eligible_documents(repo)

        # Explicitly check None, because empty list is valid
        if eligible_docs is None:
            self.clear_doc_diff()
            return

        document_results = self._compute_working_tree_diffs(repo, eligible_docs)
        self._store_results(document_results)

        if document_results:
            self.present_diffs(document_results)
        else:
            Log.info("No diff results to display")
            self.clear_doc_diff()

    def _get_eligible_documents(self, repo: GitRepository) -> list[DocumentLike] | None:
        """Get eligible open documents for repository."""
        docs_result = self._get_eligible_docs.execute(repo)

        if not docs_result.is_success:
            Log.warning(f"Failed to get eligible documents: {docs_result.message}")
            return None

        return docs_result.data

    def _compute_working_tree_diffs(
        self, repo: GitRepository, eligible_docs: list[DocumentLike]
    ) -> list[DocumentDiffResult]:
        """Compute diffs for working tree mode."""
        doc_diff_results_result = self._create_document_diffs.execute(
            CreateDocumentDiffsRequest(mode=DocumentDiffMode.WORKING_TREE, repo=repo, eligible_docs=eligible_docs)
        )
        if doc_diff_results_result.is_success and doc_diff_results_result.data:
            return doc_diff_results_result.data
        return []

    def _store_results(self, document_results: list[DocumentDiffResult]) -> None:
        """Store action results and diff payloads for later use."""
        self._diff_results_by_path.clear()
        self._document_results_by_path = {result.git_path: result for result in document_results}
        for result in document_results:
            if result.snapshot_diff is not None:
                self._diff_results_by_path[result.git_path] = result.snapshot_diff

    def _on_staging_selected(self) -> None:
        """Handle Staging item selection.

        For each staged FCStd file:
        1. Get staged snapshot from index (commit=None)
        2. Get snapshot from HEAD
        3. Create diff between HEAD and index

        Displays resulting diffs. For paths where index snapshot is missing,
        creates flat warning items (no tree below).
        """
        self._view.set_stage_all_button_visible(False)
        self._view.set_remove_all_button_visible(False)

        repo = self._ui_state.git_repository
        if repo is None:
            Log.warning("No git repository detected")
            self.clear_doc_diff()
            return

        document_results = self._compute_staging_diffs(repo)
        self._store_results(document_results)

        if document_results:
            self.present_diffs(document_results)
        else:
            Log.info("No diff results to display for staging")
            self.clear_doc_diff()

    def _compute_staging_diffs(self, repo: GitRepository) -> list[DocumentDiffResult]:
        """Compute diffs for staging mode."""
        doc_diff_results_result = self._create_document_diffs.execute(
            CreateDocumentDiffsRequest(mode=DocumentDiffMode.STAGING, repo=repo)
        )
        if doc_diff_results_result.is_success and doc_diff_results_result.data:
            return doc_diff_results_result.data
        return []

    def _on_commit_selected(self, commit_hash: str | None) -> None:
        """Handle commit item selection.

        Requests document-level commit diffs via CreateDocumentDiffsAction,
        then stores results and presents them to the view.
        """
        self._view.set_stage_all_button_visible(False)
        self._view.set_remove_all_button_visible(False)

        if commit_hash is None:
            Log.warning("Commit selection received without commit hash")
            self.clear_doc_diff()
            return

        repo = self._ui_state.git_repository
        if repo is None:
            Log.warning("No git repository detected")
            self.clear_doc_diff()
            return

        document_results = self._compute_commit_diffs(repo, commit_hash)
        self._store_results(document_results)

        if document_results:
            self.present_diffs(document_results)
        else:
            Log.info(f"No FCStd files changed in commit {commit_hash}")
            self.clear_doc_diff()

    def _compute_commit_diffs(self, repo: GitRepository, commit_hash: str) -> list[DocumentDiffResult]:
        """Compute diffs for commit mode."""
        doc_diff_results_result = self._create_document_diffs.execute(
            CreateDocumentDiffsRequest(mode=DocumentDiffMode.COMMIT, repo=repo, commit_hash=commit_hash)
        )
        if doc_diff_results_result.is_success and doc_diff_results_result.data:
            return doc_diff_results_result.data
        return []

    def on_add_button_clicked(self, git_path: str) -> None:
        """Handle '+ Stage' button click for staging.

        For deleted documents, stages the deletion with no snapshots.
        For other documents, stages the new snapshot from the diff result.
        """
        repo = self._ui_state.git_repository
        if repo is None:
            Log.warning("No git repository detected")
            return

        # Use document result to determine staging strategy.
        document_result = self._document_results_by_path.get(git_path)
        if document_result is None:
            Log.warning(f"No document result found for {git_path}")
            return

        # Deleted document -- stage deletion, no snapshot to persist.
        if document_result.document_state == DiffState.DELETED:
            result = self._stage_documents.execute(repo, [], deleted_paths=[git_path])
            if not result.is_success:
                Log.warning(f"Failed to stage deleted document: {result.message}")
                return

            Log.info(f"Successfully staged deletion of {git_path}")
            self.clear_property_diff()
            self._remove_path_from_cached_working_tree_results(git_path)
            return

        # Normal document -- require a snapshot diff to stage.
        diff_result = self._diff_results_by_path.get(git_path)
        if diff_result is None:
            Log.warning(f"No diff result found for {git_path}")
            return

        # Get the working tree snapshot (new_snapshot) from the diff
        # Since we're in working tree view, old_snapshot may be None
        working_snapshot = diff_result.new_snapshot

        # Stage the document
        result = self._stage_documents.execute(repo, [working_snapshot], deleted_paths=[])
        if not result.is_success:
            Log.warning(f"Failed to stage document: {result.message}")
            return

        Log.info(f"Successfully staged {git_path}")

        # Clear stale property view tied to prior node selection
        self.clear_property_diff()

        # Remove staged path from cached Current Files results and re-present remainder.
        self._remove_path_from_cached_working_tree_results(git_path)

    def on_stage_all_clicked(self) -> None:
        """Handle 'Stage All' button click.

        Collects snapshots for non-deleted stage-able documents and deleted paths
        for stage-able deleted documents, then stages everything in one call.
        """
        repo = self._ui_state.git_repository
        if repo is None:
            Log.warning("No git repository detected")
            return

        snapshots: list[Snapshot] = []
        deleted_paths: list[str] = []

        for document_result in self._document_results_by_path.values():
            if not compute_stage_button_state(document_result, True):
                # Not stage-able -- skip.
                continue

            if document_result.document_state == DiffState.DELETED:
                # Deleted documents are staged by path, not snapshot.
                deleted_paths.append(document_result.git_path)
                continue

            # Non-deleted documents need a snapshot diff to stage.
            diff_result = self._diff_results_by_path.get(document_result.git_path)
            if diff_result is not None and diff_result.new_snapshot is not None:
                snapshots.append(diff_result.new_snapshot)

        # Nothing to stage.
        if not snapshots and not deleted_paths:
            # Normal no-op case (for example, Current Files context action with nothing to stage).
            return

        # Stage all documents
        result = self._stage_documents.execute(repo, snapshots, deleted_paths=deleted_paths)
        if not result.is_success:
            Log.warning(f"Failed to stage documents: {result.message}")
            return

        Log.info(f"Successfully staged {len(snapshots) + len(deleted_paths)} documents")

        # Clear current doc/property selection before reloading trees
        self.clear_doc_diff()

        # Refresh the working tree view to reflect staged state
        self._on_working_tree_selected()

    def _remove_path_from_cached_working_tree_results(self, git_path: str) -> None:
        """Remove one path from cached working-tree results and refresh view from cache."""
        self._diff_results_by_path.pop(git_path, None)
        self._document_results_by_path.pop(git_path, None)

        if not self._document_results_by_path:
            self.clear_doc_diff()
            return

        remaining_results = sorted(self._document_results_by_path.values(), key=lambda result: result.git_path)
        self.present_diffs(remaining_results)

    def on_remove_from_reviewed_button_clicked(self, git_path: str) -> None:
        """Unstage one reviewed document unit (FCStd + snapshot yaml)."""
        repo = self._ui_state.git_repository
        if repo is None:
            Log.warning("No git repository detected")
            return

        result = self._unstage_documents.execute(repo, [git_path])
        if not result.is_success:
            Log.warning(f"Failed to remove document from reviewed: {result.message}")
            return

        Log.info(f"Removed reviewed document: {git_path}")
        self.clear_property_diff()
        self._on_staging_selected()

    def on_remove_all_from_reviewed_clicked(self) -> None:
        """Unstage all reviewed staged paths from index."""
        repo = self._ui_state.git_repository
        if repo is None:
            Log.warning("No git repository detected")
            return

        result = self._unstage_documents.execute(repo, None)
        if not result.is_success:
            Log.warning(f"Failed to remove all reviewed files: {result.message}")
            return

        Log.info("Removed all reviewed files")
        self.clear_property_diff()
        current_selection = self._view.get_current_history_selection()
        if current_selection is None:
            return
        if current_selection.item_kind == "STAGING":
            self._on_staging_selected()
        elif current_selection.item_kind == "WORKING_TREE":
            self._on_working_tree_selected()

    def on_restore_document_clicked(self, git_path: str) -> None:
        """Restore one document for current staging/commit source."""
        current = self._current_history_selection
        repo = self._ui_state.git_repository
        if current is None or repo is None:
            return
        if current.item_kind not in ("STAGING", "COMMIT"):
            return
        source, commit_hash = self._restore_source_from_selection(current)
        if not self._view.show_restore_file_confirmation_dialog(git_path):
            return
        request = RestoreDocumentsRequest(
            repo=repo,
            source=source,
            scope=RestoreScope.SINGLE_PATH,
            commit_hash=commit_hash,
            paths=[git_path],
        )
        self._execute_restore(request)

    def on_restore_all_clicked(self) -> None:
        """Restore listed/all files for current staging/commit source."""
        current = self._current_history_selection
        if current is None:
            return
        self.on_restore_all_from_history_context(current)

    def on_restore_all_from_history_context(self, selection: HistorySelection) -> None:
        """Restore from history context selection without changing selected row."""
        repo = self._ui_state.git_repository
        if repo is None:
            return
        if selection.item_kind not in ("STAGING", "COMMIT"):
            return
        scope_text = self._view.show_restore_scope_dialog()
        if scope_text is None:
            return
        if not self._view.show_restore_file_confirmation_dialog(""):
            return

        source, commit_hash = self._restore_source_from_selection(selection)
        listed_paths = self._listed_paths_for_selection(repo, selection)
        scope = RestoreScope.LISTED_FCSTD if scope_text == "listed_fcstd" else RestoreScope.ALL_FCSTD
        request = RestoreDocumentsRequest(
            repo=repo,
            source=source,
            scope=scope,
            commit_hash=commit_hash,
            paths=listed_paths,
        )
        self._execute_restore(request)

    def _restore_source_from_selection(self, selection: HistorySelection) -> tuple[RestoreSource, str | None]:
        if selection.item_kind == "COMMIT":
            return RestoreSource.COMMIT, selection.commit_hash
        return RestoreSource.INDEX, None

    def _listed_paths_for_selection(self, repo: GitRepository, selection: HistorySelection) -> list[str]:
        if selection.item_kind == "COMMIT" and selection.commit_hash:
            result = self._get_committed_file_paths.execute(repo, selection.commit_hash)
            return result.data if result.is_success and result.data else []
        result = self._get_staged_file_paths.execute(repo)
        return result.data if result.is_success and result.data else []

    def _execute_restore(self, request: RestoreDocumentsRequest) -> None:
        result = self._restore_documents.execute(request)
        self.clear_property_diff()
        if not result.is_success:
            self._view.show_error_message(translate("History", "Restore"), result.message or "Restore failed")
            return
        self._view.show_info_message(translate("History", "Restore"), translate("History", "Restoration complete."))
        current = self._current_history_selection
        if current is not None and current.item_kind == "WORKING_TREE":
            self._on_working_tree_selected()

    def present_diffs(
        self,
        document_results: list[DocumentDiffResult],
    ) -> None:
        """Transform multiple DiffResults into presentation models and display.

        Args:
            document_results: Action-level document diff results.
        """
        if not document_results:
            self.clear_doc_diff()
            return

        self.clear_property_diff()

        is_working_tree = (
            self._current_history_selection is not None and self._current_history_selection.item_kind == "WORKING_TREE"
        )

        presentations = build_document_presentations(document_results, is_working_tree)

        presentations.sort(key=lambda p: p.git_path)

        self._view.show_doc_diffs(presentations)
        state: SummaryButtonState = build_summary_button_state(self._current_history_selection, presentations)
        self._view.set_stage_all_button_visible(state.stage_all_visible)
        self._view.set_stage_all_button_enabled(state.stage_all_enabled)
        self._view.set_remove_all_button_visible(state.remove_all_visible)
        self._view.set_remove_all_button_enabled(state.remove_all_enabled)
        self._view.set_restore_all_button_visible(state.restore_all_visible)
        self._view.set_restore_all_button_enabled(state.restore_all_enabled)

        counts = count_summary_counts(document_results)
        self._view.show_summary(
            modified_docs=counts.modified_docs,
            deleted_docs=counts.deleted_docs,
            added_docs=counts.added_docs,
        )

    def on_visual_diff_clicked(self, git_path: str, node_path: str) -> None:
        """Open visual diff for one node in current history mode."""
        current_selection = self._current_history_selection
        if current_selection is None:
            return

        repo = self._ui_state.git_repository
        if repo is None:
            Log.warning("No git repository detected")
            return

        request = self._build_visual_diff_request(current_selection, repo, git_path, node_path)
        if request is None:
            return

        result = self._open_visual_feature_diff.execute(request)
        if not result.is_success and result.message:
            Log.warning(result.message)

    def _build_visual_diff_request(
        self,
        selection: HistorySelection,
        repo: GitRepository,
        git_path: str,
        node_path: str,
    ) -> OpenVisualDiffRequest | None:
        """Build visual diff request for current history mode."""
        if selection.item_kind == "WORKING_TREE":
            return OpenVisualDiffRequest(
                repo=repo,
                git_path=git_path,
                node_path=node_path,
                type=VisualDiffRequestType.WORKING,
            )

        if selection.item_kind == "STAGING":
            return OpenVisualDiffRequest(
                repo=repo,
                git_path=git_path,
                node_path=node_path,
                type=VisualDiffRequestType.STAGING,
            )

        if selection.item_kind == "COMMIT" and selection.commit_hash:
            return OpenVisualDiffRequest(
                repo=repo,
                git_path=git_path,
                node_path=node_path,
                type=VisualDiffRequestType.COMMIT,
                old_commit=f"{selection.commit_hash}~1",
                new_commit=selection.commit_hash,
            )

        Log.warning("Commit selection missing commit hash for visual diff")
        return None

    def on_node_selected(self, git_path: str, node_path: str) -> None:
        """Handle tree node selection to display property diffs.

        Called by view when user clicks a node in the diff tree.
        Looks up the property diffs for that path and displays them.

        Args:
            git_path: The document path (key in _diff_results_by_path)
            node_path: The path of the selected node within that document
        """
        # Guard: No diff results stored
        if not self._diff_results_by_path:
            self.clear_property_diff()
            return

        # Look up the correct DiffResult for this document
        diff_result = self._diff_results_by_path.get(git_path)
        if diff_result is None:
            Log.debug(f"[PRESENTER] No DiffResult found for git_path: {git_path}")
            self.clear_property_diff()
            return

        # Find NodeDiff by path within this document's hierarchy
        node_diff = diff_result.hierarchy.find_by_path(node_path)

        # If not found, clear properties
        if node_diff is None:
            Log.debug(f"[PRESENTER] NodeDiff not found for path: {node_path} in document {git_path}")
            self.clear_property_diff()
            return

        # Transform property diffs to presentations
        properties = transform_property_diffs(node_diff, self._get_precision())
        Log.debug(f"[PRESENTER] Transformed to {len(properties)} PropertyPresentation")
        self._view.show_property_diff(properties)
