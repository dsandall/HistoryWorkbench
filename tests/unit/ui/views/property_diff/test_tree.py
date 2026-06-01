"""File responsibility: Unit tests for PropertyDiffTreeWidget container behavior."""

from __future__ import annotations

from freecad.history_wb.domain.diff.models import DiffState
from freecad.history_wb.qt import QtWidgets
from freecad.history_wb.ui.presenters.presentation_models import PropertyPresentation
from freecad.history_wb.ui.views.property_diff.delegate import PropertyValueDelegate


def test_widget_has_three_columns(widget) -> None:  # type: ignore[no-untyped-def]
    """Property diff tree keeps 3-column layout."""
    assert widget.columnCount() == 3


def test_header_labels_are_correct(widget) -> None:  # type: ignore[no-untyped-def]
    """Property diff tree exposes expected translated headers."""
    assert widget.headerItem().text(0) == "Property"
    assert widget.headerItem().text(1) == "Old Value"
    assert widget.headerItem().text(2) == "New Value"


def test_widget_uses_selectable_read_only_delegate(widget) -> None:  # type: ignore[no-untyped-def]
    """Property diff tree wires extracted delegate as item delegate."""
    assert isinstance(widget.itemDelegate(), PropertyValueDelegate)


def test_empty_property_list_clears_tree(widget) -> None:  # type: ignore[no-untyped-def]
    """show_property_diff clears existing rows when given empty input."""
    widget.show_property_diff([PropertyPresentation(name="Length", state=DiffState.MODIFIED)])
    assert widget.topLevelItemCount() == 1

    widget.show_property_diff([])

    assert widget.topLevelItemCount() == 0


def test_clear_property_diff_removes_existing_rows(widget) -> None:  # type: ignore[no-untyped-def]
    """Explicit clear entry point removes rendered property rows."""
    widget.show_property_diff([PropertyPresentation(name="Length", state=DiffState.MODIFIED)])

    widget.clear_property_diff()

    assert widget.topLevelItemCount() == 0


def test_show_property_diff_renders_group_rows(widget) -> None:  # type: ignore[no-untyped-def]
    """Container renders grouped top-level items via extracted builders."""
    widget.show_property_diff(
        [
            PropertyPresentation(name="Length", state=DiffState.MODIFIED, group="Base"),
            PropertyPresentation(name="Width", state=DiffState.MODIFIED, group="Data"),
        ]
    )

    assert widget.topLevelItemCount() == 2
    assert widget.topLevelItem(0).text(0) == "Base"
    assert widget.topLevelItem(1).text(0) == "Data"


def test_tree_keeps_double_click_edit_trigger(widget) -> None:  # type: ignore[no-untyped-def]
    """Container keeps double-click text-selection trigger."""
    triggers = widget.editTriggers()
    assert bool(triggers & QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked)
