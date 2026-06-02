# File responsibility: Pure summary counts and summary-button state helpers.
"""Pure summary counts and summary-button state helpers."""

from dataclasses import dataclass

from ....application.actions.result_models import DocumentDiffResult
from ....domain.diff.models import DiffState
from ...views.history.models import HistorySelection
from ..presentation_models import DiffTreePresentation


@dataclass(frozen=True)
class SummaryButtonState:
    """Visibility and enabled state for summary-bar bulk actions."""

    stage_all_visible: bool
    stage_all_enabled: bool
    remove_all_visible: bool
    remove_all_enabled: bool
    restore_all_visible: bool
    restore_all_enabled: bool


@dataclass(frozen=True)
class SummaryCounts:
    """Per-document-state counts shown in summary bar."""

    modified_docs: int = 0
    deleted_docs: int = 0
    added_docs: int = 0


def build_summary_button_state(
    current_selection: HistorySelection | None,
    presentations: list[DiffTreePresentation],
) -> SummaryButtonState:
    """Return summary-bar button state for current history selection."""
    if current_selection is None:
        return SummaryButtonState(False, False, False, False, False, False)

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
