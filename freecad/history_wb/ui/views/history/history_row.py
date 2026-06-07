"""File responsibility: History row widgets and QListWidgetItem builders."""

from ....domain.git.models import GitCommit
from ....qt import QtCore, QtWidgets
from .formatters import format_commit_timestamp
from .models import HistorySelection


class HistoryListItemWidget(QtWidgets.QWidget):
    """Render formatted history-list row content."""

    def __init__(
        self,
        *,
        left_text: str = "",
        center_text: str = "",
        right_text: str = "",
        bottom_text: str = "",
        is_bottom_bold: bool = False,
        centered_text: str | None = None,
        centered_italic: bool = False,
    ) -> None:
        super().__init__()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 0)
        layout.setSpacing(6)

        if centered_text is not None:
            centered_label = QtWidgets.QLabel(centered_text)
            centered_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

            # Placeholder rows need visual distinction from commit rows.
            if centered_italic:
                centered_label.setStyleSheet("font-style: italic;")

            layout.addWidget(centered_label)
        else:
            top_row = QtWidgets.QHBoxLayout()
            top_row.setContentsMargins(0, 0, 0, 0)
            top_row.setSpacing(8)

            left_label = QtWidgets.QLabel(left_text)
            left_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
            left_label.setStyleSheet("font-weight: 700;")

            center_label = QtWidgets.QLabel(center_text)
            center_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

            right_label = QtWidgets.QLabel(right_text)
            right_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)

            top_row.addWidget(left_label, 1)
            top_row.addWidget(center_label, 1)
            top_row.addWidget(right_label, 1)
            layout.addLayout(top_row)

            bottom_label = QtWidgets.QLabel(bottom_text)
            bottom_label.setWordWrap(True)
            bottom_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)

            if is_bottom_bold:
                bottom_label.setStyleSheet("font-weight: 700;")

            layout.addWidget(bottom_label)

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: black;")
        layout.addWidget(separator)


def create_special_history_item(
    text: str, selection: HistorySelection
) -> tuple[QtWidgets.QListWidgetItem, QtWidgets.QWidget]:
    """Create Current Files Area or Reviewed Area pseudo-row."""
    item = QtWidgets.QListWidgetItem(text)
    item.setData(QtCore.Qt.ItemDataRole.TextAlignmentRole, QtCore.Qt.AlignmentFlag.AlignCenter)
    item.setData(QtCore.Qt.ItemDataRole.UserRole, selection)
    return item, HistoryListItemWidget(centered_text=text)


def create_no_iterations_history_item(text: str) -> tuple[QtWidgets.QListWidgetItem, QtWidgets.QWidget]:
    """Create italic placeholder row shown when commit history is empty."""
    item = QtWidgets.QListWidgetItem(text)
    item.setData(QtCore.Qt.ItemDataRole.TextAlignmentRole, QtCore.Qt.AlignmentFlag.AlignCenter)
    return item, HistoryListItemWidget(centered_text=text, centered_italic=True)


def create_commit_history_item(commit: GitCommit) -> tuple[QtWidgets.QListWidgetItem, QtWidgets.QWidget]:
    """Create formatted commit row item and widget."""
    short_hash = commit.id[:7] if len(commit.id) >= 7 else commit.id
    timestamp_str = format_commit_timestamp(commit.timestamp)
    first_line = commit.message.split("\n")[0].strip() if commit.message and commit.message.strip() else ""
    display_text = f"{short_hash} {commit.author} {timestamp_str}\n{first_line}"

    item = QtWidgets.QListWidgetItem(display_text)
    item.setToolTip(commit.message)
    item.setData(QtCore.Qt.ItemDataRole.TextAlignmentRole, QtCore.Qt.AlignmentFlag.AlignLeft)
    item.setData(QtCore.Qt.ItemDataRole.UserRole, HistorySelection(item_kind="COMMIT", commit_hash=commit.id))

    widget = HistoryListItemWidget(
        left_text=short_hash,
        center_text=commit.author,
        right_text=timestamp_str,
        bottom_text=first_line,
    )
    return item, widget
