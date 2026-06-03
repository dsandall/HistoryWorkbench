"""File responsibility: Shared fixtures and helpers for history view unit tests."""

from __future__ import annotations

from datetime import datetime

import pytest

from freecad.history_wb.domain.git.models import GitCommit
from freecad.history_wb.qt import QtWidgets
from freecad.history_wb.ui.views.history.panel import HistoryPanelWidget


@pytest.fixture
def history_panel_widget() -> HistoryPanelWidget:
    """Create HistoryPanelWidget with QApplication available."""
    return HistoryPanelWidget()


@pytest.fixture
def history_list_widget(history_panel_widget: HistoryPanelWidget):
    """Expose HistoryList child through panel fixture."""
    return history_panel_widget._history_list


def make_commit(
    *,
    commit_id: str = "a1b2c3d4e5f67890",
    message: str = "Test commit",
    author: str = "Test Author",
    timestamp: str = "2024-01-15T10:30:00+00:00",
) -> GitCommit:
    """Build GitCommit test value with common defaults."""
    return GitCommit(
        id=commit_id,
        message=message,
        author=author,
        timestamp=datetime.fromisoformat(timestamp),
    )


def history_row_text(list_widget, row: int) -> str:  # type: ignore[no-untyped-def]
    """Return visible text for history row, including custom widgets."""
    item = list_widget.item(row)
    widget = list_widget.itemWidget(item)
    if widget is None:
        return item.text()

    labels = widget.findChildren(QtWidgets.QLabel)
    if len(labels) == 1:
        return labels[0].text()
    if len(labels) >= 4:
        top_line = f"{labels[0].text()} {labels[1].text()} {labels[2].text()}"
        return f"{top_line}\n{labels[3].text()}"
    return item.text()


class FakeMenuAction:
    """Reusable fake QMenu action for context-menu tests."""

    def setToolTip(self, _value: str) -> None:
        """Ignore tooltip assignment in fake action."""
        return

    def setStatusTip(self, _value: str) -> None:
        """Ignore status-tip assignment in fake action."""
        return


def build_fake_menu_class() -> type:
    """Return fake QMenu class tracking creation and exec calls."""

    class _FakeMenu:
        created = False
        exec_called = False

        def __init__(self, *_args, **_kwargs) -> None:
            _FakeMenu.created = True
            self._action = FakeMenuAction()

        def setToolTipsVisible(self, _visible: bool) -> None:
            """Ignore tooltip visibility in fake menu."""
            return

        def addAction(self, _text: str) -> FakeMenuAction:
            """Return tracked fake action."""
            return self._action

        def exec(self, *_args, **_kwargs) -> FakeMenuAction:
            """Record menu execution and return tracked action."""
            _FakeMenu.exec_called = True
            return self._action

    return _FakeMenu
