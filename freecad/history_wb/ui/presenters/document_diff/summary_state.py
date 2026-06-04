# File responsibility: Pure summary counts and summary-button state computation.
"""Pure summary counts and summary-button state computation.

Imports dataclasses from the view layer and provides computation functions
that operate on presenter-level types (HistorySelection, DiffTreePresentation).
"""

from ....application.actions.result_models import DocumentDiffResult
from ....domain.diff.models import DiffState
from ...views.document_diff.summary_state import SummaryButtonState, SummaryCounts
from ..presentation_models import DiffTreePresentation


def build_summary_button_state(
    current_selection,
    presentations: list[DiffTreePresentation],
) -> SummaryButtonState:
    """Return summary-bar button state for current history selection."""
    if current_selection is None:
        return SummaryButtonState.hidden()

    if current_selection.item_kind == "WORKING_TREE":
        any_stagable = any(p.stage_button_enabled for p in presentations)
        return SummaryButtonState(True, any_stagable, False, False, False, False)

    if current_selection.item_kind == "STAGING":
        has_rows = bool(presentations)
        return SummaryButtonState(False, False, True, has_rows, True, has_rows)

    if current_selection.item_kind == "COMMIT":
        has_rows = bool(presentations)
        return SummaryButtonState(False, False, False, False, True, has_rows)

    raise RuntimeError(f"Unsupported history selection kind: {current_selection.item_kind}")


def count_summary_counts(document_results: list[DocumentDiffResult]) -> SummaryCounts:
    """Count added, deleted, and modified documents for summary display."""
    modified_docs = 0
    deleted_docs = 0
    added_docs = 0
    for document_result in document_results:
        if document_result.document_state == DiffState.MODIFIED:
            modified_docs += 1
        elif document_result.document_state == DiffState.DELETED:
            deleted_docs += 1
        elif document_result.document_state == DiffState.ADDED:
            added_docs += 1
    return SummaryCounts(modified_docs=modified_docs, deleted_docs=deleted_docs, added_docs=added_docs)
