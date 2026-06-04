"""File responsibility: Build document diff QTreeWidgetItem hierarchies from presentation models."""

from __future__ import annotations

from ....domain.diff.models import DiffState
from ....qt import QtCore, QtGui, QtWidgets
from ....utils import translate
from ...presenters.presentation_models import NodePresentation
from ..theme.diff import apply_diff_state_to_item
from ..widgets.styles import TREE_ITEM_HEIGHT


__all__ = ["build_document_root_item", "build_node_item"]


def build_document_root_item(
    display_text: str,
    git_path: str,
    palette: QtGui.QPalette,
    *,
    document_state: DiffState | None = None,
) -> QtWidgets.QTreeWidgetItem:
    """Create one top-level document item with optional diff-state data."""
    root_item = QtWidgets.QTreeWidgetItem([display_text or translate("History", "Unnamed Document")])
    root_item.setSizeHint(0, QtCore.QSize(0, TREE_ITEM_HEIGHT))
    root_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, git_path or display_text)

    # Document rows only store semantic color role when presenter says document state differs.
    if document_state is not None:
        apply_diff_state_to_item(root_item, document_state, palette)

    return root_item


def build_node_item(node: NodePresentation, palette: QtGui.QPalette) -> QtWidgets.QTreeWidgetItem:
    """Recursively build one node subtree and attach semantic diff-state data."""
    name = node.path.split("/")[-1] if node.path else ""
    text = node.label if node.label == name else f"{node.label} ({name})"

    item = QtWidgets.QTreeWidgetItem([text])
    item.setSizeHint(0, QtCore.QSize(0, TREE_ITEM_HEIGHT))
    item.setToolTip(0, node.type_id)
    item.setData(0, QtCore.Qt.ItemDataRole.UserRole, node.path)
    item.setData(0, QtCore.Qt.ItemDataRole.UserRole + 1, node.has_changes)
    apply_diff_state_to_item(item, node.state, palette)

    for child in node.children:
        item.addChild(build_node_item(child, palette))

    return item
