# SPDX-License-Identifier: LGPL-3.0-or-later
# File responsibility: Unit tests for document-diff staging and unstaging flows.

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from freecad.history_wb.application.actions.git_workflow.stage_documents import StageDocumentsAction
from freecad.history_wb.application.actions.git_workflow.unstage_documents import UnstageDocumentsAction
from freecad.history_wb.application.actions.result_models import DiffIssues, DocumentDiffResult, Result
from freecad.history_wb.domain.diff.models import DiffResult, DiffState
from freecad.history_wb.domain.git.models import GitRepository
from freecad.history_wb.domain.snapshots.models import Snapshot
from freecad.history_wb.ui.presenters.document_diff.result_store import DocumentDiffResultStore
from freecad.history_wb.ui.presenters.document_diff.staging_handler import DocumentDiffStagingHandler
from freecad.history_wb.ui.views.history.models import HistorySelection


def _make_snapshot(git_path: str) -> Snapshot:
    return Snapshot(
        snapshot_id=git_path,
        document_name=git_path,
        timestamp=datetime.now(),
        git_path=git_path,
    )


def _store_with_modified_docs(*git_paths: str) -> tuple[DocumentDiffResultStore, list[Snapshot]]:
    store = DocumentDiffResultStore()
    snapshots = [_make_snapshot(git_path) for git_path in git_paths]
    store.store_results(
        [
            DocumentDiffResult(
                git_path=snapshot.git_path,
                document_state=DiffState.MODIFIED,
                issues=DiffIssues(),
                snapshot_diff=DiffResult(old_snapshot=snapshot, new_snapshot=snapshot),
            )
            for snapshot in snapshots
        ]
    )
    return store, snapshots


def test_stage_document_removes_path_from_cached_working_tree_results() -> None:
    """Single-file staging removes cached row and returns remaining results."""
    store, snapshots = _store_with_modified_docs("a.FCStd", "b.FCStd")
    stage_documents = MagicMock(spec=StageDocumentsAction)
    unstage_documents = MagicMock(spec=UnstageDocumentsAction)
    handler = DocumentDiffStagingHandler(store, stage_documents, unstage_documents)
    repo = GitRepository(name="repo", absolute_path="/home/user/dir/repo")
    stage_documents.execute.return_value = Result.success(True)

    state = handler.stage_document(repo, "a.FCStd")

    stage_documents.execute.assert_called_once_with(repo, [snapshots[0]], deleted_paths=[])
    assert state.clear_property_diff is True
    assert state.clear_doc_diff is False
    assert [result.git_path for result in state.remaining_document_results or []] == ["b.FCStd"]


def test_stage_deleted_document_uses_deleted_paths_only() -> None:
    """Deleted working-tree docs stage by path without snapshot payload."""
    store = DocumentDiffResultStore()
    store.store_results(
        [DocumentDiffResult(git_path="gone.FCStd", document_state=DiffState.DELETED, issues=DiffIssues())]
    )
    stage_documents = MagicMock(spec=StageDocumentsAction)
    handler = DocumentDiffStagingHandler(store, stage_documents, MagicMock(spec=UnstageDocumentsAction))
    repo = GitRepository(name="repo", absolute_path="/home/user/dir/repo")
    stage_documents.execute.return_value = Result.success(True)

    state = handler.stage_document(repo, "gone.FCStd")

    stage_documents.execute.assert_called_once_with(repo, [], deleted_paths=["gone.FCStd"])
    assert state.clear_doc_diff is True


def test_stage_all_sends_snapshots_and_deleted_paths() -> None:
    """Bulk stage batches snapshot payloads and deleted paths together."""
    store, snapshots = _store_with_modified_docs("a.FCStd")
    existing_results = store.get_document_results()
    store.store_results(existing_results + [DocumentDiffResult("gone.FCStd", DiffState.DELETED, DiffIssues())])
    stage_documents = MagicMock(spec=StageDocumentsAction)
    handler = DocumentDiffStagingHandler(store, stage_documents, MagicMock(spec=UnstageDocumentsAction))
    repo = GitRepository(name="repo", absolute_path="/home/user/dir/repo")
    stage_documents.execute.return_value = Result.success(True)

    state = handler.stage_all(repo)

    stage_documents.execute.assert_called_once_with(repo, [snapshots[0]], deleted_paths=["gone.FCStd"])
    assert state.clear_doc_diff is True
    assert state.refresh_mode == "working_tree"


def test_stage_all_raises_for_impossible_missing_snapshot_cache_state() -> None:
    """Stage-all fails fast when stageable row lacks required cached diff payload."""
    store = DocumentDiffResultStore()
    store.store_results([DocumentDiffResult("a.FCStd", DiffState.MODIFIED, DiffIssues())])
    handler = DocumentDiffStagingHandler(
        store,
        MagicMock(spec=StageDocumentsAction),
        MagicMock(spec=UnstageDocumentsAction),
    )
    repo = GitRepository(name="repo", absolute_path="/home/user/dir/repo")

    with pytest.raises(RuntimeError, match="a.FCStd"):
        handler.stage_all(repo)


def test_remove_reviewed_document_refreshes_staging() -> None:
    """Single remove-from-reviewed refreshes staging selection."""
    unstage_documents = MagicMock(spec=UnstageDocumentsAction)
    handler = DocumentDiffStagingHandler(
        DocumentDiffResultStore(),
        MagicMock(spec=StageDocumentsAction),
        unstage_documents,
    )
    repo = GitRepository(name="repo", absolute_path="/home/user/dir/repo")
    unstage_documents.execute.return_value = Result.success(True)

    state = handler.remove_document_from_reviewed(repo, "doc.FCStd")

    unstage_documents.execute.assert_called_once_with(repo, ["doc.FCStd"])
    assert state.clear_property_diff is True
    assert state.refresh_mode == "staging"


@pytest.mark.parametrize(
    ("selection", "expected_refresh"),
    [
        (HistorySelection(item_kind="STAGING", commit_hash=None), "staging"),
        (HistorySelection(item_kind="WORKING_TREE", commit_hash=None), "working_tree"),
        (HistorySelection(item_kind="COMMIT", commit_hash="abc123"), "none"),
        (None, "none"),
    ],
)
def test_remove_all_reviewed_selects_follow_up_refresh(
    selection: HistorySelection | None,
    expected_refresh: str,
) -> None:
    """Remove-all chooses follow-up refresh from current history selection."""
    unstage_documents = MagicMock(spec=UnstageDocumentsAction)
    handler = DocumentDiffStagingHandler(
        DocumentDiffResultStore(),
        MagicMock(spec=StageDocumentsAction),
        unstage_documents,
    )
    repo = GitRepository(name="repo", absolute_path="/home/user/dir/repo")
    unstage_documents.execute.return_value = Result.success(True)

    state = handler.remove_all_from_reviewed(repo, selection)

    assert state.clear_property_diff is True
    assert state.refresh_mode == expected_refresh
