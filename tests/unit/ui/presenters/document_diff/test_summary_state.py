# SPDX-License-Identifier: LGPL-3.0-or-later
# File responsibility: Unit tests for pure summary-state helpers used by diff presenter.

from freecad.history_wb.application.actions.result_models import DiffIssues, DocumentDiffResult
from freecad.history_wb.domain.diff.models import DiffState
from freecad.history_wb.ui.presenters.document_diff.summary_state import (
    SummaryButtonState,
    SummaryCounts,
    build_summary_button_state,
    count_summary_counts,
)
from freecad.history_wb.ui.presenters.presentation_models import DiffTreePresentation
from freecad.history_wb.ui.views.history.models import HistorySelection


def test_count_summary_counts_counts_document_states() -> None:
    """Summary counts derive only from document state buckets."""
    counts = count_summary_counts(
        [
            DocumentDiffResult(git_path="a.FCStd", document_state=DiffState.MODIFIED, issues=DiffIssues()),
            DocumentDiffResult(git_path="b.FCStd", document_state=DiffState.DELETED, issues=DiffIssues()),
            DocumentDiffResult(git_path="c.FCStd", document_state=DiffState.ADDED, issues=DiffIssues()),
            DocumentDiffResult(git_path="d.FCStd", document_state=DiffState.UNCHANGED, issues=DiffIssues()),
        ]
    )

    assert counts == SummaryCounts(modified_docs=1, deleted_docs=1, added_docs=1)


def test_build_summary_button_state_for_working_tree() -> None:
    """Working tree shows stage-all only and enables it when any row stages."""
    state = build_summary_button_state(
        HistorySelection(item_kind="WORKING_TREE", commit_hash=None),
        [DiffTreePresentation(nodes=[], git_path="a.FCStd", indicators=[], stage_button_enabled=True)],
    )

    assert state == SummaryButtonState(True, True, False, False, False, False)


def test_build_summary_button_state_for_staging() -> None:
    """Staging shows remove-all and restore-all when rows exist."""
    state = build_summary_button_state(
        HistorySelection(item_kind="STAGING", commit_hash=None),
        [DiffTreePresentation(nodes=[], git_path="a.FCStd", indicators=[])],
    )

    assert state == SummaryButtonState(False, False, True, True, True, True)


def test_build_summary_button_state_for_commit() -> None:
    """Commit view shows restore-all only when rows exist."""
    state = build_summary_button_state(
        HistorySelection(item_kind="COMMIT", commit_hash="abc123"),
        [DiffTreePresentation(nodes=[], git_path="a.FCStd", indicators=[])],
    )

    assert state == SummaryButtonState(False, False, False, False, True, True)


def test_build_summary_button_state_for_none_selection() -> None:
    """Missing selection hides and disables every summary action."""
    state = build_summary_button_state(None, [DiffTreePresentation(nodes=[], git_path="a.FCStd", indicators=[])])

    assert state == SummaryButtonState(False, False, False, False, False, False)
