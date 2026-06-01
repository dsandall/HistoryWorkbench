"""File responsibility: Build theme-aware Qt icons from SVG resources."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, cast

from ....qt import QtCore, QtGui, QtWidgets
from ....resources import get_icon_path
from .colors import _color_from_key, _color_key, _ColorKey, _contrast_ratio, _is_dark_color, _relative_luminance


__all__ = ["set_themed_icon"]

_LIGHT_TEXT_LUMINANCE_THRESHOLD = 0.65
_THEMED_ICON_BINDING_ATTR = "_history_wb_themed_icon_binding"


def _themed_icon(icon_name: str, palette: QtGui.QPalette, color: QtGui.QColor | None = None) -> QtGui.QIcon:
    """Create a QIcon from an SVG resource that uses currentColor.

    Args:
        icon_name: SVG file name inside resources/icons.
        palette: Palette used to choose black or white when color is omitted.
        color: Explicit icon color. Use this for accent icons.
    """
    icon_color = color if color is not None else _themed_icon_color(palette)
    return _cached_themed_icon(icon_name, _color_key(icon_color))


def _themed_icon_color(palette: QtGui.QPalette) -> QtGui.QColor:
    """Return default monochrome icon color for the current theme."""
    if _palette_suggests_dark_icon(palette):
        return QtGui.QColor(255, 255, 255)
    return _contrast_icon_color(_primary_icon_background(palette))


def set_themed_icon(button: QtWidgets.QAbstractButton, icon_name: str) -> None:
    """Set a themed SVG icon on a button and refresh it when palette changes."""
    binding = _ThemedButtonIconBinding(button, icon_name)
    cast(Any, button).__setattr__(_THEMED_ICON_BINDING_ATTR, binding)
    button.installEventFilter(binding)
    binding.apply()


class _ThemedButtonIconBinding(QtCore.QObject):
    """Event filter that keeps one button icon synced with its palette."""

    def __init__(self, button: QtWidgets.QAbstractButton, icon_name: str) -> None:
        super().__init__(button)
        self._button = button
        self._icon_name = icon_name

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """Refresh icon after Qt style or palette changes."""
        if watched is self._button and event.type() in {
            QtCore.QEvent.Type.ApplicationPaletteChange,
            QtCore.QEvent.Type.PaletteChange,
            QtCore.QEvent.Type.Polish,
            QtCore.QEvent.Type.Show,
            QtCore.QEvent.Type.StyleChange,
        }:
            self.apply()
        return False

    def apply(self) -> None:
        """Apply current themed icon to the target button."""
        self._button.setIcon(_themed_icon(self._icon_name, _effective_icon_palette(self._button)))


def _effective_icon_palette(widget: QtWidgets.QWidget) -> QtGui.QPalette:
    """Return widget palette, falling back to application palette for stylesheet themes."""
    widget_palette = widget.palette()
    app = QtWidgets.QApplication.instance()
    if app is None:
        return widget_palette

    app = cast(QtWidgets.QApplication, app)
    app_palette = app.palette()
    if _palette_suggests_dark_icon(app_palette) and not _palette_suggests_dark_icon(widget_palette):
        return app_palette
    return widget_palette


def _palette_suggests_dark_icon(palette: QtGui.QPalette) -> bool:
    """Return true when button/window palette roles indicate dark icon surface."""
    has_dark_background = any(_is_dark_color(color) for color in _icon_background_candidates(palette))
    has_light_text = any(
        _relative_luminance(color) > _LIGHT_TEXT_LUMINANCE_THRESHOLD for color in _icon_text_candidates(palette)
    )
    return has_dark_background and has_light_text


def _contrast_icon_color(background: QtGui.QColor) -> QtGui.QColor:
    """Return black or white, whichever contrasts better with background."""
    black = QtGui.QColor(0, 0, 0)
    white = QtGui.QColor(255, 255, 255)
    return white if _contrast_ratio(white, background) > _contrast_ratio(black, background) else black


def _primary_icon_background(palette: QtGui.QPalette) -> QtGui.QColor:
    """Return most likely surface color under a transparent tool button."""
    for role in (QtGui.QPalette.ColorRole.Window, QtGui.QPalette.ColorRole.Button, QtGui.QPalette.ColorRole.Base):
        color = palette.color(role)
        if color.isValid():
            return color
    return QtGui.QColor(255, 255, 255)


def _icon_background_candidates(palette: QtGui.QPalette) -> list[QtGui.QColor]:
    """Return palette background roles that can sit behind icons."""
    return [
        palette.color(QtGui.QPalette.ColorRole.Button),
        palette.color(QtGui.QPalette.ColorRole.Window),
        palette.color(QtGui.QPalette.ColorRole.Base),
    ]


def _icon_text_candidates(palette: QtGui.QPalette) -> list[QtGui.QColor]:
    """Return palette text roles that describe icon foreground intent."""
    return [
        palette.color(QtGui.QPalette.ColorRole.ButtonText),
        palette.color(QtGui.QPalette.ColorRole.WindowText),
        palette.color(QtGui.QPalette.ColorRole.Text),
    ]


@lru_cache(maxsize=256)
def _cached_themed_icon(icon_name: str, icon_color_key: _ColorKey) -> QtGui.QIcon:
    """Return cached icon rendered with one foreground color."""
    icon_path = get_icon_path(icon_name)
    if not icon_path.exists():
        raise RuntimeError(f"Icon resource not found: {icon_name}")

    svg_text = icon_path.read_text(encoding="utf-8")
    if "currentColor" not in svg_text:
        raise RuntimeError(f"Themed SVG icon must use currentColor: {icon_name}")

    icon_color = _color_from_key(icon_color_key)
    themed_svg_text = svg_text.replace("currentColor", icon_color.name())
    pixmap = QtGui.QPixmap()
    if not pixmap.loadFromData(themed_svg_text.encode("utf-8")):
        raise RuntimeError(f"Themed SVG icon could not be rendered: {icon_name}")
    return QtGui.QIcon(pixmap)
