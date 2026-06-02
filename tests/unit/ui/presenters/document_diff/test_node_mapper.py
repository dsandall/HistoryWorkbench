# SPDX-License-Identifier: LGPL-3.0-or-later
# File responsibility: Unit tests for visual-diff eligibility checks in node mapper.

import pytest

from freecad.history_wb.ui.presenters.document_diff.node_mapper import _is_visual_diff_enabled


@pytest.mark.parametrize(
    ("type_id", "expected"),
    [
        ("Part::Feature", True),
        ("Part::Box", True),
        ("PartDesign::Pad", True),
        ("PartDesign::Body", True),
        ("Sketcher::SketchObject", True),
        ("App::DocumentObjectGroup", False),
        ("Mesh::Feature", False),
        ("Sketcher::Other", False),
    ],
)
def test_is_visual_diff_enabled(type_id: str, expected: bool) -> None:
    """Visual diff support matches allowed Part, PartDesign, and sketch node types."""
    assert _is_visual_diff_enabled(type_id) is expected
