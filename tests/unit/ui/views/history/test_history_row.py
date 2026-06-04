"""File responsibility: Unit tests for history row widget builders and rendering."""

from __future__ import annotations

from freecad.history_wb.qt import QtCore, QtWidgets
from freecad.history_wb.ui.views.history.formatters import format_commit_timestamp
from freecad.history_wb.ui.views.history.history_row import (
    HistoryListItemWidget,
    create_commit_history_item,
    create_no_iterations_history_item,
    create_special_history_item,
)
from freecad.history_wb.ui.views.history.models import HistorySelection

from .conftest import history_row_text, make_commit


def test_create_special_history_item_builds_centered_selection_row() -> None:
    """Special-item builder stores HistorySelection and centered text."""
    selection = HistorySelection(item_kind="WORKING_TREE", commit_hash=None)
    item, widget = create_special_history_item("Current Files", selection)

    assert item.data(QtCore.Qt.ItemDataRole.UserRole) == selection
    assert item.data(QtCore.Qt.ItemDataRole.TextAlignmentRole) == QtCore.Qt.AlignmentFlag.AlignCenter
    assert history_row_text(_list_with_widget(item, widget), 0) == "Current Files"


def test_create_no_iterations_history_item_builds_italic_placeholder() -> None:
    """Placeholder builder renders italic empty-history row."""
    item, widget = create_no_iterations_history_item("No iterations to display.")
    labels = widget.findChildren(QtWidgets.QLabel)

    assert item.data(QtCore.Qt.ItemDataRole.TextAlignmentRole) == QtCore.Qt.AlignmentFlag.AlignCenter
    assert len(labels) == 1
    assert labels[0].text() == "No iterations to display."
    assert "italic" in labels[0].styleSheet()


def test_create_commit_history_item_formats_two_line_row() -> None:
    """Commit-row builder renders hash author timestamp plus subject line."""
    commit = make_commit(
        commit_id="abc123def456",
        message="This is the subject line\n\nBody text",
        author="Alice Smith",
        timestamp="2024-03-20T14:45:00+00:00",
    )
    item, widget = create_commit_history_item(commit)
    list_widget = _list_with_widget(item, widget)
    text = history_row_text(list_widget, 0)
    lines = text.split("\n")

    assert item.toolTip() == commit.message
    assert item.data(QtCore.Qt.ItemDataRole.UserRole) == HistorySelection(item_kind="COMMIT", commit_hash=commit.id)
    assert len(lines) == 2
    assert "abc123d" in lines[0]
    assert "Alice Smith" in lines[0]
    assert format_commit_timestamp(commit.timestamp) in lines[0]
    assert lines[1] == "This is the subject line"


def test_create_commit_history_item_truncates_hash_and_preserves_long_message() -> None:
    """Commit-row builder truncates hash and keeps long subject text."""
    commit = make_commit(
        commit_id="a1b2c3d4e5f6789012345678901234567890abcd",
        message="A" * 200,
    )
    item, widget = create_commit_history_item(commit)
    list_widget = _list_with_widget(item, widget)
    text = history_row_text(list_widget, 0)

    assert "a1b2c3d" in text
    assert "e5f6789" not in text
    assert "A" * 100 in text


def test_create_commit_history_item_strips_empty_or_whitespace_subject() -> None:
    """Commit-row builder renders blank second line for empty subject."""
    empty_item, empty_widget = create_commit_history_item(make_commit(message=""))
    whitespace_item, whitespace_widget = create_commit_history_item(make_commit(message="   \n\n   "))
    empty_list = _list_with_widget(empty_item, empty_widget)
    whitespace_list = _list_with_widget(whitespace_item, whitespace_widget)

    assert history_row_text(empty_list, 0).split("\n")[1] == ""
    assert history_row_text(whitespace_list, 0).split("\n")[1] == ""


def test_history_list_item_widget_can_render_bold_bottom_text() -> None:
    """Row widget applies bold style to bottom label when requested."""
    widget = HistoryListItemWidget(bottom_text="Important", is_bottom_bold=True)
    labels = widget.findChildren(QtWidgets.QLabel)

    assert any(label.text() == "Important" and "font-weight: 700" in label.styleSheet() for label in labels)


def _list_with_widget(item: QtWidgets.QListWidgetItem, widget: QtWidgets.QWidget) -> QtWidgets.QListWidget:
    """Build temporary QListWidget for shared row-text helper."""
    list_widget = QtWidgets.QListWidget()
    list_widget.addItem(item)
    list_widget.setItemWidget(item, widget)
    return list_widget
