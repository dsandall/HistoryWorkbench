"""Module responsibility: Diff panel view facade and modal UI helpers."""

from .dialog_view import DialogView
from .dialogs import (
    GitConfigDialogResult,
    show_configure_author_dialog,
    show_restore_file_confirmation_dialog,
    show_restore_scope_dialog,
    show_save_iteration_dialog,
)
from .messages import show_error_message, show_info_message, show_warning_message
from .view import HistoryPanelView


__all__ = [
    "HistoryPanelView",
    "DialogView",
    "GitConfigDialogResult",
    "show_configure_author_dialog",
    "show_error_message",
    "show_info_message",
    "show_restore_file_confirmation_dialog",
    "show_restore_scope_dialog",
    "show_save_iteration_dialog",
    "show_warning_message",
]
