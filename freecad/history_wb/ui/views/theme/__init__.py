"""Module responsibility: Shared theme helpers for Qt view widgets."""

from .diff import (
    DIFF_STATE_ROLE,
    DiffItemDelegate,
    apply_diff_state_to_item,
    apply_diff_state_to_widget,
    background_for_state,
    foreground_for_background,
)
from .icons import set_themed_icon


__all__ = [
    "DIFF_STATE_ROLE",
    "DiffItemDelegate",
    "apply_diff_state_to_item",
    "apply_diff_state_to_widget",
    "background_for_state",
    "foreground_for_background",
    "set_themed_icon",
]
