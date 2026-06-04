# SPDX-License-Identifier: LGPL-3.0-or-later
# File responsibility: Unit tests for internal path-tree helpers used by property presentation mapping.

import pytest

from freecad.history_wb.domain.diff.models import DiffState, PropertyPathDiff
from freecad.history_wb.domain.tree.data_path import PropertyPathType, PropertyPathValue
from freecad.history_wb.ui.presenters.property_diff.path_tree import (
    _collect_leaf_values,
    _derive_container_summary,
    _format_path_value,
    _insert_path_diff,
    _path_tree_to_presentations,
    _PathTreeNode,
    _set_subtree_state,
    _split_rel_path,
)


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (".", []),
        ("", []),
        ("Base.x", ["Base", "x"]),
        ("Constraints[10].Value", ["Constraints", "[10]", "Value"]),
        ("[2].Expression", ["[2]", "Expression"]),
        ("Constraints[abc", ["Constraints", "[abc"]),
    ],
)
def test_split_rel_path(path: str, expected: list[str]) -> None:
    """Path splitting preserves dotted names, indices, and malformed bracket text."""
    assert _split_rel_path(path) == expected


def test_format_path_value_formats_float_and_quantity_values() -> None:
    """Float-like path values format with configured precision."""
    float_value = PropertyPathValue(PropertyPathType.FLOAT, 1.234)
    quantity_value = PropertyPathValue(PropertyPathType.QUANTITY, 10.0, unit="mm")

    assert _format_path_value(float_value, precision=2) == "1.23"
    assert _format_path_value(quantity_value, precision=2) == "10.00 mm"


def test_insert_path_diff_creates_expression_child_when_expression_changes() -> None:
    """Inserted path diffs keep value row plus nested Expression child when needed."""
    root = _PathTreeNode(name="Root")
    path_diff = PropertyPathDiff(
        path="Base.x",
        old_value=PropertyPathValue(PropertyPathType.FLOAT, 1.0, expression="Sketch.A"),
        new_value=PropertyPathValue(PropertyPathType.FLOAT, 2.0, expression="Sketch.B"),
    )

    _insert_path_diff(root, path_diff)

    base_node = root.children["Base"]
    x_node = base_node.children["x"]
    expr_node = x_node.children["__expr__"]
    assert x_node.state == DiffState.MODIFIED
    assert expr_node.name == "Expression"
    assert expr_node.state == DiffState.MODIFIED
    assert expr_node.old_value == "Sketch.A"
    assert expr_node.new_value == "Sketch.B"


def test_collect_leaf_values_skips_expression_rows_by_default() -> None:
    """Container summaries ignore expression rows unless caller opts in."""
    root = _PathTreeNode(name="Root")
    _insert_path_diff(
        root,
        PropertyPathDiff(
            path="Value",
            old_value=PropertyPathValue(PropertyPathType.FLOAT, 1.0, expression="Sketch.A"),
            new_value=PropertyPathValue(PropertyPathType.FLOAT, 2.0, expression="Sketch.B"),
        ),
    )

    old_values, new_values = _collect_leaf_values(root)
    old_values_with_expr, new_values_with_expr = _collect_leaf_values(root, include_expr=True)

    assert [value.value for value in old_values] == [1.0]
    assert [value.value for value in new_values] == [2.0]
    assert old_values_with_expr[1] == "Sketch.A"
    assert new_values_with_expr[1] == "Sketch.B"


def test_derive_container_summary_formats_nested_values() -> None:
    """Container summaries render formatted child values inside FreeCAD-style brackets."""
    values = [
        PropertyPathValue(PropertyPathType.FLOAT, 1.234),
        PropertyPathValue(PropertyPathType.QUANTITY, 10.0, unit="mm"),
    ]

    assert _derive_container_summary(values, precision=2) == "[1.23 10.00 mm]"


def test_set_subtree_state_applies_state_to_all_descendants() -> None:
    """Whole-property add/delete propagates state through every path-tree node."""
    root = _PathTreeNode(
        name="Root",
        children={
            "Base": _PathTreeNode(
                name="Base",
                children={"x": _PathTreeNode(name="x")},
            )
        },
    )

    _set_subtree_state(root, DiffState.ADDED)

    assert root.state == DiffState.ADDED
    assert root.children["Base"].state == DiffState.ADDED
    assert root.children["Base"].children["x"].state == DiffState.ADDED


def test_path_tree_to_presentations_sorts_indices_naturally_and_summarizes_containers() -> None:
    """Presentation rows keep deterministic order and container summaries for child-only nodes."""
    root = _PathTreeNode(name="Root")
    _insert_path_diff(
        root,
        PropertyPathDiff(
            path="Constraints[10].Value",
            old_value=PropertyPathValue(PropertyPathType.FLOAT, 10.0),
            new_value=PropertyPathValue(PropertyPathType.FLOAT, 10.0),
        ),
    )
    _insert_path_diff(
        root,
        PropertyPathDiff(
            path="Constraints[2].Value",
            old_value=PropertyPathValue(PropertyPathType.FLOAT, 2.0),
            new_value=PropertyPathValue(PropertyPathType.FLOAT, 2.0),
        ),
    )

    presentations = _path_tree_to_presentations(root, precision=2)

    constraints = presentations[0]
    assert constraints.name == "Constraints"
    assert constraints.old_value == "[[2.00] [10.00]]"
    assert [child.name for child in constraints.children] == ["[2]", "[10]"]
