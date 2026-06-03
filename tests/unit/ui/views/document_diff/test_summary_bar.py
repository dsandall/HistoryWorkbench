"""File responsibility: Unit tests for document diff summary bar behavior."""

from __future__ import annotations

from freecad.history_wb.ui.views.document_diff.document_row import REMOVE_REVIEWED_TOOLTIP
from freecad.history_wb.ui.views.document_diff.summary_bar import DocumentDiffSummaryBar


def test_show_summary_with_zero_changes(application) -> None:  # type: ignore[no-untyped-def]
    """show_summary(0) displays No changes."""
    widget = DocumentDiffSummaryBar(REMOVE_REVIEWED_TOOLTIP)

    widget.show_summary(0, 0, 0)

    assert widget._changed_label.text() == "No changes"


def test_show_summary_with_per_status_counts(application) -> None:  # type: ignore[no-untyped-def]
    """show_summary() displays Modified/Deleted/Added counts."""
    widget = DocumentDiffSummaryBar(REMOVE_REVIEWED_TOOLTIP)

    widget.show_summary(2, 1, 3)

    assert widget._changed_label.text() == "Modified: 2  Deleted: 1  Added: 3"


def test_stage_all_button_visibility_and_enabled(application) -> None:  # type: ignore[no-untyped-def]
    """Stage-all visibility and enabled state stay controllable."""
    widget = DocumentDiffSummaryBar(REMOVE_REVIEWED_TOOLTIP)

    widget.set_stage_all_button_visible(True)
    widget.set_stage_all_button_enabled(True)
    assert not widget._stage_all_button.isHidden()
    assert widget._stage_all_button.isEnabled()

    widget.set_stage_all_button_enabled(False)
    widget.set_stage_all_button_visible(False)
    assert not widget._stage_all_button.isEnabled()
    assert widget._stage_all_button.isHidden()


def test_remove_all_button_visibility_and_callback(application) -> None:  # type: ignore[no-untyped-def]
    """Remove All button keeps text, tooltip, visibility, and callback routing."""
    widget = DocumentDiffSummaryBar(REMOVE_REVIEWED_TOOLTIP)
    captured: list[str] = []
    widget.remove_all_requested.connect(lambda: captured.append("remove"))

    widget.set_remove_all_button_visible(True)
    widget.set_remove_all_button_enabled(True)
    widget._remove_all_button.click()

    assert widget._remove_all_button.text() == "Remove All"
    assert "will not be saved in the next iteration" in widget._remove_all_button.toolTip()
    assert not widget._remove_all_button.isHidden()
    assert captured == ["remove"]


def test_restore_all_button_visibility_and_callback(application) -> None:  # type: ignore[no-untyped-def]
    """Restore All button stays hidden by default and emits when clicked."""
    widget = DocumentDiffSummaryBar(REMOVE_REVIEWED_TOOLTIP)
    captured: list[str] = []
    widget.restore_all_requested.connect(lambda: captured.append("restore"))

    widget.set_restore_all_button_visible(True)
    widget.set_restore_all_button_enabled(True)
    widget._restore_all_button.click()

    assert not widget._restore_all_button.isHidden()
    assert captured == ["restore"]
