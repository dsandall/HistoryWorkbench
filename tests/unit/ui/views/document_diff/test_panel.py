"""File responsibility: Unit tests for document diff panel facade and tree behavior kept in Phase 4a."""

from __future__ import annotations

import pytest

from freecad.history_wb.domain.diff.models import DiffState
from freecad.history_wb.qt import QtCore, QtWidgets
from freecad.history_wb.ui.presenters.presentation_models import DiffTreePresentation, NodePresentation
from freecad.history_wb.ui.views.history.models import HistorySelection
from freecad.history_wb.ui.views.theme.diff import DIFF_STATE_ROLE


def _tree_widget(panel) -> QtWidgets.QTreeWidget:  # type: ignore[no-untyped-def]
    """Find rendered document tree through observable object name."""
    tree = panel.findChild(QtWidgets.QTreeWidget, "documentDiffTree")
    assert tree is not None
    return tree


def _collapse_all_button(panel) -> QtWidgets.QToolButton:  # type: ignore[no-untyped-def]
    """Find collapse-all action through accessible name."""
    for button in panel.findChildren(QtWidgets.QToolButton):
        if button.accessibleName() == "Collapse All":
            return button
    raise RuntimeError("Collapse All button not found")


def _first_document_row_button(panel, text: str) -> QtWidgets.QToolButton:  # type: ignore[no-untyped-def]
    """Find first top-level document-row action button by visible text."""
    tree = _tree_widget(panel)
    root_item = tree.topLevelItem(0)
    assert root_item is not None
    row_widget = tree.itemWidget(root_item, 0)
    assert row_widget is not None

    for button in row_widget.findChildren(QtWidgets.QToolButton):
        if button.text() == text:
            return button
    raise RuntimeError(f"Document row button not found: {text}")


def _node(
    *,
    path: str = "Body/Pad",
    type_id: str = "PartDesign::Pad",
    label: str = "Pad",
    state: DiffState = DiffState.MODIFIED,
    has_changes: bool = True,
    visual_diff_enabled: bool = False,
    children: list[NodePresentation] | None = None,
) -> NodePresentation:
    """Build node presentation for panel tests."""
    return NodePresentation(
        path=path,
        type_id=type_id,
        label=label,
        state=state,
        has_changes=has_changes,
        visual_diff_enabled=visual_diff_enabled,
        children=[] if children is None else children,
    )


def _diff(*, nodes: list[NodePresentation] | None = None, state: DiffState = DiffState.UNCHANGED) -> DiffTreePresentation:
    """Build document diff presentation for panel tests."""
    return DiffTreePresentation(
        nodes=[] if nodes is None else nodes,
        git_path="parts/A.FCStd",
        indicators=[],
        document_state=state,
    )


def test_show_doc_diff_with_empty_list_clears_tree(panel) -> None:  # type: ignore[no-untyped-def]
    """show_doc_diff() clears tree when given empty list."""
    panel.show_doc_diff([_node()])

    assert _tree_widget(panel).topLevelItemCount() == 1

    panel.show_doc_diff([])

    assert _tree_widget(panel).topLevelItemCount() == 0


@pytest.mark.parametrize("state", [DiffState.ADDED, DiffState.DELETED, DiffState.MODIFIED])
def test_node_state_colors(panel, state: DiffState) -> None:  # type: ignore[no-untyped-def]
    """Nodes display with theme-aware color data per diff state."""
    panel.show_doc_diff([_node(state=state)])

    root_item = _tree_widget(panel).topLevelItem(0)
    assert root_item is not None
    child_item = root_item.child(0)
    assert child_item is not None
    assert child_item.data(0, DIFF_STATE_ROLE) == state
    assert child_item.background(0).style() != QtCore.Qt.BrushStyle.NoBrush
    assert child_item.foreground(0).style() != QtCore.Qt.BrushStyle.NoBrush


def test_unchanged_nodes_shown_without_color(panel) -> None:  # type: ignore[no-untyped-def]
    """UNCHANGED nodes display without custom color."""
    panel.show_doc_diff([_node(state=DiffState.UNCHANGED, has_changes=False, type_id="PartDesign::Body", label="BasePart")])

    root_item = _tree_widget(panel).topLevelItem(0)
    assert root_item is not None
    child_item = root_item.child(0)
    assert child_item is not None
    assert child_item.data(0, DIFF_STATE_ROLE) is None
    assert child_item.background(0).style() == QtCore.Qt.BrushStyle.NoBrush


def test_path_stored_in_user_role_for_retrieval(panel) -> None:  # type: ignore[no-untyped-def]
    """Node paths are stored in Qt.UserRole for later property lookup."""
    panel.show_doc_diff([_node(path="Body/Pad/Length", type_id="PropertyLength", label="Length")])

    root_item = _tree_widget(panel).topLevelItem(0)
    assert root_item is not None
    child_item = root_item.child(0)
    assert child_item is not None
    assert child_item.data(0, QtCore.Qt.ItemDataRole.UserRole) == "Body/Pad/Length"


def test_show_doc_diffs_creates_top_level_document_rows(panel) -> None:  # type: ignore[no-untyped-def]
    """show_doc_diffs() creates top-level document rows."""
    panel.show_doc_diffs([_diff(nodes=[_node()])])

    tree = _tree_widget(panel)
    assert tree.topLevelItemCount() == 1
    root_item = tree.topLevelItem(0)
    assert root_item is not None
    assert root_item.text(0) == "parts/A.FCStd"


@pytest.mark.parametrize("state", [DiffState.ADDED, DiffState.DELETED])
def test_show_doc_diffs_applies_document_row_diff_state(panel, state: DiffState) -> None:  # type: ignore[no-untyped-def]
    """Document rows keep diff-state styling after row extraction."""
    panel.show_doc_diffs([_diff(state=state)])

    tree = _tree_widget(panel)
    root_item = tree.topLevelItem(0)
    assert root_item is not None
    assert root_item.data(0, DIFF_STATE_ROLE) == state
    row_widget = tree.itemWidget(root_item, 0)
    assert row_widget is not None
    assert "background-color" in row_widget.styleSheet()
    assert "QWidget#diffRowContainer" in row_widget.styleSheet()


def test_visual_diff_row_widget_keeps_diff_state_styling(panel) -> None:  # type: ignore[no-untyped-def]
    """Visual diff child rows remain panel-owned and keep diff styling in Phase 4a."""
    panel.show_doc_diffs([_diff(nodes=[_node(state=DiffState.ADDED, visual_diff_enabled=True)])])

    tree = _tree_widget(panel)
    root_item = tree.topLevelItem(0)
    assert root_item is not None
    child_item = root_item.child(0)
    assert child_item is not None
    row_widget = tree.itemWidget(child_item, 0)
    assert row_widget is not None
    assert "background-color" in row_widget.styleSheet()


def test_show_doc_diffs_with_empty_list_clears_tree(panel) -> None:  # type: ignore[no-untyped-def]
    """show_doc_diffs() clears tree when given empty list."""
    panel.show_doc_diffs([_diff(nodes=[_node()])])

    assert _tree_widget(panel).topLevelItemCount() == 1

    panel.show_doc_diffs([])

    assert _tree_widget(panel).topLevelItemCount() == 0


def test_set_node_selection_callback_receives_git_path_and_node_path(panel) -> None:  # type: ignore[no-untyped-def]
    """Child item clicks still route through panel callback."""
    captured: list[tuple[str, str]] = []
    panel.set_node_selection_callback(lambda git_path, node_path: captured.append((git_path, node_path)))
    panel.show_doc_diffs([_diff(nodes=[_node(path="Body", type_id="PartDesign::Body", label="Body")])])

    root_item = _tree_widget(panel).topLevelItem(0)
    assert root_item is not None
    child_item = root_item.child(0)
    assert child_item is not None

    panel._on_tree_item_clicked(child_item, 0)

    assert captured == [("parts/A.FCStd", "Body")]


def test_visual_diff_button_only_for_enabled_nodes(panel) -> None:  # type: ignore[no-untyped-def]
    """Visual diff button appears only when presentation enables it."""
    panel.set_current_history_selection(HistorySelection(item_kind="WORKING_TREE", commit_hash=None))
    panel.show_doc_diffs(
        [
            _diff(
                nodes=[
                    _node(visual_diff_enabled=True),
                    _node(path="Body/Sketch", type_id="App::FeaturePython", label="Sketch", visual_diff_enabled=False),
                ]
            )
        ]
    )

    tree = _tree_widget(panel)
    root = tree.topLevelItem(0)
    assert root is not None
    first = root.child(0)
    second = root.child(1)
    assert first is not None and second is not None
    first_container = tree.itemWidget(first, 0)
    second_container = tree.itemWidget(second, 0)
    assert first_container is not None
    assert second_container is None
    assert len(first_container.findChildren(QtWidgets.QToolButton)) == 1


def test_visual_diff_button_emits_git_path_and_node_path(panel) -> None:  # type: ignore[no-untyped-def]
    """Visual diff button callback emits (git_path, node_path)."""
    captured: list[tuple[str, str]] = []
    panel.set_visual_diff_callback(lambda git_path, node_path: captured.append((git_path, node_path)))
    panel.set_current_history_selection(HistorySelection(item_kind="WORKING_TREE", commit_hash=None))
    panel.show_doc_diffs([_diff(nodes=[_node(visual_diff_enabled=True)])])

    tree = _tree_widget(panel)
    root = tree.topLevelItem(0)
    assert root is not None
    child = root.child(0)
    assert child is not None
    container = tree.itemWidget(child, 0)
    assert container is not None
    buttons = container.findChildren(QtWidgets.QToolButton)
    assert len(buttons) == 1

    buttons[0].click()

    assert captured == [("parts/A.FCStd", "Body/Pad")]


def test_widget_clears_document_diffs_without_property_widget(panel) -> None:  # type: ignore[no-untyped-def]
    """DocumentDiffTreeWidget does not need property widget reference to clear diffs."""
    panel.show_doc_diff([_node()])

    assert _tree_widget(panel).topLevelItemCount() == 1

    panel.clear_doc_diffs()

    assert _tree_widget(panel).topLevelItemCount() == 0


def test_widget_renders_document_diffs_without_property_widget(panel) -> None:  # type: ignore[no-untyped-def]
    """DocumentDiffTreeWidget does not need property widget reference to render diffs."""
    panel.show_doc_diff([_node()])

    tree = _tree_widget(panel)
    assert tree.topLevelItemCount() == 1
    root_item = tree.topLevelItem(0)
    assert root_item is not None
    assert root_item.childCount() == 1


def test_collapse_all_button_is_icon_only(panel) -> None:  # type: ignore[no-untyped-def]
    """Collapse All action uses icon-only button with tooltip."""
    collapse_button = _collapse_all_button(panel)
    assert collapse_button.text() == ""
    assert not collapse_button.icon().isNull()
    assert "Collapse All" in collapse_button.toolTip()


def test_collapse_tree_item_collapses_root(panel) -> None:  # type: ignore[no-untyped-def]
    """collapse_tree_item() collapses root item for given git_path."""
    panel.show_doc_diff([_node()], git_path="parts/A.FCStd")

    root_item = _tree_widget(panel).topLevelItem(0)
    assert root_item is not None
    root_item.setExpanded(True)
    assert root_item.isExpanded()

    panel.collapse_tree_item("parts/A.FCStd")

    assert not root_item.isExpanded()


def test_collapse_all_tree_items_collapses_every_root(panel) -> None:  # type: ignore[no-untyped-def]
    """collapse_all_tree_items() collapses every expanded root item."""
    panel.show_doc_diffs(
        [
            _diff(nodes=[_node()]),
            DiffTreePresentation(nodes=[_node()], git_path="parts/B.FCStd", indicators=[]),
        ]
    )
    tree = _tree_widget(panel)
    first_root = tree.topLevelItem(0)
    second_root = tree.topLevelItem(1)
    assert first_root is not None
    assert second_root is not None
    first_root.setExpanded(True)
    second_root.setExpanded(True)

    panel.collapse_all_tree_items()

    assert not first_root.isExpanded()
    assert not second_root.isExpanded()


def test_set_stage_button_enabled_updates_button(panel) -> None:  # type: ignore[no-untyped-def]
    """set_stage_button_enabled() updates rendered stage button for git_path."""
    panel.set_current_history_selection(HistorySelection(item_kind="WORKING_TREE", commit_hash=None))
    panel.show_doc_diffs(
        [
            DiffTreePresentation(
                nodes=[_node()],
                git_path="parts/A.FCStd",
                indicators=[],
                stage_button_enabled=True,
            )
        ]
    )

    stage_button = _first_document_row_button(panel, "+ Reviewed")
    assert stage_button.isEnabled()

    panel.set_stage_button_enabled("parts/A.FCStd", False)

    assert not stage_button.isEnabled()
