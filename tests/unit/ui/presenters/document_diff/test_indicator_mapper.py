# SPDX-License-Identifier: LGPL-3.0-or-later
# File responsibility: Unit tests for document status indicator mapping helpers.

from freecad.history_wb.application.actions.result_models import DiffIssues, GeneralDiffIssue, SnapshotIssue
from freecad.history_wb.ui.presenters.document_diff.indicator_mapper import get_document_indicators


def test_get_document_indicators_orders_old_new_then_general() -> None:
    """Indicators keep old-side, new-side, then general issue ordering."""
    indicators = get_document_indicators(
        DiffIssues(
            old_snapshot=SnapshotIssue.MISSING,
            new_snapshot=SnapshotIssue.INVALID,
            general=[GeneralDiffIssue.GIT_CHANGED_NO_PARAMETRIC_DIFF],
        ),
        is_working_tree=False,
    )

    assert [indicator.__class__.__name__ for indicator in indicators] == [
        "OldSnapshotMissingIndicator",
        "NewInvalidSnapshotIndicator",
        "FileChangedOnlyIndicator",
    ]


def test_get_document_indicators_uses_open_document_indicator_for_working_tree_missing_new_snapshot() -> None:
    """Working-tree missing new snapshot maps to open-document indicator."""
    indicators = get_document_indicators(
        DiffIssues(new_snapshot=SnapshotIssue.MISSING),
        is_working_tree=True,
    )

    assert [indicator.__class__.__name__ for indicator in indicators] == ["WorkingTreeDocumentClosedIndicator"]


def test_get_document_indicators_uses_snapshot_missing_indicator_outside_working_tree() -> None:
    """Non-working-tree missing new snapshot keeps generic snapshot-missing indicator."""
    indicators = get_document_indicators(
        DiffIssues(new_snapshot=SnapshotIssue.MISSING),
        is_working_tree=False,
    )

    assert [indicator.__class__.__name__ for indicator in indicators] == ["NewSnapshotMissingIndicator"]


def test_get_document_indicators_returns_empty_list_when_no_issues() -> None:
    """No issues produce no indicators."""
    assert get_document_indicators(DiffIssues(), is_working_tree=False) == []
