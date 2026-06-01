"""File responsibility: Document diff panel facade wiring summary, tree, document rows, and callbacks."""

from __future__ import annotations

from collections.abc import Callable

from ....qt import QtWidgets
from ...presenters.presentation_models import DiffTreePresentation
from ..history.models import HistorySelection
from .document_row import REMOVE_REVIEWED_TOOLTIP, DocumentDiffRowWidget
from .summary_bar import DocumentDiffSummaryBar
from .tree import DocumentDiffTree


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
        self._setup_ui()

    def _setup_ui(self) -> None:
        self._summary_bar = DocumentDiffSummaryBar(REMOVE_REVIEWED_TOOLTIP, self)
        self._summary_bar.stage_all_requested.connect(self._on_stage_all_clicked)
        self._summary_bar.restore_all_requested.connect(self._on_restore_all_clicked)
        self._summary_bar.remove_all_requested.connect(self._on_remove_all_clicked)
        self._tree = DocumentDiffTree(self)
        self._tree.node_selected.connect(self._on_tree_node_selected)
        self._tree.visual_diff_requested.connect(self._on_tree_visual_diff_requested)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._summary_bar)
        layout.addWidget(self._tree)

    def set_current_history_selection(self, selection: HistorySelection | None) -> None:
        """Set current history selection for conditional Current Files controls."""
        self._current_selection = selection

    def collapse_all_tree_items(self) -> None:
        """Collapse every document and node row in the tree."""
        self._tree.collapse_all_tree_items()

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

    def show_doc_diffs(self, diffs: list[DiffTreePresentation]) -> None:
        """Display multiple diff trees in the tree widget."""
        self._tree.clear()
        self._stage_buttons.clear()
        self._remove_from_reviewed_buttons.clear()

        # Empty document lists mean presenter wants a cleared middle column.
        if not diffs:
            return

        self._tree.show_doc_diffs(diffs, self._create_doc_row_widget)

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
        self._tree.clear()
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

    def _on_tree_node_selected(self, git_path: str, node_path: str) -> None:
        """Route child-tree node selection upward through stable callback setter."""

        # Callback stays optional while view protocol still bridges through setter adapters.
        if self._on_node_selection_callback is not None:
            self._on_node_selection_callback(git_path, node_path)

    def _on_tree_visual_diff_requested(self, git_path: str, node_path: str) -> None:
        """Route child-tree visual diff request upward through stable callback setter."""

        # Callback stays optional while presenter wiring still uses adapter setters.
        if self._on_visual_diff_callback is not None:
            self._on_visual_diff_callback(git_path, node_path)

    def collapse_tree_item(self, git_path: str) -> None:
        """Collapse the root tree item for the given git_path."""
        self._tree.collapse_tree_item(git_path)

    def set_stage_button_enabled(self, git_path: str, enabled: bool) -> None:
        """Enable or disable the + Reviewed button for a given git_path."""
        if git_path in self._stage_buttons:
            self._stage_buttons[git_path].setEnabled(enabled)
