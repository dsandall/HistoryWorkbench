"""File responsibility: Build grouped property diff tree items and expansion state."""

from __future__ import annotations

from ....domain.diff.models import DiffState
from ....qt import QtCore, QtGui, QtWidgets
from ....utils import translate
from ...presenters.presentation_models import PropertyPresentation
from ..theme.diff import apply_diff_state_to_item, background_for_state, foreground_for_background
from .formatters import build_property_tooltip, camelcase_to_spaces, get_property_display_values


__all__ = ["apply_stored_expansion_state", "build_grouped_property_items"]


_EXPAND_STATE_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1


def build_grouped_property_items(
    properties: list[PropertyPresentation],
    palette: QtGui.QPalette,
    precision: int,
) -> list[QtWidgets.QTreeWidgetItem]:
    """Build grouped top-level tree items for property diff rendering."""
    groups: dict[str, list[PropertyPresentation]] = {}
    for prop in properties:
        group_name = getattr(prop, "group", None) or translate("History", "Properties")
        groups.setdefault(group_name, []).append(prop)

    items: list[QtWidgets.QTreeWidgetItem] = []
    for group_name in sorted(groups.keys()):
        group_item = _create_group_header_item(group_name, palette)
        for prop in groups[group_name]:
            group_item.addChild(_build_property_tree_item(prop, palette, precision))
        group_item.setExpanded(True)
        items.append(group_item)

    return items


def _create_group_header_item(group_name: str, palette: QtGui.QPalette) -> QtWidgets.QTreeWidgetItem:
    """Create one non-selectable group header row."""
    item = QtWidgets.QTreeWidgetItem([group_name, "", ""])
    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsSelectable)
    _apply_group_header_colors(item, palette)

    font = item.font(0)
    font.setBold(True)
    item.setFont(0, font)
    item.setFont(1, font)
    item.setFont(2, font)
    return item


def _build_property_tree_item(
    prop: PropertyPresentation,
    palette: QtGui.QPalette,
    precision: int,
) -> QtWidgets.QTreeWidgetItem:
    """Build one property tree row and all descendants."""
    left_value, right_value = get_property_display_values(
        prop.state,
        old_value=prop.old_value,
        new_value=prop.new_value,
        precision=precision,
    )
    item = QtWidgets.QTreeWidgetItem([camelcase_to_spaces(prop.name), left_value, right_value])
    item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)

    tooltip = build_property_tooltip(left_value, right_value)
    for column in range(3):
        item.setToolTip(column, tooltip)

    item.setData(0, _EXPAND_STATE_ROLE, _presentation_has_changes(prop))
    for child in prop.children:
        item.addChild(_build_property_tree_item(child, palette, precision))

    _apply_property_diff_state(item, prop.state, palette)
    return item


def _presentation_has_changes(prop: PropertyPresentation) -> bool:
    """Return whether property or any descendant carries a changed diff state."""
    if prop.state != DiffState.UNCHANGED:
        return True
    return any(_presentation_has_changes(child) for child in prop.children)


def _apply_property_diff_state(
    item: QtWidgets.QTreeWidgetItem,
    state: DiffState,
    palette: QtGui.QPalette,
) -> None:
    """Apply semantic diff colors to all visible property columns."""
    background = background_for_state(state, palette)
    if background is None:
        return
    apply_diff_state_to_item(item, state, palette, columns=range(3))


def _apply_group_header_colors(item: QtWidgets.QTreeWidgetItem, palette: QtGui.QPalette) -> None:
    """Apply theme-aware header colors for one property group row."""
    background = palette.color(QtGui.QPalette.ColorRole.AlternateBase)

    # Some themes collapse AlternateBase into Base. Fall back to Button for contrast.
    if not background.isValid() or background == palette.color(QtGui.QPalette.ColorRole.Base):
        background = palette.color(QtGui.QPalette.ColorRole.Button)

    foreground = foreground_for_background(background, palette)
    for column in range(3):
        item.setBackground(column, QtGui.QBrush(background))
        item.setForeground(column, QtGui.QBrush(foreground))


def apply_stored_expansion_state(items: list[QtWidgets.QTreeWidgetItem]) -> None:
    """Apply stored expansion flags after whole tree structure exists."""
    for item in items:
        item.setExpanded(True)
        _apply_expansion_recursive(item)


def _apply_expansion_recursive(item: QtWidgets.QTreeWidgetItem) -> None:
    """Apply expansion flag to one item and all descendants."""
    if item.data(0, _EXPAND_STATE_ROLE):
        item.setExpanded(True)
    for index in range(item.childCount()):
        _apply_expansion_recursive(item.child(index))
