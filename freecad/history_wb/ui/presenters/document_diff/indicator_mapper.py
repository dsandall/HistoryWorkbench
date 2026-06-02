# File responsibility: Pure document-issue to status-indicator mapping.
"""Pure document-issue to status-indicator mapping helpers."""

from ....application.actions.result_models import DiffIssues, GeneralDiffIssue, SnapshotIssue
from ..presentation_models import (
    DiffComputationFailedIndicator,
    DocumentStatusIndicator,
    FileChangedOnlyIndicator,
    NewInvalidSnapshotIndicator,
    NewSnapshotMissingIndicator,
    OldInvalidSnapshotIndicator,
    OldSnapshotMissingIndicator,
    WorkingTreeDocumentClosedIndicator,
)


def get_document_indicators(issues: DiffIssues, is_working_tree: bool) -> list[DocumentStatusIndicator]:
    """Build UI indicators for categorized document issues."""
    indicators: list[DocumentStatusIndicator] = []
    if issues.old_snapshot == SnapshotIssue.MISSING:
        indicators.append(OldSnapshotMissingIndicator())
    elif issues.old_snapshot == SnapshotIssue.INVALID:
        indicators.append(OldInvalidSnapshotIndicator())

    if issues.new_snapshot == SnapshotIssue.MISSING:
        # Working-tree missing new snapshot means document closed, not missing git data.
        if is_working_tree:
            indicators.append(WorkingTreeDocumentClosedIndicator())
        else:
            indicators.append(NewSnapshotMissingIndicator())
    elif issues.new_snapshot == SnapshotIssue.INVALID:
        indicators.append(NewInvalidSnapshotIndicator())

    for issue in issues.general:
        if issue == GeneralDiffIssue.DIFF_COMPUTATION_FAILED:
            indicators.append(DiffComputationFailedIndicator())
        elif issue == GeneralDiffIssue.GIT_CHANGED_NO_PARAMETRIC_DIFF:
            indicators.append(FileChangedOnlyIndicator())
    return indicators
