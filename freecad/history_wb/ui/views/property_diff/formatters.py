"""File responsibility: Property diff display-name, value, and tooltip formatting helpers."""

from __future__ import annotations

from typing import Any

from ....domain.diff.models import DiffState
from ....utils import format_float


__all__ = [
    "build_property_tooltip",
    "camelcase_to_spaces",
    "format_property_value",
    "get_property_display_values",
]


def camelcase_to_spaces(name: str) -> str:
    """Insert spaces before uppercase letters and digits to match FreeCAD display."""
    if not name:
        return name

    result = [name[0]]
    upper_sequence_start = 0 if name[0].isupper() else -1
    for index in range(1, len(name)):
        char = name[index]
        previous_char = name[index - 1]

        # Split lower->upper and acronym->word boundaries to match FreeCAD labels.
        if _should_insert_space_before_char(char, previous_char, upper_sequence_start, index, name):
            result.append(" ")

        upper_sequence_start = _update_upper_sequence_start(char, index)
        result.append(char)
    return "".join(result)


def format_property_value(value: Any, precision: int) -> str:
    """Format one property value for display using configured float precision."""
    if isinstance(value, float):
        return format_float(value, precision)
    return str(value)


def get_property_display_values(
    state: DiffState,
    *,
    old_value: Any,
    new_value: Any,
    precision: int,
) -> tuple[str, str]:
    """Return left/right display values for one property row."""
    old_value_str = format_property_value(old_value, precision) if old_value is not None else ""
    new_value_str = format_property_value(new_value, precision) if new_value is not None else ""
    if state == DiffState.ADDED:
        return "", new_value_str
    if state == DiffState.DELETED:
        return old_value_str, ""
    if state == DiffState.MODIFIED:
        return old_value_str, new_value_str

    # Mirror unchanged values in both columns for quick comparison consistency.
    return new_value_str, new_value_str


def build_property_tooltip(old_value_str: str, new_value_str: str) -> str:
    """Create tooltip text showing old and new values in stacked form."""
    return f"{old_value_str}\n-----\n{new_value_str}"


def _should_insert_space_before_char(
    char: str,
    previous_char: str,
    upper_sequence_start: int,
    index: int,
    name: str,
) -> bool:
    """Determine whether current character starts a new visible word segment."""
    if char.isupper():
        if previous_char.islower():
            return True

        # Break acronym before final capital when next char starts lowercase word.
        if upper_sequence_start >= 0 and index + 1 < len(name) and name[index + 1].islower():
            return True
    elif char.isdigit():
        if previous_char.isalpha():
            return True
    return False


def _update_upper_sequence_start(char: str, index: int) -> int:
    """Track current uppercase run for acronym boundary handling."""
    if char.isupper():
        return index
    return -1
