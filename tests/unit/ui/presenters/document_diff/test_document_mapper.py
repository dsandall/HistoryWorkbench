# SPDX-License-Identifier: LGPL-3.0-or-later
# File responsibility: Unit tests for pure document-diff presentation mapping helpers.

from freecad.history_wb.application.actions.result_models import (
    DiffIssues,
    DocumentDiffResult,
    SnapshotIssue,
)
from freecad.history_wb.domain.diff.models import DiffState
from freecad.history_wb.ui.presenters.document_diff.document_mapper import (
    build_document_presentations,
    compute_stage_button_state,
)


def test_stage_button_rule_uses_state_and_new_side_issue() -> None:
    """Changed docs stage only when new snapshot issue absent."""
    enabled = compute_stage_button_state(
        DocumentDiffResult(git_path="a.FCStd", document_state=DiffState.MODIFIED, issues=DiffIssues()),
        True,
    )
    blocked = compute_stage_button_state(
        DocumentDiffResult(
            git_path="a.FCStd",
            document_state=DiffState.MODIFIED,
            issues=DiffIssues(new_snapshot=SnapshotIssue.MISSING),
        ),
        True,
    )

    assert enabled is True
    assert blocked is False


def test_stage_button_enabled_with_old_side_issue_only() -> None:
    """Old-side issue alone still permits staging in working tree."""
    enabled = compute_stage_button_state(
        DocumentDiffResult(
            git_path="a.FCStd",
            document_state=DiffState.MODIFIED,
            issues=DiffIssues(old_snapshot=SnapshotIssue.MISSING),
        ),
        True,
    )

    assert enabled is True


def test_stage_button_enabled_for_deleted_document() -> None:
    """Deleted working-tree docs stage by path even without snapshot diff."""
    enabled = compute_stage_button_state(
        DocumentDiffResult(git_path="gone.FCStd", document_state=DiffState.DELETED, issues=DiffIssues()),
        True,
    )

    assert enabled is True


def test_stage_button_disable_for_closed_dirty_document() -> None:
    """Closed dirty documents block staging until reopened."""
    enabled = compute_stage_button_state(
        DocumentDiffResult(
            git_path="a.FCStd",
            document_state=DiffState.MODIFIED,
            issues=DiffIssues(new_snapshot=SnapshotIssue.MISSING),
        ),
        True,
    )

    assert enabled is False


def test_build_document_presentations_filters_out_unchanged_document_without_issues() -> None:
    """Pure mapper omits fully unchanged docs with no snapshot diff or issues."""
    presentations = build_document_presentations(
        [
            DocumentDiffResult(
                git_path="doc.FCStd",
                document_state=DiffState.UNCHANGED,
                issues=DiffIssues(),
            )
        ],
        is_working_tree=True,
    )

    assert presentations == []


def test_build_document_presentations_shows_deleted_without_snapshot_diff() -> None:
    """Deleted docs still render document rows without tree payload."""
    presentations = build_document_presentations(
        [
            DocumentDiffResult(
                git_path="gone.FCStd",
                document_state=DiffState.DELETED,
                snapshot_diff=None,
                issues=DiffIssues(),
            )
        ],
        is_working_tree=True,
    )

    assert [presentation.git_path for presentation in presentations] == ["gone.FCStd"]
