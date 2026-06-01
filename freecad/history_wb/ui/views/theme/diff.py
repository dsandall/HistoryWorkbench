"""File responsibility: Theme-aware diff item coloring for Qt tree views."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, cast

from ....domain.diff.models import DiffState
from ....qt import QtCore, QtGui, QtWidgets
from .colors import (
    _blend_colors,
    _color_from_key,
    _color_key,
    _ColorKey,
    _contrast_ratio,
    _palette_from_key,
    _palette_key,
    _palette_theme_colors,
    _PaletteKey,
    _theme_is_dark,
)


__all__ = [
    "DIFF_STATE_ROLE",
    "DiffItemDelegate",
    "background_for_state",
    "foreground_for_background",
]


# Custom model role used by DiffItemDelegate. Qt's built-in BackgroundRole can be
# ignored by aggressive application stylesheets, so we store semantic state and
# let the delegate paint it directly.
DIFF_STATE_ROLE = QtCore.Qt.ItemDataRole.UserRole + 20

# Minimum contrast target for normal-sized UI text. This follows the WCAG AA
# 4.5:1 guidance and keeps diff labels readable across light and dark themes.
_MIN_CONTRAST = 4.5

# First-pass accent blend for dark themes. Light themes use direct pastel
# colors so they match the original bright diff highlights with black text.
_DARK_ACCENT_BLEND = 0.38

# Fallback blend ratios move gradually toward pure accent color until the chosen
# text color reaches the contrast target.
_CONTRAST_FALLBACK_BLEND_RATIOS = (0.45, 0.52, 0.60, 0.70, 0.82, 1.0)
_LAST_FALLBACK_BLEND = 0.52

# Diff accents are paired as (light-theme accent, dark-theme accent). Light
# variants preserve the original bright pastel highlights. Dark variants are
# brighter saturated targets so they remain visible when blended into dark
# palettes.
_ADDED_LIGHT_ACCENT = QtGui.QColor(200, 255, 200)
_ADDED_DARK_ACCENT = QtGui.QColor(48, 219, 91)
_DELETED_LIGHT_ACCENT = QtGui.QColor(255, 200, 200)
_DELETED_DARK_ACCENT = QtGui.QColor(255, 105, 97)
_MODIFIED_LIGHT_ACCENT = QtGui.QColor(200, 200, 255)
_MODIFIED_DARK_ACCENT = QtGui.QColor(116, 192, 252)


class DiffItemDelegate(QtWidgets.QStyledItemDelegate):
    """Paint diff item backgrounds with contrast-safe foreground colors."""

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> None:  # type: ignore[override]
        """Paint one tree cell using semantic diff colors when present."""
        state = index.data(DIFF_STATE_ROLE)
        if not isinstance(state, DiffState):
            super().paint(painter, option, index)
            return

        themed_option = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(themed_option, index)

        # PySide exposes these attributes at runtime, but current stubs omit
        # them. Keep the cast local so the rest of the module remains typed.
        themed_option_data = cast(Any, themed_option)
        background = background_for_state(state, themed_option_data.palette)
        if background is None:
            super().paint(painter, option, index)
            return

        foreground = foreground_for_background(background, themed_option_data.palette)

        # Set both background and text roles on the style option. This lets the
        # current Qt style keep selection, padding, icons, and branch painting
        # while overriding only diff-specific colors.
        themed_option_data.backgroundBrush = QtGui.QBrush(background)
        themed_option_data.palette.setColor(QtGui.QPalette.ColorRole.Text, foreground)
        themed_option_data.palette.setColor(QtGui.QPalette.ColorRole.WindowText, foreground)
        themed_option_data.palette.setColor(QtGui.QPalette.ColorRole.Highlight, background)
        themed_option_data.palette.setColor(QtGui.QPalette.ColorRole.HighlightedText, foreground)
        super().paint(painter, themed_option, index)


def background_for_state(state: DiffState, palette: QtGui.QPalette) -> QtGui.QColor | None:
    """Return theme-aware background color for diff state.

    Unchanged rows return None so they inherit the normal theme background.
    """
    palette_cache_key = _palette_key(palette)
    return _cached_background_for_state(state, palette_cache_key)


@lru_cache(maxsize=96)
def _cached_background_for_state(state: DiffState, palette_cache_key: _PaletteKey) -> QtGui.QColor | None:
    """Return cached background for state and palette colors.

    Painting can call this once per visible cell, while many cells share the
    same application palette and diff state. Cache prevents repeating WCAG math.
    """
    palette = _palette_from_key(palette_cache_key)
    if state == DiffState.ADDED:
        return _state_background(palette, _ADDED_LIGHT_ACCENT, _ADDED_DARK_ACCENT)
    if state == DiffState.DELETED:
        return _state_background(palette, _DELETED_LIGHT_ACCENT, _DELETED_DARK_ACCENT)
    if state == DiffState.MODIFIED:
        return _state_background(palette, _MODIFIED_LIGHT_ACCENT, _MODIFIED_DARK_ACCENT)
    return None


def foreground_for_background(background: QtGui.QColor, palette: QtGui.QPalette) -> QtGui.QColor:
    """Return readable text color for a background and current palette.

    Prefer the theme text color when possible, then fall back to black or white.
    """
    return _cached_foreground_for_background(_color_key(background), _palette_key(palette))


@lru_cache(maxsize=256)
def _cached_foreground_for_background(background_key: _ColorKey, palette_cache_key: _PaletteKey) -> QtGui.QColor:
    """Return cached foreground for background and palette colors."""
    background = _color_from_key(background_key)
    palette = _palette_from_key(palette_cache_key)
    if not _theme_is_dark(palette):
        return QtGui.QColor(0, 0, 0)

    palette_text = _color_from_key(palette_cache_key[1])
    black = QtGui.QColor(0, 0, 0)
    white = QtGui.QColor(255, 255, 255)
    candidates = [palette_text, black, white]
    best = max(candidates, key=lambda color: _contrast_ratio(color, background))
    if _contrast_ratio(best, background) >= _MIN_CONTRAST:
        return best
    return black if _contrast_ratio(black, background) > _contrast_ratio(white, background) else white


def _state_background(palette: QtGui.QPalette, light_accent: QtGui.QColor, dark_accent: QtGui.QColor) -> QtGui.QColor:
    """Blend state accent with theme base and adjust until text is readable."""
    colors = _palette_theme_colors(palette)
    if _theme_is_dark(palette):
        accent = dark_accent
        initial = _blend_colors(colors.base, accent, _DARK_ACCENT_BLEND)
    else:
        accent = light_accent
        initial = light_accent
    foreground = foreground_for_background(initial, palette)
    if _contrast_ratio(foreground, initial) >= _MIN_CONTRAST:
        return initial
    return _find_contrast_background(colors.base, accent, foreground)


def _find_contrast_background(base: QtGui.QColor, accent: QtGui.QColor, foreground: QtGui.QColor) -> QtGui.QColor:
    """Try stronger accent blends until foreground contrast is sufficient."""
    for ratio in _CONTRAST_FALLBACK_BLEND_RATIOS:
        candidate = _blend_colors(base, accent, ratio)
        if _contrast_ratio(foreground, candidate) >= _MIN_CONTRAST:
            return candidate
    return _blend_colors(base, accent, _LAST_FALLBACK_BLEND)
