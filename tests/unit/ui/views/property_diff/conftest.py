"""File responsibility: Shared fixtures for property diff view tests."""

from __future__ import annotations

import pytest

from freecad.history_wb.qt import QtWidgets
from freecad.history_wb.ui.views.property_diff.tree import PropertyDiffTreeWidget


@pytest.fixture(scope="session", autouse=True)
def application() -> QtWidgets.QApplication:
    """Provide one QApplication instance for property diff tests."""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    assert isinstance(app, QtWidgets.QApplication)
    return app


@pytest.fixture
def widget() -> PropertyDiffTreeWidget:
    """Create a fresh property diff widget per test."""
    return PropertyDiffTreeWidget()
