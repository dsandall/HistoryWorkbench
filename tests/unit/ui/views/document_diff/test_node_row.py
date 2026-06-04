"""File responsibility: Unit tests for extracted visual-diff node row widget."""

from __future__ import annotations

from freecad.history_wb.qt import QtWidgets
from freecad.history_wb.ui.views.document_diff.node_row import NodeDiffRowWidget


def test_node_row_renders_visual_diff_button() -> None:
    """Node row renders icon-only visual-diff action."""
    row = NodeDiffRowWidget(
        text="Pad",
        type_id="PartDesign::Pad",
        git_path="parts/A.FCStd",
        node_path="Body/Pad",
    )

    label = row.findChild(QtWidgets.QLabel)
    button = row.findChild(QtWidgets.QToolButton)
    assert label is not None
    assert button is not None
    assert label.text() == "Pad"
    assert label.toolTip() == "PartDesign::Pad"
    assert button.text() == ""
    assert not button.icon().isNull()
    assert "Open 3D comparison" in button.toolTip()


def test_node_row_emits_visual_diff_request_with_paths() -> None:
    """Button click emits git path and node path payload."""
    row = NodeDiffRowWidget(
        text="Pad",
        type_id="PartDesign::Pad",
        git_path="parts/A.FCStd",
        node_path="Body/Pad",
    )
    captured: list[tuple[str, str]] = []
    row.visual_diff_requested.connect(lambda git_path, node_path: captured.append((git_path, node_path)))

    button = row.findChild(QtWidgets.QToolButton)
    assert button is not None
    button.click()

    assert captured == [("parts/A.FCStd", "Body/Pad")]
