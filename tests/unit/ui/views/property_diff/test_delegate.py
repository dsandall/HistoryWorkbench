"""File responsibility: Unit tests for extracted property diff item delegate."""

from __future__ import annotations

from freecad.history_wb.qt import QtCore, QtGui, QtWidgets
from freecad.history_wb.ui.views.property_diff.delegate import PropertyValueDelegate


def test_create_editor_builds_borderless_line_edit() -> None:
    """Delegate creates borderless line edit aligned for row text."""
    parent = QtWidgets.QWidget()
    delegate = PropertyValueDelegate(parent)
    option = QtWidgets.QStyleOptionViewItem()
    model = QtGui.QStandardItemModel(1, 1)
    index = model.index(0, 0)

    editor = delegate.createEditor(parent, option, index)

    assert isinstance(editor, QtWidgets.QLineEdit)
    assert not editor.hasFrame()
    assert editor.alignment() == (
        QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignLeft
    )


def test_set_editor_data_populates_text_and_selects_all() -> None:
    """Delegate copies display text into editor and selects all text."""
    parent = QtWidgets.QWidget()
    delegate = PropertyValueDelegate(parent)
    model = QtGui.QStandardItemModel(1, 1)
    model.setData(model.index(0, 0), "Length", QtCore.Qt.ItemDataRole.DisplayRole)
    editor = QtWidgets.QLineEdit(parent)

    delegate.setEditorData(editor, model.index(0, 0))

    assert editor.text() == "Length"
    assert editor.selectedText() == "Length"


def test_set_model_data_keeps_model_read_only() -> None:
    """Delegate ignores editor writes so backing model data stays unchanged."""
    parent = QtWidgets.QWidget()
    delegate = PropertyValueDelegate(parent)
    model = QtGui.QStandardItemModel(1, 1)
    model.setData(model.index(0, 0), "Original", QtCore.Qt.ItemDataRole.DisplayRole)
    editor = QtWidgets.QLineEdit(parent)
    editor.setText("Updated")

    delegate.setModelData(editor, model, model.index(0, 0))

    assert model.data(model.index(0, 0), QtCore.Qt.ItemDataRole.DisplayRole) == "Original"


def test_update_editor_geometry_matches_item_rect() -> None:
    """Delegate positions editor over cell rectangle."""
    parent = QtWidgets.QWidget()
    delegate = PropertyValueDelegate(parent)
    editor = QtWidgets.QLineEdit(parent)
    option = QtWidgets.QStyleOptionViewItem()
    option.rect = QtCore.QRect(5, 7, 80, 20)
    model = QtGui.QStandardItemModel(1, 1)

    delegate.updateEditorGeometry(editor, option, model.index(0, 0))

    assert editor.geometry() == option.rect
