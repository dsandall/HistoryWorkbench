"""File responsibility: Unit tests for HistoryPanelWidget facade orchestration behavior."""

from __future__ import annotations

from freecad.history_wb.qt import QtCore
from freecad.history_wb.ui.views.history.models import HistorySelection
from freecad.history_wb.ui.views.history.repository_header import RepositoryHeader

from .conftest import history_row_text, make_commit


def test_show_commits_keeps_special_rows_and_appends_commit_rows(history_panel_widget) -> None:  # type: ignore[no-untyped-def]
    """Facade rebuild keeps special rows before appended commit rows."""
    history_panel_widget.show_commits([make_commit()])

    assert history_panel_widget.history_list.count() == 3
    assert history_row_text(history_panel_widget.history_list, 0) == "Current Files"
    assert history_row_text(history_panel_widget.history_list, 1) == "Reviewed"
    assert "a1b2c3d" in history_row_text(history_panel_widget.history_list, 2)


def test_append_commits_keeps_existing_special_rows(history_panel_widget) -> None:  # type: ignore[no-untyped-def]
    """Facade append adds commits without replacing existing pseudo-rows."""
    history_panel_widget.show_commits([])

    history_panel_widget.append_commits([make_commit(commit_id="abc1234", message="Older commit", author="Author")])

    assert history_panel_widget.history_list.count() == 3
    assert history_row_text(history_panel_widget.history_list, 0) == "Current Files"
    assert history_row_text(history_panel_widget.history_list, 1) == "Reviewed"
    assert "Older commit" in history_row_text(history_panel_widget.history_list, 2)


def test_show_commits_without_selection_leaves_facade_unselected(history_panel_widget) -> None:  # type: ignore[no-untyped-def]
    """Rebuild without prior selection keeps facade and list unselected."""
    history_panel_widget.show_commits([make_commit(), make_commit(commit_id="b2c3d4e5f6789012", message="Another commit")])

    assert history_panel_widget.history_list.selectedItems() == []
    assert history_panel_widget.get_current_history_selection() is None


def test_show_commits_refresh_restores_valid_selection_and_reemits_once(history_panel_widget) -> None:  # type: ignore[no-untyped-def]
    """Facade restore path keeps valid selection and re-emits one sync event."""
    selected_commit_hash = "a1b2c3d4e5f67890"
    history_panel_widget.show_commits(
        [
            make_commit(commit_id=selected_commit_hash, message="Selected commit"),
            make_commit(commit_id="b2c3d4e5f6789012", message="Another commit", timestamp="2024-01-16T10:30:00+00:00"),
        ]
    )
    history_panel_widget.history_list.itemClicked.emit(history_panel_widget.history_list.item(2))

    selection_requests: list[HistorySelection] = []
    selection_changes: list[HistorySelection | None] = []
    history_panel_widget.history_selection_requested.connect(selection_requests.append)
    history_panel_widget.history_selection_changed.connect(selection_changes.append)

    history_panel_widget.show_commits([make_commit(commit_id=selected_commit_hash, message="Selected commit updated")])

    selected_items = history_panel_widget.history_list.selectedItems()
    assert len(selected_items) == 1
    assert selected_items[0].data(QtCore.Qt.ItemDataRole.UserRole) == HistorySelection(
        item_kind="COMMIT",
        commit_hash=selected_commit_hash,
    )
    assert selection_requests == [HistorySelection(item_kind="COMMIT", commit_hash=selected_commit_hash)]
    assert selection_changes == [HistorySelection(item_kind="COMMIT", commit_hash=selected_commit_hash)]


def test_show_commits_refresh_clears_missing_selection_and_propagates_none(history_panel_widget) -> None:  # type: ignore[no-untyped-def]
    """Facade clear path drops stale selection and emits null sync state."""
    removed_commit_hash = "a1b2c3d4e5f67890"
    history_panel_widget.show_commits([make_commit(commit_id=removed_commit_hash, message="Will be removed")])
    history_panel_widget.history_list.itemClicked.emit(history_panel_widget.history_list.item(2))
    selection_changes: list[HistorySelection | None] = []
    history_panel_widget.history_selection_changed.connect(selection_changes.append)

    history_panel_widget.show_commits(
        [make_commit(commit_id="b2c3d4e5f6789012", message="Different commit", timestamp="2024-01-16T10:30:00+00:00")]
    )

    assert history_panel_widget.history_list.selectedItems() == []
    assert history_panel_widget.get_current_history_selection() is None
    assert selection_changes == [None]


def test_refresh_requested_signal_forwards_repository_header_signal(history_panel_widget) -> None:  # type: ignore[no-untyped-def]
    """Facade refresh signal forwards child signal without exposing child internals."""
    called = []
    history_panel_widget.refresh_requested.connect(lambda: called.append("refresh"))
    repository_header = history_panel_widget.findChild(RepositoryHeader)

    assert repository_header is not None
    repository_header.refresh_button.click()

    assert called == ["refresh"]


def test_save_iteration_requested_signal_forwards_repository_header_signal(history_panel_widget) -> None:  # type: ignore[no-untyped-def]
    """Facade save signal forwards child signal without exposing child internals."""
    called = []
    history_panel_widget.save_iteration_requested.connect(lambda: called.append("save"))
    repository_header = history_panel_widget.findChild(RepositoryHeader)

    assert repository_header is not None
    repository_header.save_iteration_button.click()

    assert called == ["save"]


def test_history_scroll_bottom_requested_signal_forwards_list_signal(history_panel_widget) -> None:  # type: ignore[no-untyped-def]
    """Facade bottom-scroll signal forwards list near-bottom signal."""
    called = []
    history_panel_widget.history_scroll_bottom_requested.connect(lambda: called.append("bottom"))

    history_panel_widget.history_list.near_bottom_requested.emit()

    assert called == ["bottom"]


def test_get_current_history_selection_returns_clicked_selection(history_panel_widget) -> None:  # type: ignore[no-untyped-def]
    """Facade stores current history selection from child list changes."""
    commit_hash = "a1b2c3d4e5f67890"
    history_panel_widget.show_commits([make_commit(commit_id=commit_hash, message="Test commit")])

    history_panel_widget.history_list.itemClicked.emit(history_panel_widget.history_list.item(2))

    assert history_panel_widget.get_current_history_selection() == HistorySelection(
        item_kind="COMMIT",
        commit_hash=commit_hash,
    )
