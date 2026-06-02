# SPDX-License-Identifier: LGPL-3.0-or-later
# File responsibility: Unit tests for document-diff selection loading flows.

from __future__ import annotations

from unittest.mock import MagicMock, patch

from freecad.history_wb.application.actions.create_document_diffs import CreateDocumentDiffsAction
from freecad.history_wb.application.actions.get_open_eligible_documents import GetOpenEligibleDocumentsAction
from freecad.history_wb.application.actions.result_models import (
    CreateDocumentDiffsRequest,
    DocumentDiffMode,
    DiffIssues,
    DocumentDiffResult,
    Result,
)
from freecad.history_wb.domain.diff.models import DiffState
from freecad.history_wb.domain.git.models import GitRepository
from freecad.history_wb.ui.presenters.document_diff.diff_loader import DocumentDiffLoader


def test_working_tree_load_uses_eligible_docs_even_when_empty() -> None:
    """Working-tree load still diff-requests with empty eligible-doc list."""
    get_eligible_docs = MagicMock(spec=GetOpenEligibleDocumentsAction)
    create_document_diffs = MagicMock(spec=CreateDocumentDiffsAction)
    repo = GitRepository(name="repo", absolute_path="/home/user/dir/repo")
    get_eligible_docs.execute.return_value = Result.success([])
    create_document_diffs.execute.return_value = Result.success([])
    loader = DocumentDiffLoader(get_eligible_docs, create_document_diffs)

    loader.load_working_tree(repo)

    create_document_diffs.execute.assert_called_once_with(
        CreateDocumentDiffsRequest(mode=DocumentDiffMode.WORKING_TREE, repo=repo, eligible_docs=[])
    )


def test_working_tree_load_logs_failure_and_skips_diff_request_when_eligible_docs_fail() -> None:
    """Eligible-doc failure logs warning and returns empty list."""
    get_eligible_docs = MagicMock(spec=GetOpenEligibleDocumentsAction)
    create_document_diffs = MagicMock(spec=CreateDocumentDiffsAction)
    repo = GitRepository(name="repo", absolute_path="/home/user/dir/repo")
    get_eligible_docs.execute.return_value = Result.failure("boom")
    loader = DocumentDiffLoader(get_eligible_docs, create_document_diffs)

    with patch("freecad.history_wb.ui.presenters.document_diff.diff_loader.Log.warning") as warning:
        result = loader.load_working_tree(repo)

    assert result == []
    warning.assert_called_once_with("Failed to get eligible documents: boom")
    create_document_diffs.execute.assert_not_called()


def test_staging_load_builds_staging_request() -> None:
    """Staging selection delegates to diff action with staging mode."""
    get_eligible_docs = MagicMock(spec=GetOpenEligibleDocumentsAction)
    create_document_diffs = MagicMock(spec=CreateDocumentDiffsAction)
    repo = GitRepository(name="repo", absolute_path="/home/user/dir/repo")
    create_document_diffs.execute.return_value = Result.success([])
    loader = DocumentDiffLoader(get_eligible_docs, create_document_diffs)

    loader.load_staging(repo)

    create_document_diffs.execute.assert_called_once_with(
        CreateDocumentDiffsRequest(mode=DocumentDiffMode.STAGING, repo=repo)
    )


def test_staging_load_returns_action_results() -> None:
    """Staging load returns action-produced document diff results."""
    get_eligible_docs = MagicMock(spec=GetOpenEligibleDocumentsAction)
    create_document_diffs = MagicMock(spec=CreateDocumentDiffsAction)
    repo = GitRepository(name="repo", absolute_path="/home/user/dir/repo")
    expected_results = [DocumentDiffResult(git_path="doc.FCStd", document_state=DiffState.MODIFIED, issues=DiffIssues())]
    create_document_diffs.execute.return_value = Result.success(expected_results)
    loader = DocumentDiffLoader(get_eligible_docs, create_document_diffs)

    result = loader.load_staging(repo)

    assert result == expected_results


def test_commit_load_logs_diff_failure_and_returns_empty_list() -> None:
    """Commit load owns diff-action failure logging."""
    get_eligible_docs = MagicMock(spec=GetOpenEligibleDocumentsAction)
    create_document_diffs = MagicMock(spec=CreateDocumentDiffsAction)
    repo = GitRepository(name="repo", absolute_path="/home/user/dir/repo")
    create_document_diffs.execute.return_value = Result.failure("bad diff")
    loader = DocumentDiffLoader(get_eligible_docs, create_document_diffs)

    with patch("freecad.history_wb.ui.presenters.document_diff.diff_loader.Log.warning") as warning:
        result = loader.load_commit(repo, "abc123")

    assert result == []
    warning.assert_called_once_with("Failed to create document diffs: bad diff")


def test_commit_load_returns_action_results() -> None:
    """Commit load returns action-produced document diff results."""
    get_eligible_docs = MagicMock(spec=GetOpenEligibleDocumentsAction)
    create_document_diffs = MagicMock(spec=CreateDocumentDiffsAction)
    repo = GitRepository(name="repo", absolute_path="/home/user/dir/repo")
    expected_results = [DocumentDiffResult(git_path="doc.FCStd", document_state=DiffState.MODIFIED, issues=DiffIssues())]
    create_document_diffs.execute.return_value = Result.success(expected_results)
    loader = DocumentDiffLoader(get_eligible_docs, create_document_diffs)

    result = loader.load_commit(repo, "abc123")

    assert result == expected_results
