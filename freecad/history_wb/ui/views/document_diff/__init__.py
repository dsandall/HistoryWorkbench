"""Module responsibility: Document diff panel facade and extracted child widgets."""

from .document_row import REMOVE_REVIEWED_TOOLTIP, DocumentDiffRowWidget
from .panel import DocumentDiffTreeWidget
from .status_indicators import DocumentStatusIndicatorsWidget
from .summary_bar import DocumentDiffSummaryBar


__all__ = [
    "DocumentDiffRowWidget",
    "DocumentDiffSummaryBar",
    "DocumentDiffTreeWidget",
    "DocumentStatusIndicatorsWidget",
    "REMOVE_REVIEWED_TOOLTIP",
]
