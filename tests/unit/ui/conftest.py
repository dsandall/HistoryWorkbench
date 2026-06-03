"""File responsibility: Shared fixtures for UI unit tests, including the singleton QApplication."""

from __future__ import annotations

import pytest

from freecad.history_wb.qt import QtWidgets


@pytest.fixture(scope="session", autouse=True)
def application() -> QtWidgets.QApplication:
    """Provide one QApplication instance for all UI unit tests."""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    assert isinstance(app, QtWidgets.QApplication)
    return app
