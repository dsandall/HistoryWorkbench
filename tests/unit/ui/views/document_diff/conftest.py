"""File responsibility: Shared fixtures for document diff view tests."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from freecad.history_wb.qt import QtWidgets
from freecad.history_wb.ui.presenters.presentation_models import DiffTreePresentation
from freecad.history_wb.ui.views.document_diff.panel import DocumentDiffTreeWidget
from freecad.history_wb.ui.views.document_diff.tree import DocumentDiffTree


@pytest.fixture
def panel() -> DocumentDiffTreeWidget:
    """Create a fresh document diff panel widget per test."""
    return DocumentDiffTreeWidget()


@pytest.fixture
def tree() -> DocumentDiffTree:
    """Create a fresh extracted document diff tree per test."""
    return DocumentDiffTree()


@pytest.fixture
def simple_document_row_factory() -> Callable[[DiffTreePresentation, str], QtWidgets.QWidget]:
    """Create minimal document-row widgets for extracted tree tests."""

    def _create_row(_diff: DiffTreePresentation, text: str) -> QtWidgets.QWidget:
        widget = QtWidgets.QLabel(text)
        widget.setObjectName("testDocumentRow")
        return widget

    return _create_row
