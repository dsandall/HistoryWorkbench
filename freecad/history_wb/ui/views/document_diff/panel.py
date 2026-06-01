"""File responsibility: Document diff panel facade with extracted summary, status, and document-row components."""

from __future__ import annotations

from collections.abc import Callable

from ....domain.diff.models import DiffState
from ....qt import QtCore, QtGui, QtWidgets
from ....resources import get_icon_path
from ....utils import translate
from ...presenters.presentation_models import DiffTreePresentation, NodePresentation
from ..history.models import HistorySelection
from ..theme.diff import DiffItemDelegate, apply_diff_state_to_item, apply_diff_state_to_widget
from ..widgets.buttons import make_icon_tool_button, make_tool_button
from ..widgets.styles import (
    DIFF_ROW_CONTAINER_OBJECT_NAME,
    DIFF_ROW_LABEL_OBJECT_NAME,
    TREE_ITEM_HEIGHT,
    TREE_ITEM_ICON_SIZE,
    VISUAL_DIFF_ICON_BUTTON_STYLE,
)
from .document_row import REMOVE_REVIEWED_TOOLTIP, DocumentDiffRowWidget
from .summary_bar import DocumentDiffSummaryBar


__all__ = ["DocumentDiffTreeWidget"]


class DocumentDiffTreeWidget(QtWidgets.QWidget):
    """Middle-column widget that renders document/node diffs and staging actions."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._on_add_button_callback: Callable[[str], None] | None = None
        self._on_stage_all_callback: Callable[[], None] | None = None
        self._on_remove_all_callback: Callable[[], None] | None = None
        self._on_restore_button_callback: Callable[[str], None] | None = None
        self._on_restore_all_callback: Callable[[], None] | None = None
        self._on_remove_from_reviewed_button_callback: Callable[[str], None] | None = None
        self._on_node_selection_callback: Callable[[str, str], None] | None = None
        self._current_selection: HistorySelection | None = None
        self._on_visual_diff_callback: Callable[[str, str], None] | None = None
        self._on_open_document_for_comparison_callback: Callable[[str], None] | None = None
        self._stage_buttons: dict[str, QtWidgets.QToolButton] = {}
        self._remove_from_reviewed_buttons: dict[str, QtWidgets.QToolButton] = {}
        self._diff_item_delegate: DiffItemDelegate | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        self._summary_bar = DocumentDiffSummaryBar(REMOVE_REVIEWED_TOOLTIP, self)
        self._summary_bar.stage_all_requested.connect(self._on_stage_all_clicked)
        self._summary_bar.restore_all_requested.connect(self._on_restore_all_clicked)
        self._summary_bar.remove_all_requested.connect(self._on_remove_all_clicked)

        tree_header = QtWidgets.QWidget()
        tree_header_layout = QtWidgets.QHBoxLayout(tree_header)
        tree_header_layout.setContentsMargins(4, 2, 4, 2)
        tree_header_layout.setSpacing(4)
        tree_header_layout.addWidget(QtWidgets.QLabel(translate("History", "Tree")))
        tree_header_layout.addStretch()

        self._collapse_all_button = make_icon_tool_button(
            icon_name="Collapse.svg",
            tooltip=translate("History", "Collapse All"),
            accessible_name=translate("History", "Collapse All"),
            size=TREE_ITEM_HEIGHT,
        )
        self._collapse_all_button.clicked.connect(self.collapse_all_tree_items)
        tree_header_layout.addWidget(self._collapse_all_button)

        self._tree_widget = QtWidgets.QTreeWidget()
        self._tree_widget.setObjectName("documentDiffTree")
        self._tree_widget.header().hide()
        self._tree_widget.setColumnCount(1)
        self._tree_widget.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self._diff_item_delegate = DiffItemDelegate(self._tree_widget)
        self._tree_widget.setItemDelegate(self._diff_item_delegate)
        self._tree_widget.itemClicked.connect(self._on_tree_item_clicked)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._summary_bar)
        layout.addWidget(tree_header)
        layout.addWidget(self._tree_widget)

    def set_current_history_selection(self, selection: HistorySelection | None) -> None:
        """Set current history selection for conditional Current Files controls."""
        self._current_selection = selection

    def collapse_all_tree_items(self) -> None:
        """Collapse every document and node row in the tree."""
        self._tree_widget.collapseAll()

    def set_node_selection_callback(self, callback: Callable[[str, str], None]) -> None:
        """Set callback for node selection with (git_path, node_path)."""
        self._on_node_selection_callback = callback

    def set_visual_diff_callback(self, callback: Callable[[str, str], None]) -> None:
        """Set callback for visual diff click with (git_path, node_path)."""
        self._on_visual_diff_callback = callback

    def set_open_document_for_comparison_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for open-document indicator click with git_path."""
        self._on_open_document_for_comparison_callback = callback

    def set_add_button_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for per-document + Reviewed button clicks."""
        self._on_add_button_callback = callback

    def set_stage_all_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for Mark All Reviewed button."""
        self._on_stage_all_callback = callback

    def set_remove_from_reviewed_button_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for Remove button in Reviewed selection."""
        self._on_remove_from_reviewed_button_callback = callback

    def set_stage_all_button_visible(self, visible: bool) -> None:
        """Show or hide Mark All Reviewed button."""
        self._summary_bar.set_stage_all_button_visible(visible)

    def set_stage_all_button_enabled(self, enabled: bool) -> None:
        """Enable or disable Mark All Reviewed button."""
        self._summary_bar.set_stage_all_button_enabled(enabled)

    def set_remove_all_button_visible(self, visible: bool) -> None:
        """Show or hide Remove All button for Reviewed selection."""
        self._summary_bar.set_remove_all_button_visible(visible)

    def set_remove_all_button_enabled(self, enabled: bool) -> None:
        """Enable or disable Remove All button for Reviewed selection."""
        self._summary_bar.set_remove_all_button_enabled(enabled)

    def set_remove_all_button_callback(self, callback: Callable[[], None]) -> None:
        """Set callback used by summary-bar Remove All button."""
        self._on_remove_all_callback = callback

    def set_restore_button_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for per-file Restore button."""
        self._on_restore_button_callback = callback

    def set_restore_all_button_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for summary-bar Restore All button."""
        self._on_restore_all_callback = callback

    def set_restore_all_button_visible(self, visible: bool) -> None:
        """Show or hide Restore All button."""
        self._summary_bar.set_restore_all_button_visible(visible)

    def set_restore_all_button_enabled(self, enabled: bool) -> None:
        """Enable or disable Restore All button."""
        self._summary_bar.set_restore_all_button_enabled(enabled)

    def show_doc_diff(self, nodes: list[NodePresentation], git_path: str = "") -> None:
        """Display the diff tree with color-coded nodes."""
        self._tree_widget.clear()

        # Empty node lists mean no displayable document tree for selection.
        if not nodes:
            return

        top_level_text = git_path or translate("History", "Unnamed Document")
        root_item = QtWidgets.QTreeWidgetItem([top_level_text])
        root_item.setSizeHint(0, QtCore.QSize(0, TREE_ITEM_HEIGHT))
        root_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, git_path or top_level_text)

        for node in nodes:
            self._add_tree_item(root_item, node, git_path)

        self._tree_widget.addTopLevelItem(root_item)
        self._expand_nodes_with_changes(root_item)
        self._tree_widget.show()

    def show_doc_diffs(self, diffs: list[DiffTreePresentation]) -> None:
        """Display multiple diff trees in the tree widget."""
        self._tree_widget.clear()
        self._stage_buttons.clear()
        self._remove_from_reviewed_buttons.clear()

        # Empty document lists mean presenter wants a cleared middle column.
        if not diffs:
            return

        for diff in diffs:
            top_level_text = diff.git_path or translate("History", "Unnamed Document")

            root_item = QtWidgets.QTreeWidgetItem([top_level_text])
            root_item.setSizeHint(0, QtCore.QSize(0, TREE_ITEM_HEIGHT))
            root_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, diff.git_path or top_level_text)
            self._apply_diff_state(root_item, diff.document_state)
            container = self._create_doc_row_widget(diff, top_level_text)
            self._apply_diff_state_to_widget(container, diff.document_state)

            self._tree_widget.addTopLevelItem(root_item)
            self._tree_widget.setItemWidget(root_item, 0, container)

            for node in diff.nodes:
                self._add_tree_item(root_item, node, diff.git_path)

            self._expand_nodes_with_changes(root_item)

        self._tree_widget.show()

    def _create_doc_row_widget(self, diff: DiffTreePresentation, top_level_text: str) -> DocumentDiffRowWidget:
        """Create top-level row widget for one document diff."""
        container = DocumentDiffRowWidget(diff, top_level_text, self._current_selection, self)
        container.stage_requested.connect(self._on_add_button_clicked)
        container.remove_from_reviewed_requested.connect(self._on_remove_from_reviewed_button_clicked)
        container.restore_requested.connect(self._on_restore_button_clicked)
        container.open_document_requested.connect(self._on_open_document_for_comparison_clicked)

        if diff.git_path and container.stage_button is not None:
            self._stage_buttons[diff.git_path] = container.stage_button

        if diff.git_path and container.remove_from_reviewed_button is not None:
            self._remove_from_reviewed_buttons[diff.git_path] = container.remove_from_reviewed_button

        return container

    def clear_doc_diffs(self) -> None:
        """Clear document diff tree and related controls."""
        self._tree_widget.clear()
        self._summary_bar.show_summary(0, 0, 0)
        self.set_stage_all_button_visible(False)
        self.set_stage_all_button_enabled(False)
        self.set_remove_all_button_visible(False)
        self.set_remove_all_button_enabled(False)
        self.set_restore_all_button_visible(False)
        self.set_restore_all_button_enabled(False)
        self._stage_buttons.clear()
        self._remove_from_reviewed_buttons.clear()

    def _on_open_document_for_comparison_clicked(self, git_path: str) -> None:
        """Invoke callback for open-document indicator click."""

        # Missing callback means presenter did not enable this affordance yet.
        if self._on_open_document_for_comparison_callback is not None:
            self._on_open_document_for_comparison_callback(git_path)

    def _on_add_button_clicked(self, git_path: str) -> None:
        """Handle + Reviewed button click by invoking callback."""

        # Row widgets always emit git_path; callback presence stays optional during wiring transition.
        if self._on_add_button_callback:
            self._on_add_button_callback(git_path)

    def _expand_nodes_with_changes(self, item: QtWidgets.QTreeWidgetItem) -> None:
        """Recursively expand nodes that have descendants with changes."""
        child_count = item.childCount()
        has_changed_descendants = False

        for i in range(child_count):
            child = item.child(i)
            has_changes = child.data(0, QtCore.Qt.ItemDataRole.UserRole + 1)
            if has_changes:
                has_changed_descendants = True
            self._expand_nodes_with_changes(child)

        # Expand only ancestor branches that lead to changed descendants.
        if has_changed_descendants:
            item.setExpanded(True)

    def _add_tree_item(self, parent: QtWidgets.QTreeWidgetItem, node: NodePresentation, git_path: str) -> None:
        """Create, attach, and install optional row widget for a node."""
        item, row_widget = self._create_tree_item(node, git_path)
        parent.addChild(item)
        if row_widget is not None:
            self._tree_widget.setItemWidget(item, 0, row_widget)

    def _create_tree_item(
        self,
        node: NodePresentation,
        git_path: str,
    ) -> tuple[QtWidgets.QTreeWidgetItem, QtWidgets.QWidget | None]:
        """Recursively create a QTreeWidgetItem from NodePresentation."""
        name = node.path.split("/")[-1] if node.path else ""
        text = node.label if node.label == name else f"{node.label} ({name})"

        item = QtWidgets.QTreeWidgetItem([text])
        item.setSizeHint(0, QtCore.QSize(0, TREE_ITEM_HEIGHT))
        item.setToolTip(0, node.type_id)
        item.setData(0, QtCore.Qt.ItemDataRole.UserRole, node.path)
        item.setData(0, QtCore.Qt.ItemDataRole.UserRole + 1, node.has_changes)

        self._apply_diff_state(item, node.state)

        row_widget = self._create_node_row_widget(item, node, text, git_path)
        if row_widget is not None:
            self._apply_diff_state_to_widget(row_widget, node.state)

        for child in node.children:
            self._add_tree_item(item, child, git_path)

        return item, row_widget

    def _create_node_row_widget(
        self, item: QtWidgets.QTreeWidgetItem, node: NodePresentation, text: str, git_path: str
    ) -> QtWidgets.QWidget | None:
        """Create optional custom row widget with right-floating visual diff icon."""

        # Phase 4a keeps visual-diff node rows owned by panel until 4b extraction.
        if not node.visual_diff_enabled:
            return None

        container = QtWidgets.QWidget()
        container.setObjectName(DIFF_ROW_CONTAINER_OBJECT_NAME)
        container.setFixedHeight(TREE_ITEM_HEIGHT)
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(4)
        label = QtWidgets.QLabel(text)
        label.setObjectName(DIFF_ROW_LABEL_OBJECT_NAME)
        label.setFixedHeight(TREE_ITEM_HEIGHT)
        label.setToolTip(node.type_id)
        layout.addWidget(label)
        layout.addStretch()

        icon_size = QtCore.QSize(TREE_ITEM_ICON_SIZE, TREE_ITEM_ICON_SIZE)

        button = make_tool_button(
            tooltip=translate("History", "Open 3D comparison"),
            icon=QtGui.QIcon(str(get_icon_path("VisualDiff.svg"))),
            width=TREE_ITEM_HEIGHT,
            height=TREE_ITEM_HEIGHT,
            style=VISUAL_DIFF_ICON_BUTTON_STYLE,
            auto_raise=True,
            icon_size=icon_size,
            tool_button_style=QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly,
        )
        button.clicked.connect(
            lambda checked=False, item=item, gp=git_path, np=node.path: self._on_visual_diff_clicked(item, gp, np)
        )
        layout.addWidget(button)
        return container

    def _apply_diff_state(self, item: QtWidgets.QTreeWidgetItem, state: DiffState) -> None:
        """Apply semantic diff coloring data to a tree item."""
        apply_diff_state_to_item(item, state, self._tree_widget.palette())

    def _apply_diff_state_to_widget(self, widget: QtWidgets.QWidget, state: DiffState) -> None:
        """Apply diff state colors to custom row widgets."""
        apply_diff_state_to_widget(
            widget,
            state,
            self._tree_widget.palette(),
            container_object_name=DIFF_ROW_CONTAINER_OBJECT_NAME,
            label_object_name=DIFF_ROW_LABEL_OBJECT_NAME,
        )

    def show_summary(self, modified_docs: int, deleted_docs: int, added_docs: int) -> None:
        """Display per-status document counts."""
        self._summary_bar.show_summary(modified_docs, deleted_docs, added_docs)

    def _on_stage_all_clicked(self) -> None:
        """Handle Stage All button click by invoking the callback."""
        if self._on_stage_all_callback:
            self._on_stage_all_callback()

    def _on_remove_all_clicked(self) -> None:
        """Handle summary-bar Remove All button click by invoking callback."""
        if self._on_remove_all_callback:
            self._on_remove_all_callback()

    def _on_remove_from_reviewed_button_clicked(self, git_path: str) -> None:
        """Handle Remove button click by invoking callback."""
        if self._on_remove_from_reviewed_button_callback is not None:
            self._on_remove_from_reviewed_button_callback(git_path)

    def _on_restore_button_clicked(self, git_path: str) -> None:
        """Handle Restore button click by invoking callback."""
        if self._on_restore_button_callback is not None:
            self._on_restore_button_callback(git_path)

    def _on_restore_all_clicked(self) -> None:
        """Handle Restore All button click by invoking callback."""
        if self._on_restore_all_callback is not None:
            self._on_restore_all_callback()

    def _on_tree_item_clicked(self, item: QtWidgets.QTreeWidgetItem, column: int) -> None:
        """Extract git_path from root and node_path from clicked item, then invoke callback."""
        if self._on_node_selection_callback is None:
            return

        node_path = item.data(0, QtCore.Qt.ItemDataRole.UserRole)

        root = item
        while root.parent():
            root = root.parent()
        git_path = root.data(0, QtCore.Qt.ItemDataRole.UserRole)

        # Root rows have git_path but no node_path. Ignore them for property selection routing.
        if git_path and node_path:
            self._on_node_selection_callback(git_path, node_path)

    def _on_visual_diff_clicked(self, item: QtWidgets.QTreeWidgetItem, git_path: str, node_path: str) -> None:
        """Select clicked node row, emit normal selection, then emit visual diff request."""
        self._tree_widget.setCurrentItem(item)
        self._on_tree_item_clicked(item, 0)
        if self._on_visual_diff_callback is not None:
            self._on_visual_diff_callback(git_path, node_path)

    def collapse_tree_item(self, git_path: str) -> None:
        """Collapse the root tree item for the given git_path."""
        for i in range(self._tree_widget.topLevelItemCount()):
            item = self._tree_widget.topLevelItem(i)
            item_git_path = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if item_git_path == git_path:
                item.setExpanded(False)
                break

    def set_stage_button_enabled(self, git_path: str, enabled: bool) -> None:
        """Enable or disable the + Reviewed button for a given git_path."""
        if git_path in self._stage_buttons:
            self._stage_buttons[git_path].setEnabled(enabled)
