"""File responsibility: Summary bar widget for document diff counts and bulk actions."""

from __future__ import annotations

from ....qt import QtCore, QtWidgets
from ....utils import translate
from ..widgets.buttons import make_tool_button
from ..widgets.styles import TREE_ITEM_HEIGHT
from .summary_state import SummaryButtonState, SummaryCounts


STAGE_ALL_BUTTON_WIDTH = 140


class DocumentDiffSummaryBar(QtWidgets.QWidget):
    """Render document counts and bulk document action buttons."""

    stage_all_requested = QtCore.Signal()
    restore_all_requested = QtCore.Signal()
    remove_all_requested = QtCore.Signal()

    def __init__(self, remove_reviewed_tooltip: str, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._remove_reviewed_tooltip = remove_reviewed_tooltip
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self._changed_label = QtWidgets.QLabel("")
        self._changed_label.setObjectName("documentDiffSummaryLabel")
        self._changed_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self._changed_label)

        self._stage_all_button = make_tool_button(
            text=translate("History", "+ Mark All Reviewed"),
            width=STAGE_ALL_BUTTON_WIDTH,
            height=TREE_ITEM_HEIGHT,
        )
        self._stage_all_button.setObjectName("documentDiffStageAllButton")
        self._stage_all_button.hide()
        self._stage_all_button.clicked.connect(self.stage_all_requested.emit)
        layout.addWidget(self._stage_all_button)

        self._restore_all_button = make_tool_button(
            text=translate("History", "Restore All"),
            tooltip=translate(
                "History",
                "Choose which files to restore from the selected iteration.\n"
                "Current files on disk can be overwritten or removed.\n"
                "Saved history will not be affected.",
            ),
            height=TREE_ITEM_HEIGHT,
        )
        self._restore_all_button.setObjectName("documentDiffRestoreAllButton")
        self._restore_all_button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        self._restore_all_button.hide()
        self._restore_all_button.clicked.connect(self.restore_all_requested.emit)
        layout.addWidget(self._restore_all_button)

        self._remove_all_button = make_tool_button(
            text=translate("History", "Remove All"),
            tooltip=self._remove_reviewed_tooltip,
            height=TREE_ITEM_HEIGHT,
        )
        self._remove_all_button.setObjectName("documentDiffRemoveAllButton")
        self._remove_all_button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        self._remove_all_button.hide()
        self._remove_all_button.clicked.connect(self.remove_all_requested.emit)
        layout.addWidget(self._remove_all_button)

    def set_summary_counts(self, counts: SummaryCounts) -> None:
        """Display per-status document counts."""
        if (counts.modified_docs + counts.deleted_docs + counts.added_docs) == 0:
            self._changed_label.setText(translate("History", "No changes"))
            return

        modified_text = translate("History", "Modified:")
        deleted_text = translate("History", "Deleted:")
        added_text = translate("History", "Added:")
        self._changed_label.setText(
            f"{modified_text} {counts.modified_docs}  "
            f"{deleted_text} {counts.deleted_docs}  "
            f"{added_text} {counts.added_docs}"
        )

    def set_button_states(self, state: SummaryButtonState) -> None:
        """Apply visibility and enabled state for all bulk action buttons."""
        self._stage_all_button.setVisible(state.stage_all_visible)
        self._stage_all_button.setEnabled(state.stage_all_enabled)
        self._remove_all_button.setVisible(state.remove_all_visible)
        self._remove_all_button.setEnabled(state.remove_all_enabled)
        self._restore_all_button.setVisible(state.restore_all_visible)
        self._restore_all_button.setEnabled(state.restore_all_enabled)
