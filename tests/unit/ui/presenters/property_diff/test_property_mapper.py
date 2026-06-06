# File responsibility: Unit tests for pure property-diff presentation mapping helpers.

import pytest

from freecad.history_wb.domain.diff.models import DiffState, NodeDiff, PropertyDiff
from freecad.history_wb.domain.tree import Property
from freecad.history_wb.domain.tree.data_path import (
    ListData,
    PlacementData,
    PrimitiveData,
    PropertyPathType,
    PropertyPathValue,
    VectorData,
)
from freecad.history_wb.ui.presenters.property_diff.property_mapper import transform_property_diffs


def _find_expr_child(children: list) -> object | None:
    """Find Expression child in nested property presentations."""
    for child in children:
        if child.name == "Expression":
            return child
    return None


def _nested_list_property() -> Property:
    """Create nested list property without root-path value row."""
    return Property(
        value=ListData(
            paths={},
            items=[
                ListData(
                    paths={},
                    items=[
                        PrimitiveData(
                            paths={".": PropertyPathValue(PropertyPathType.INT, 1)},
                        )
                    ],
                )
            ],
        ),
        group="Base",
    )


class TestTransformPropertyDiffsExpressionOnly:
    """Tests that expression-only changes do not affect parent property row state."""

    def test_expression_cleared_value_unchanged(self) -> None:
        """Expression cleared, value same => property row UNCHANGED, Expression child DELETED."""
        old_val = Property.from_freecad(10.0, {".": "Sketch.X"}, "Base")
        new_val = Property.from_freecad(10.0, {}, "Base")
        prop_diff = PropertyDiff(property_name="Length", old_value=old_val, new_value=new_val)
        node_diff = NodeDiff(path="Pad", type_id="PartDesign::Pad", property_diffs=[prop_diff])

        presentations = transform_property_diffs(node_diff, precision=2)
        prop = presentations[0]

        assert prop.name == "Length"
        assert prop.state == DiffState.UNCHANGED
        expr_child = _find_expr_child(prop.children)
        assert expr_child is not None
        assert expr_child.state == DiffState.DELETED

    def test_expression_added_value_unchanged(self) -> None:
        """Expression added, value same => property row UNCHANGED, Expression child ADDED."""
        old_val = Property.from_freecad(10.0, {}, "Base")
        new_val = Property.from_freecad(10.0, {".": "Sketch.X"}, "Base")
        prop_diff = PropertyDiff(property_name="Length", old_value=old_val, new_value=new_val)
        node_diff = NodeDiff(path="Pad", type_id="PartDesign::Pad", property_diffs=[prop_diff])

        presentations = transform_property_diffs(node_diff, precision=2)
        prop = presentations[0]

        assert prop.name == "Length"
        assert prop.state == DiffState.UNCHANGED
        expr_child = _find_expr_child(prop.children)
        assert expr_child is not None
        assert expr_child.state == DiffState.ADDED

    def test_expression_modified_value_unchanged(self) -> None:
        """Expression changed, value same => property row UNCHANGED, Expression child MODIFIED."""
        old_val = Property.from_freecad(10.0, {".": "A"}, "Base")
        new_val = Property.from_freecad(10.0, {".": "B"}, "Base")
        prop_diff = PropertyDiff(property_name="Length", old_value=old_val, new_value=new_val)
        node_diff = NodeDiff(path="Pad", type_id="PartDesign::Pad", property_diffs=[prop_diff])

        presentations = transform_property_diffs(node_diff, precision=2)
        prop = presentations[0]

        assert prop.name == "Length"
        assert prop.state == DiffState.UNCHANGED
        expr_child = _find_expr_child(prop.children)
        assert expr_child is not None
        assert expr_child.state == DiffState.MODIFIED


class TestTransformPropertyDiffsValueOnly:
    """Tests that value changes correctly set property row state."""

    def test_value_changed(self) -> None:
        """Value changed => property row MODIFIED."""
        old_val = Property.from_freecad(10.0, {}, "Base")
        new_val = Property.from_freecad(20.0, {}, "Base")
        prop_diff = PropertyDiff(property_name="Length", old_value=old_val, new_value=new_val)
        node_diff = NodeDiff(path="Pad", type_id="PartDesign::Pad", property_diffs=[prop_diff])

        presentations = transform_property_diffs(node_diff, precision=2)
        prop = presentations[0]

        assert prop.name == "Length"
        assert prop.state == DiffState.MODIFIED

    def test_value_unchanged(self) -> None:
        """Value unchanged => property row UNCHANGED."""
        val = Property.from_freecad(10.0, {}, "Base")
        prop_diff = PropertyDiff(property_name="Length", old_value=val, new_value=val)
        node_diff = NodeDiff(path="Pad", type_id="PartDesign::Pad", property_diffs=[prop_diff])

        presentations = transform_property_diffs(node_diff, precision=2)
        prop = presentations[0]

        assert prop.name == "Length"
        assert prop.state == DiffState.UNCHANGED


class TestTransformPropertyDiffsDeletedAdded:
    """Tests that deleted/added properties correctly set property row and expression child states."""

    def test_property_deleted_with_expression(self) -> None:
        """Property deleted with expression => property row DELETED, Expression child DELETED."""
        old_val = Property.from_freecad(10.0, {".": "Sketch.X"}, "Base")
        prop_diff = PropertyDiff(property_name="Length", old_value=old_val, new_value=None)
        node_diff = NodeDiff(path="Pad", type_id="PartDesign::Pad", property_diffs=[prop_diff])

        presentations = transform_property_diffs(node_diff, precision=2)
        prop = presentations[0]

        assert prop.name == "Length"
        assert prop.state == DiffState.DELETED
        expr_child = _find_expr_child(prop.children)
        assert expr_child is not None
        assert expr_child.state == DiffState.DELETED

    def test_property_added_with_expression(self) -> None:
        """Property added with expression => property row ADDED, Expression child ADDED."""
        new_val = Property.from_freecad(10.0, {".": "Sketch.X"}, "Base")
        prop_diff = PropertyDiff(property_name="Length", old_value=None, new_value=new_val)
        node_diff = NodeDiff(path="Pad", type_id="Sketcher::SketchObject", property_diffs=[prop_diff])

        presentations = transform_property_diffs(node_diff, precision=2)
        prop = presentations[0]

        assert prop.name == "Length"
        assert prop.state == DiffState.ADDED
        expr_child = _find_expr_child(prop.children)
        assert expr_child is not None
        assert expr_child.state == DiffState.ADDED

    @pytest.mark.parametrize(
        ("old_value", "new_value", "expected_state"),
        [
            (None, _nested_list_property(), DiffState.ADDED),
            (_nested_list_property(), None, DiffState.DELETED),
        ],
    )
    def test_nested_whole_property_change_marks_root_and_containers(
        self,
        old_value: Property | None,
        new_value: Property | None,
        expected_state: DiffState,
    ) -> None:
        """Whole nested property change => root and container rows use same state."""
        prop_diff = PropertyDiff(property_name="Constraints", old_value=old_value, new_value=new_value)
        node_diff = NodeDiff(path="Sketch", type_id="Sketcher::SketchObject", property_diffs=[prop_diff])

        presentations = transform_property_diffs(node_diff, precision=2)
        prop = presentations[0]
        container = prop.children[0]
        leaf = container.children[0]

        assert prop.state == expected_state
        assert container.state == expected_state
        assert leaf.state == expected_state


class TestTransformPropertyDiffsComplexProperty:
    """Tests that parent rows in complex properties do not inherit child states."""

    def test_placement_base_z_changed_parent_rows_unchanged(self) -> None:
        """Placement.Base.z change => Placement and Base rows UNCHANGED."""
        old_val = Property(
            value=PlacementData(
                paths={
                    "Base.x": PropertyPathValue(PropertyPathType.QUANTITY, 0.0, unit="mm"),
                    "Base.y": PropertyPathValue(PropertyPathType.QUANTITY, 0.0, unit="mm"),
                    "Base.z": PropertyPathValue(PropertyPathType.QUANTITY, 0.0, unit="mm"),
                    "Rotation.Angle": PropertyPathValue(PropertyPathType.QUANTITY, 0.0, unit="deg"),
                    "Rotation.Axis.x": PropertyPathValue(PropertyPathType.FLOAT, 0.0),
                    "Rotation.Axis.y": PropertyPathValue(PropertyPathType.FLOAT, 0.0),
                    "Rotation.Axis.z": PropertyPathValue(PropertyPathType.FLOAT, 1.0),
                }
            ),
            group="Base",
        )
        new_val = Property(
            value=PlacementData(
                paths={
                    "Base.x": PropertyPathValue(PropertyPathType.QUANTITY, 0.0, unit="mm"),
                    "Base.y": PropertyPathValue(PropertyPathType.QUANTITY, 0.0, unit="mm"),
                    "Base.z": PropertyPathValue(PropertyPathType.QUANTITY, 10.0, unit="mm"),
                    "Rotation.Angle": PropertyPathValue(PropertyPathType.QUANTITY, 0.0, unit="deg"),
                    "Rotation.Axis.x": PropertyPathValue(PropertyPathType.FLOAT, 0.0),
                    "Rotation.Axis.y": PropertyPathValue(PropertyPathType.FLOAT, 0.0),
                    "Rotation.Axis.z": PropertyPathValue(PropertyPathType.FLOAT, 1.0),
                }
            ),
            group="Base",
        )
        prop_diff = PropertyDiff(property_name="Placement", old_value=old_val, new_value=new_val)
        node_diff = NodeDiff(path="Pad", type_id="PartDesign::Pad", property_diffs=[prop_diff])

        presentations = transform_property_diffs(node_diff, precision=2)
        prop = presentations[0]
        base_child = next((child for child in prop.children if child.name == "Base"), None)
        assert base_child is not None
        z_child = next((child for child in base_child.children if child.name == "z"), None)

        assert prop.state == DiffState.UNCHANGED
        assert base_child.state == DiffState.UNCHANGED
        assert z_child is not None
        assert z_child.state == DiffState.MODIFIED

    def test_sub_path_changed_parent_unchanged(self) -> None:
        """Only sub-path changed => parent rows UNCHANGED, only leaf MODIFIED."""
        old_val = Property(
            value=VectorData(
                paths={
                    ".": PropertyPathValue(PropertyPathType.FLOAT, 1.0),
                    "x": PropertyPathValue(PropertyPathType.FLOAT, 1.0),
                    "y": PropertyPathValue(PropertyPathType.FLOAT, 2.0),
                    "z": PropertyPathValue(PropertyPathType.FLOAT, 3.0),
                }
            ),
            group="Base",
        )
        new_val = Property(
            value=VectorData(
                paths={
                    ".": PropertyPathValue(PropertyPathType.FLOAT, 1.0),
                    "x": PropertyPathValue(PropertyPathType.FLOAT, 10.0),
                    "y": PropertyPathValue(PropertyPathType.FLOAT, 2.0),
                    "z": PropertyPathValue(PropertyPathType.FLOAT, 3.0),
                }
            ),
            group="Base",
        )
        prop_diff = PropertyDiff(property_name="Vector", old_value=old_val, new_value=new_val)
        node_diff = NodeDiff(path="Pad", type_id="PartDesign::Pad", property_diffs=[prop_diff])

        presentations = transform_property_diffs(node_diff, precision=2)
        prop = presentations[0]

        assert prop.name == "Vector"
        assert prop.state == DiffState.UNCHANGED

        x_child = next((child for child in prop.children if child.name == "x"), None)
        assert x_child is not None
        assert x_child.state == DiffState.MODIFIED

        y_child = next((child for child in prop.children if child.name == "y"), None)
        z_child = next((child for child in prop.children if child.name == "z"), None)
        assert y_child is not None
        assert y_child.state == DiffState.UNCHANGED
        assert z_child is not None
        assert z_child.state == DiffState.UNCHANGED
