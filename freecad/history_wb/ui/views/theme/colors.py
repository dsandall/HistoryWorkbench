"""File responsibility: Shared Qt palette and color utilities for UI theme handling."""

from __future__ import annotations

from dataclasses import dataclass

from ....qt import QtGui


_ColorKey = tuple[int, int, int]
_PaletteKey = tuple[_ColorKey, _ColorKey, _ColorKey]

# Luminance below this value strongly suggests a dark item-view background.
_DARK_LUMINANCE_THRESHOLD = 0.35

# Luminance above this value strongly suggests light text. Combined with a dark
# background, this is the most reliable signal for dark FreeCAD stylesheets.
_LIGHT_TEXT_LUMINANCE_THRESHOLD = 0.65


@dataclass(frozen=True)
class _ThemeColors:
    """Palette colors used as stable inputs for theme-aware rendering."""

    base: QtGui.QColor
    text: QtGui.QColor
    window: QtGui.QColor


def _palette_theme_colors(palette: QtGui.QPalette) -> _ThemeColors:
    """Extract reliable palette colors for item-view backgrounds and text."""
    base = palette.color(QtGui.QPalette.ColorRole.Base)
    if not base.isValid():
        base = palette.color(QtGui.QPalette.ColorRole.Window)
    return _ThemeColors(
        base=base,
        text=palette.color(QtGui.QPalette.ColorRole.Text),
        window=palette.color(QtGui.QPalette.ColorRole.Window),
    )


def _theme_is_dark(palette: QtGui.QPalette) -> bool:
    """Return true when palette represents dark-theme item rendering."""
    return _theme_colors_are_dark(_palette_theme_colors(palette))


def _theme_colors_are_dark(colors: _ThemeColors) -> bool:
    """Return true when palette colors represent dark-theme item rendering.

    Some FreeCAD stylesheets report surprising Base colors for item views, so
    use base, window, and text luminance. A theme is dark only when item and
    window backgrounds are both dark and text is light. Light themes therefore
    keep dark monochrome icons even if one palette role misleads.
    """
    base_is_dark = _is_dark_color(colors.base)
    window_is_dark = _is_dark_color(colors.window)
    text_is_light = _relative_luminance(colors.text) > _LIGHT_TEXT_LUMINANCE_THRESHOLD
    return base_is_dark and window_is_dark and text_is_light


def _palette_key(palette: QtGui.QPalette) -> _PaletteKey:
    """Create hashable cache key from palette colors that affect output."""
    colors = _palette_theme_colors(palette)
    return _color_key(colors.base), _color_key(colors.text), _color_key(colors.window)


def _palette_from_key(key: _PaletteKey) -> QtGui.QPalette:
    """Build minimal palette from cache key for existing color helpers."""
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.ColorRole.Base, _color_from_key(key[0]))
    palette.setColor(QtGui.QPalette.ColorRole.Text, _color_from_key(key[1]))
    palette.setColor(QtGui.QPalette.ColorRole.Window, _color_from_key(key[2]))
    return palette


def _color_key(color: QtGui.QColor) -> _ColorKey:
    """Create hashable cache key for opaque RGB color values."""
    return color.red(), color.green(), color.blue()


def _color_from_key(key: _ColorKey) -> QtGui.QColor:
    """Recreate QColor from an RGB cache key."""
    red, green, blue = key
    return QtGui.QColor(red, green, blue)


def _is_dark_color(color: QtGui.QColor) -> bool:
    """Return true when color behaves like a dark theme background."""
    return _relative_luminance(color) < _DARK_LUMINANCE_THRESHOLD


def _blend_colors(base: QtGui.QColor, accent: QtGui.QColor, accent_ratio: float) -> QtGui.QColor:
    """Blend two RGB colors using accent_ratio as the accent weight."""
    base_ratio = 1.0 - accent_ratio
    return QtGui.QColor(
        round(base.red() * base_ratio + accent.red() * accent_ratio),
        round(base.green() * base_ratio + accent.green() * accent_ratio),
        round(base.blue() * base_ratio + accent.blue() * accent_ratio),
    )


def _contrast_ratio(foreground: QtGui.QColor, background: QtGui.QColor) -> float:
    """Calculate WCAG contrast ratio between two colors."""
    first = _relative_luminance(foreground)
    second = _relative_luminance(background)
    lighter = max(first, second)
    darker = min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def _relative_luminance(color: QtGui.QColor) -> float:
    """Calculate WCAG relative luminance for an sRGB color."""
    red = _linear_channel(color.redF())
    green = _linear_channel(color.greenF())
    blue = _linear_channel(color.blueF())
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _linear_channel(value: float) -> float:
    """Convert one sRGB color channel to linear-light value."""
    if value <= 0.03928:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4
