"""File responsibility: History panel view facade with 3-column layout and dialog delegates."""

from collections.abc import Callable

from ....domain.git.models import GitCommit, GitRepository
from ....domain.settings import SettingsRepository
from ....qt import QtCore, QtWidgets
from ...presenters.presentation_models import (
    DiffTreePresentation,
    PropertyPresentation,
)
from ..document_diff.panel import DocumentDiffTreeWidget
from ..history.models import HistorySelection
from ..history.panel import HistoryPanelWidget
from ..property_diff_tree_widget import PropertyDiffTreeWidget
from .dialogs import (
    GitConfigDialogResult,
    show_configure_author_dialog,
    show_restore_file_confirmation_dialog,
    show_restore_scope_dialog,
    show_save_iteration_dialog,
)
from .messages import show_error_message, show_info_message, show_warning_message


__all__ = ["DiffPanelView"]


class DiffPanelView(QtWidgets.QWidget):
    """3-column diff panel view implementing DiffView protocol.

    Provides a horizontal QSplitter with:
    - Left: HistoryPanelWidget for repository info and history list
    - Middle: DocumentDiffTreeWidget for document diffs and staging
    - Right: PropertyDiffTreeWidget for property diffs

    Protocol Implementation:
        This class implements the DiffView protocol through
        structural subtyping (duck typing) rather than explicit inheritance to avoid
        metaclass conflicts between QWidget and Protocol classes.

        Implemented protocols:
        - DiffView (freecad.history_wb.ui.protocols.diff_view): show_doc_diffs,
          show_summary, show_property_diff, show_repository

    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        settings_repo: SettingsRepository | None = None,
    ) -> None:
        QtWidgets.QWidget.__init__(self, parent)
        self._settings_repo = settings_repo
        self._current_selection: HistorySelection | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Initialize the 3-column layout with child widgets."""
        layout = QtWidgets.QVBoxLayout(self)

        # Create horizontal splitter
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        # Column 1: History panel widget
        self._history_panel = HistoryPanelWidget(self)
        self._history_panel.set_effective_selection_changed_callback(self._on_history_panel_selection_changed)

        # Column 2: Document diff tree widget
        self._document_diff_tree = DocumentDiffTreeWidget(self)

        # Column 3: Property diff tree widget
        self._property_diff_tree = PropertyDiffTreeWidget(self, settings_repo=self._settings_repo)

        # Add to splitter
        splitter.addWidget(self._history_panel)
        splitter.addWidget(self._document_diff_tree)
        splitter.addWidget(self._property_diff_tree)

        # Set initial sizes: narrower history, narrower document diff, wider property table
        splitter.setSizes([150, 150, 400])

        # Set minimum size for the panel
        self.setMinimumSize(450, 200)

        layout.addWidget(splitter)

    def _on_history_panel_selection_changed(self, selection: HistorySelection | None) -> None:
        """Handle history panel selection changes to update document widget state."""
        self._current_selection = selection
        self._document_diff_tree.set_current_history_selection(selection)

    def show_commits(self, commits: list[GitCommit], show_special_items: bool = True) -> None:
        """Display git commits in the history list.

        Delegates to HistoryPanelWidget.

        Args:
            commits: List of GitCommit objects to display. Commits are shown
                in DESC order (newest first) with 7-char hash, author, timestamp
                on line 1, and first line of message on line 2. Full commit
                message is shown in tooltip.
            show_special_items: Whether to include top "Current Files" and
                "Reviewed" rows before commit rows.
        """
        self._history_panel.show_commits(commits, show_special_items=show_special_items)

    def append_commits(self, commits: list[GitCommit]) -> None:
        """Append commit entries after existing history rows.

        Delegates to HistoryPanelWidget.

        Args:
            commits: List of GitCommit objects to append.
        """
        self._history_panel.append_commits(commits)

    def set_refresh_callback(self, callback: Callable[[], None]) -> None:
        """Set the callback to invoke when refresh button is clicked.

        Delegates to HistoryPanelWidget.

        Args:
            callback: A no-argument callable to invoke on refresh.
        """
        self._history_panel.set_refresh_callback(callback)

    def set_save_iteration_callback(self, callback: Callable[[], None]) -> None:
        """Set callback fired by Save Iteration panel button."""
        self._history_panel.set_save_iteration_callback(callback)

    def set_user_history_selection_requested_callback(self, callback: Callable[[HistorySelection], None]) -> None:
        """Set callback for direct user-driven history selection requests.

        Delegates to HistoryPanelWidget.

        Args:
            callback: A callable that receives HistorySelection with item_kind and commit_hash
        """
        self._history_panel.set_user_history_selection_requested_callback(callback)

    def set_history_scroll_bottom_callback(self, callback: Callable[[], None]) -> None:
        """Set callback invoked when history list is near scroll bottom.

        Delegates to HistoryPanelWidget.
        """
        self._history_panel.set_history_scroll_bottom_callback(callback)

    def get_current_history_selection(self) -> HistorySelection | None:
        """Return currently selected history entry.

        Delegates to HistoryPanelWidget.
        """
        return self._history_panel.get_current_history_selection()

    def show_repository(self, repo: GitRepository | None) -> None:
        """Display git repository info above snapshot list.

        Delegates to HistoryPanelWidget.

        Args:
            repo: GitRepository object if detected, or None if no repository found.
                  If None, shows "No git repository detected".
        """
        self._history_panel.show_repository(repo)

    def set_add_button_callback(self, callback: Callable[[str], None]) -> None:
        """Set the callback for when the '+ Reviewed' button is clicked.

        Delegates to DocumentDiffTreeWidget.

        Args:
            callback: A callable that receives the git_path (str) of the
                      document whose '+ Reviewed' button was clicked.
        """
        self._document_diff_tree.set_add_button_callback(callback)

    def set_remove_from_reviewed_button_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for per-file Remove button in Reviewed view."""
        self._document_diff_tree.set_remove_from_reviewed_button_callback(callback)

    def set_remove_all_from_reviewed_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for Reviewed context action Remove All from Reviewed."""
        self._history_panel.set_remove_all_from_reviewed_callback(callback)

    def set_mark_all_reviewed_from_in_progress_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for Current Files context action Mark All Reviewed."""
        self._history_panel.set_mark_all_reviewed_from_in_progress_callback(callback)

    def set_restore_all_from_history_context_callback(self, callback: Callable[[HistorySelection], None]) -> None:
        """Set callback for restore actions from history context menu."""
        self._history_panel.set_restore_all_from_history_context_callback(callback)

    def set_stage_all_button_visible(self, visible: bool) -> None:
        """Show or hide the Mark All Reviewed button.

        Delegates to DocumentDiffTreeWidget.

        Args:
            visible: Whether the button should be visible.
        """
        self._document_diff_tree.set_stage_all_button_visible(visible)

    def set_stage_all_button_enabled(self, enabled: bool) -> None:
        """Enable or disable the Mark All Reviewed button.

        Delegates to DocumentDiffTreeWidget.

        Args:
            enabled: Whether the button should be enabled.
        """
        self._document_diff_tree.set_stage_all_button_enabled(enabled)

    def set_stage_all_callback(self, callback: Callable[[], None]) -> None:
        """Set the callback for Mark All Reviewed button.

        Delegates to DocumentDiffTreeWidget.

        Args:
            callback: A no-argument callable to invoke on click.
        """
        self._document_diff_tree.set_stage_all_callback(callback)

    def set_remove_all_button_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for summary-bar Remove All button."""
        self._document_diff_tree.set_remove_all_button_callback(callback)

    def set_remove_all_button_visible(self, visible: bool) -> None:
        """Show or hide summary-bar Remove All button."""
        self._document_diff_tree.set_remove_all_button_visible(visible)

    def set_remove_all_button_enabled(self, enabled: bool) -> None:
        """Enable or disable summary-bar Remove All button."""
        self._document_diff_tree.set_remove_all_button_enabled(enabled)

    def set_restore_button_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for per-file restore action."""
        self._document_diff_tree.set_restore_button_callback(callback)

    def set_restore_all_button_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for summary-bar restore-all action."""
        self._document_diff_tree.set_restore_all_button_callback(callback)

    def set_restore_all_button_visible(self, visible: bool) -> None:
        """Show or hide summary-bar restore-all button."""
        self._document_diff_tree.set_restore_all_button_visible(visible)

    def set_restore_all_button_enabled(self, enabled: bool) -> None:
        """Enable or disable summary-bar restore-all button."""
        self._document_diff_tree.set_restore_all_button_enabled(enabled)

    def set_node_selection_callback(self, callback: Callable[[str, str], None]) -> None:
        """Set callback for node selection with (git_path, node_path).

        Delegates to DocumentDiffTreeWidget.

        Args:
            callback: A callable receiving (git_path, node_path) when a node is clicked.
        """
        self._document_diff_tree.set_node_selection_callback(callback)

    def set_visual_diff_callback(self, callback: Callable[[str, str], None]) -> None:
        """Set callback for visual diff click with (git_path, node_path)."""
        self._document_diff_tree.set_visual_diff_callback(callback)

    def set_open_document_for_comparison_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for open-document indicator click with git_path."""
        self._document_diff_tree.set_open_document_for_comparison_callback(callback)

    def focus_window(self) -> None:
        """Bring the top-level history panel window to foreground."""
        window = self.window()
        window.show()
        window.raise_()
        window.activateWindow()
        window.setFocus()

    # DiffView protocol methods
    def show_doc_diffs(self, diffs: list[DiffTreePresentation]) -> None:
        """Display multiple diff trees in the tree widget.

        Delegates to DocumentDiffTreeWidget.

        Args:
            diffs: List of DiffTreePresentation objects, each representing
                  a diff tree for one document with its metadata.
        """
        self._document_diff_tree.set_current_history_selection(self._current_selection)
        self._document_diff_tree.show_doc_diffs(diffs)

    def clear_property_diff(self) -> None:
        """Clear property diff panel content."""
        self._property_diff_tree.clear_property_diff()

    def clear_doc_diffs(self) -> None:
        """Clear document diff tree and related controls.

        Also clears property diff panel to avoid stale node/property pairing.
        """
        self._document_diff_tree.clear_doc_diffs()
        self.clear_property_diff()

    def show_summary(self, modified_docs: int, deleted_docs: int, added_docs: int) -> None:
        """Display per-status document counts.

        Delegates to DocumentDiffTreeWidget.

        Args:
            modified_docs: Number of modified documents.
            deleted_docs: Number of deleted documents.
            added_docs: Number of added documents.
        """
        self._document_diff_tree.show_summary(modified_docs, deleted_docs, added_docs)

    def show_property_diff(self, properties: list[PropertyPresentation]) -> None:
        """Display property diffs in the properties tree widget.

        Delegates to the child PropertyDiffTreeWidget.

        Args:
            properties: List of PropertyPresentation objects to display.
        """
        self._property_diff_tree.show_property_diff(properties)

    def collapse_tree_item(self, git_path: str) -> None:
        """Collapse the root tree item for the given git_path.

        Delegates to DocumentDiffTreeWidget.

        Args:
            git_path: The git_path of the root tree item to collapse.
        """
        self._document_diff_tree.collapse_tree_item(git_path)

    def set_stage_button_enabled(self, git_path: str, enabled: bool) -> None:
        """Enable or disable the '+ Reviewed' button for a given git_path.

        Delegates to DocumentDiffTreeWidget.

        Args:
            git_path: The git_path of the document whose button to update.
            enabled: Whether the reviewed button should be enabled.
        """
        self._document_diff_tree.set_stage_button_enabled(git_path, enabled)

    def show_warning_message(self, title: str, message: str) -> None:
        """Show warning dialog."""
        show_warning_message(self, title, message)

    def show_info_message(self, title: str, message: str) -> None:
        """Show informational dialog."""
        show_info_message(self, title, message)

    def show_error_message(self, title: str, message: str) -> None:
        """Show error dialog."""
        show_error_message(self, title, message)

    def show_save_iteration_dialog(self) -> str | None:
        """Show Save Iteration dialog and return notes when accepted."""
        return show_save_iteration_dialog(self)

    def show_configure_author_dialog(
        self,
        *,
        message: str | None = None,
        initial_values: GitConfigDialogResult | None = None,
        global_config_writable: bool = True,
    ) -> GitConfigDialogResult | None:
        """Show configure-author dialog and return entered values."""
        return show_configure_author_dialog(
            self,
            message=message,
            initial_values=initial_values,
            global_config_writable=global_config_writable,
        )

    def show_restore_file_confirmation_dialog(self, git_path: str) -> bool:
        """Show destructive confirmation dialog for file restore."""
        return show_restore_file_confirmation_dialog(self, git_path)

    def show_restore_scope_dialog(self) -> str | None:
        """Show bulk scope picker for restore-all action."""
        return show_restore_scope_dialog(self)
