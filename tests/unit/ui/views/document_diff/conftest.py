"""File responsibility: Shared fixtures for document diff view tests."""

from __future__ import annotations

import pytest

from freecad.history_wb.qt import QtWidgets
from freecad.history_wb.ui.views.document_diff.panel import DocumentDiffTreeWidget


@pytest.fixture(scope="session", autouse=True)
def application() -> QtWidgets.QApplication:
    """Provide one QApplication instance for document diff widget tests."""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    assert isinstance(app, QtWidgets.QApplication)
    return app


@pytest.fixture
def panel() -> DocumentDiffTreeWidget:
    """Create a fresh document diff panel widget per test."""
    return DocumentDiffTreeWidget()
