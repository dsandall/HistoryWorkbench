"""Module responsibility: Pure document-diff presentation mapping helpers."""

from .document_mapper import build_document_presentations, compute_stage_button_state
from .summary_state import (
    SummaryButtonState,
    SummaryCounts,
    build_summary_button_state,
    count_summary_counts,
)


__all__ = [
    "SummaryButtonState",
    "SummaryCounts",
    "build_document_presentations",
    "build_summary_button_state",
    "compute_stage_button_state",
    "count_summary_counts",
]
