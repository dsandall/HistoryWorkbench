# SPDX-License-Identifier: LGPL-3.0-or-later
# File responsibility: Unit tests for document-diff visual diff handler.

from __future__ import annotations

from unittest.mock import MagicMock, patch

from freecad.history_wb.application.actions.diffs.open_visual_diff import (
    OpenVisualDiffAction,
    OpenVisualDiffRequest,
    VisualDiffRequestType,
)
from freecad.history_wb.application.actions.result_models import Result
from freecad.history_wb.domain.git.models import GitRepository
from freecad.history_wb.ui.presenters.document_diff.visual_diff_handler import DocumentVisualDiffHandler
from freecad.history_wb.ui.views.history.models import HistorySelection


def test_visual_diff_handler_builds_working_tree_request() -> None:
    """Working-tree selection maps to working visual-diff request."""
    action = MagicMock(spec=OpenVisualDiffAction)
    action.execute.return_value = Result.success(True)
    handler = DocumentVisualDiffHandler(action)
    repo = GitRepository(name="repo", absolute_path="/home/user/dir/repo")

    handler.open_visual_diff(HistorySelection(item_kind="WORKING_TREE", commit_hash=None), repo, "doc.FCStd", "Body/Pad")

    request = action.execute.call_args.args[0]
    assert request == OpenVisualDiffRequest(
        repo=repo,
        git_path="doc.FCStd",
        node_path="Body/Pad",
        type=VisualDiffRequestType.WORKING,
    )


def test_visual_diff_handler_builds_commit_request() -> None:
    """Commit selection maps to commit visual-diff request with adjacent revisions."""
    action = MagicMock(spec=OpenVisualDiffAction)
    action.execute.return_value = Result.success(True)
    handler = DocumentVisualDiffHandler(action)
    repo = GitRepository(name="repo", absolute_path="/home/user/dir/repo")

    handler.open_visual_diff(HistorySelection(item_kind="COMMIT", commit_hash="abc123"), repo, "doc.FCStd", "Body/Pad")

    request = action.execute.call_args.args[0]
    assert request == OpenVisualDiffRequest(
        repo=repo,
        git_path="doc.FCStd",
        node_path="Body/Pad",
        type=VisualDiffRequestType.COMMIT,
        old_commit="abc123~1",
        new_commit="abc123",
    )


def test_visual_diff_handler_builds_staging_request() -> None:
    """Staging selection maps to staging visual-diff request."""
    action = MagicMock(spec=OpenVisualDiffAction)
    action.execute.return_value = Result.success(True)
    handler = DocumentVisualDiffHandler(action)
    repo = GitRepository(name="repo", absolute_path="/home/user/dir/repo")

    handler.open_visual_diff(HistorySelection(item_kind="STAGING", commit_hash=None), repo, "doc.FCStd", "Body/Pad")

    request = action.execute.call_args.args[0]
    assert request == OpenVisualDiffRequest(
        repo=repo,
        git_path="doc.FCStd",
        node_path="Body/Pad",
        type=VisualDiffRequestType.STAGING,
    )


def test_visual_diff_handler_skips_execute_when_commit_hash_missing() -> None:
    """Invalid commit selection logs and does not invoke visual-diff action."""
    action = MagicMock(spec=OpenVisualDiffAction)
    handler = DocumentVisualDiffHandler(action)
    repo = GitRepository(name="repo", absolute_path="/home/user/dir/repo")

    with patch("freecad.history_wb.ui.presenters.document_diff.visual_diff_handler.Log.warning") as warning:
        handler.open_visual_diff(HistorySelection(item_kind="COMMIT", commit_hash=None), repo, "doc.FCStd", "Body/Pad")

    warning.assert_called_once_with("Commit selection missing commit hash for visual diff")
    action.execute.assert_not_called()
