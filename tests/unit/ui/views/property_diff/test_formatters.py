"""File responsibility: Unit tests for extracted property diff formatting helpers."""

from __future__ import annotations

import pytest

from freecad.history_wb.domain.diff.models import DiffState
from freecad.history_wb.ui.views.property_diff.formatters import (
    build_property_tooltip,
    camelcase_to_spaces,
    format_property_value,
    get_property_display_values,
)


@pytest.mark.parametrize(
    ("input_name", "expected"),
    [
        ("SavedGeometry", "Saved Geometry"),
        ("Placement", "Placement"),
        ("Label2", "Label 2"),
        ("XDirection", "X Direction"),
        ("MyPropertyName", "My Property Name"),
        ("XMLDoc", "XML Doc"),
        ("Value2D", "Value 2D"),
    ],
)
def test_camelcase_to_spaces(input_name: str, expected: str) -> None:
    """CamelCase conversion keeps existing display behavior."""
    assert camelcase_to_spaces(input_name) == expected


def test_build_property_tooltip_stacks_old_and_new_values() -> None:
    """Tooltip format stays stable for property rows."""
    assert build_property_tooltip("old", "new") == "old\n-----\nnew"


def test_format_property_value_rounds_floats() -> None:
    """Float values format using provided precision."""
    assert format_property_value(1.23456, 3) == "1.235"


def test_format_property_value_uses_str_for_non_floats() -> None:
    """Non-float values keep string conversion behavior."""
    assert format_property_value({"a": 1}, 3) == "{'a': 1}"


@pytest.mark.parametrize(
    ("state", "old_value", "new_value", "expected"),
    [
        (DiffState.ADDED, None, "25.0", ("", "25.0")),
        (DiffState.DELETED, "15.0", None, ("15.0", "")),
        (DiffState.MODIFIED, "10.0", "20.0", ("10.0", "20.0")),
        (DiffState.UNCHANGED, "50.0", "50.0", ("50.0", "50.0")),
    ],
)
def test_get_property_display_values(
    state: DiffState,
    old_value: object,
    new_value: object,
    expected: tuple[str, str],
) -> None:
    """Display-value helper keeps state-specific left/right rendering."""
    assert (
        get_property_display_values(
            state,
            old_value=old_value,
            new_value=new_value,
            precision=6,
        )
        == expected
    )
