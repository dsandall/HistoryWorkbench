"""File responsibility: Unit tests for repository header interactions and rendering."""

from __future__ import annotations

from unittest.mock import patch

from freecad.history_wb.domain.git.models import GitRepository
from freecad.history_wb.qt import QtCore, QtGui, QtWidgets
from freecad.history_wb.ui.views.history.repository_header import RepositoryHeader


def test_refresh_button_emits_signal() -> None:
    """Refresh button click emits header refresh signal."""
    header = RepositoryHeader()
    received = []
    header.refresh_requested.connect(lambda: received.append("refresh"))

    header.refresh_button.click()

    assert received == ["refresh"]


def test_save_iteration_button_emits_signal() -> None:
    """Save Iteration button click emits header save signal."""
    header = RepositoryHeader()
    received = []
    header.save_iteration_requested.connect(lambda: received.append("save"))

    header.save_iteration_button.click()

    assert received == ["save"]


def test_header_buttons_keep_expected_order_and_icon_only_policy() -> None:
    """Header layout keeps save left of refresh with compact icon-only buttons."""
    header = RepositoryHeader()
    button_positions = []
    layout = header.layout()
    for index in range(layout.count()):
        child_widget = layout.itemAt(index).widget()
        if child_widget is not None:
            button_positions.append(child_widget)

    assert button_positions[-2] is header.save_iteration_button
    assert button_positions[-1] is header.refresh_button
    assert header.save_iteration_button.toolButtonStyle() == QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly
    assert header.refresh_button.toolButtonStyle() == QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly


def test_show_repository_none_shows_empty_state() -> None:
    """Null repository shows empty-state label styling and no tooltip."""
    header = RepositoryHeader()

    header.show_repository(None)

    assert "no project detected" in header.repository_label.text().lower()
    assert header.repository_label.toolTip() == ""
    assert "italic" in header.repository_label.styleSheet()
    assert "gray" in header.repository_label.styleSheet()


def test_show_repository_valid_repo_updates_text_tooltip_and_link_style() -> None:
    """Valid repository shows clickable project label with tooltip path."""
    header = RepositoryHeader()
    repo = GitRepository(name="test_project", absolute_path="/home/user/test_project")

    header.show_repository(repo)

    assert header.repository_label.text() == "Project: test_project"
    assert header.repository_label.toolTip() == "/home/user/test_project"
    assert "bold" in header.repository_label.styleSheet()
    assert "underline" in header.repository_label.styleSheet()


def test_open_repository_directory_opens_path_when_present() -> None:
    """Header opens repository path in desktop services when available."""
    header = RepositoryHeader()
    header.show_repository(GitRepository(name="test_project", absolute_path="/home/user/test_project"))

    with patch.object(QtGui.QDesktopServices, "openUrl", return_value=True) as open_url:
        header.open_repository_directory()

    open_url.assert_called_once_with(QtCore.QUrl.fromLocalFile("/home/user/test_project"))


def test_open_repository_directory_does_nothing_without_project() -> None:
    """Header does not open directory when no repository path is available."""
    header = RepositoryHeader()
    header.show_repository(None)

    with patch.object(QtGui.QDesktopServices, "openUrl", return_value=True) as open_url:
        header.open_repository_directory()

    open_url.assert_not_called()
