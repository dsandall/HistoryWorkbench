"""File responsibility: Unit tests for reusable theme-aware SVG icons."""

from __future__ import annotations

import pytest

from freecad.history_wb.qt import QtCore, QtGui, QtWidgets
from freecad.history_wb.ui.views.theme.icons import set_themed_icon


@pytest.fixture(scope="module", autouse=True)
def _qapplication() -> None:
    """Ensure QPixmap can render SVG icons during tests."""
    app = QtWidgets.QApplication.instance()
    if app is None:
        QtWidgets.QApplication([])


def _palette(base: QtGui.QColor, text: QtGui.QColor, window: QtGui.QColor) -> QtGui.QPalette:
    """Build minimal palette for icon theme tests."""
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.ColorRole.Base, base)
    palette.setColor(QtGui.QPalette.ColorRole.Text, text)
    palette.setColor(QtGui.QPalette.ColorRole.Window, window)
    palette.setColor(QtGui.QPalette.ColorRole.Button, window)
    palette.setColor(QtGui.QPalette.ColorRole.ButtonText, text)
    palette.setColor(QtGui.QPalette.ColorRole.WindowText, text)
    return palette


def _icon_center_color(icon: QtGui.QIcon) -> QtGui.QColor:
    """Return rendered color from Collapse.svg minus-sign center."""
    return icon.pixmap(64, 64).toImage().pixelColor(32, 32)


def test_set_themed_icon_refreshes_when_button_palette_changes() -> None:
    """Button helper updates rendered SVG color after palette changes."""
    button = QtWidgets.QToolButton()
    button.setPalette(
        _palette(base=QtGui.QColor(255, 255, 255), text=QtGui.QColor(0, 0, 0), window=QtGui.QColor(245, 245, 245))
    )
    set_themed_icon(button, "Collapse.svg")
    assert _icon_center_color(button.icon()) == QtGui.QColor(0, 0, 0)

    button.setPalette(
        _palette(base=QtGui.QColor(255, 255, 255), text=QtGui.QColor(240, 240, 240), window=QtGui.QColor(20, 20, 20))
    )
    QtWidgets.QApplication.sendEvent(button, QtCore.QEvent(QtCore.QEvent.Type.PaletteChange))

    assert _icon_center_color(button.icon()) == QtGui.QColor(255, 255, 255)


def test_set_themed_icon_uses_dark_application_palette_when_button_palette_is_stale() -> None:
    """Application palette fixes stylesheet themes that leave button palette light."""
    app = QtWidgets.QApplication.instance()
    assert app is not None
    original_palette = app.palette()
    try:
        app.setPalette(
            _palette(
                base=QtGui.QColor(30, 30, 30),
                text=QtGui.QColor(240, 240, 240),
                window=QtGui.QColor(20, 20, 20),
            )
        )
        button = QtWidgets.QToolButton()
        button.setPalette(
            _palette(
                base=QtGui.QColor(255, 255, 255),
                text=QtGui.QColor(0, 0, 0),
                window=QtGui.QColor(245, 245, 245),
            )
        )

        set_themed_icon(button, "Collapse.svg")

        assert _icon_center_color(button.icon()) == QtGui.QColor(255, 255, 255)
    finally:
        app.setPalette(original_palette)
