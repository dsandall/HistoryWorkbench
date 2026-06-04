"""File responsibility: Message-box helpers for diff panel modal feedback."""

from ....qt import QtWidgets


def show_warning_message(parent: QtWidgets.QWidget, title: str, message: str) -> None:
    """Show warning dialog for diff panel flows."""
    QtWidgets.QMessageBox.warning(parent, title, message)


def show_info_message(parent: QtWidgets.QWidget, title: str, message: str) -> None:
    """Show informational dialog for diff panel flows."""
    QtWidgets.QMessageBox.information(parent, title, message)


def show_error_message(parent: QtWidgets.QWidget, title: str, message: str) -> None:
    """Show error dialog for diff panel flows."""
    QtWidgets.QMessageBox.critical(parent, title, message)
