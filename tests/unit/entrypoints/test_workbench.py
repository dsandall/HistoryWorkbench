# SPDX-License-Identifier: LGPL-3.0-or-later
# File responsibility: Unit tests for workbench lifecycle, state registration, and presenter cleanup.
"""Unit tests for HistoryWorkbench."""

from unittest.mock import MagicMock, patch

import pytest

from freecad.history_wb.ui.registry import ui_registry
from freecad.history_wb.ui.state import ApplicationState


@pytest.fixture(autouse=True)
def _reset_registry():
    """Reset registry before and after each test."""
    ui_registry.clear()
    yield
    ui_registry.clear()


class TestHistoryWorkbench:
    """Tests for HistoryWorkbench lifecycle."""

    def _get_workbench_class(self) -> type:
        """Import and return the workbench class under test."""
        import FreeCADGui as Gui  # type: ignore[import-not-found, no-redef]  # pylint: disable=import-error

        # Workbench class is only defined when FreeCADGui is available
        if Gui is None:
            pytest.skip("FreeCADGui not available")

        from freecad.history_wb.entrypoints.workbench import HistoryWorkbench
        return HistoryWorkbench

    def test_on_subwindow_closed_clears_presenters(self) -> None:
        """_on_subwindow_closed calls clear_presenters on the registry."""
        # FreeCADGui may not be available in unit test environment
        try:
            import FreeCADGui  # pylint: disable=import-error
        except ImportError:
            pytest.skip("FreeCADGui not available for workbench tests")

        WorkbenchClass = self._get_workbench_class()
        wb = WorkbenchClass()
        wb._subwindow = MagicMock()

        # Register some presenters first
        ui_registry.register_diff_presenter(MagicMock())
        ui_registry.register_git_repository_presenter(MagicMock())
        state = ApplicationState(git_repository=None)
        ui_registry.register_application_state(state)

        wb._on_subwindow_closed()

        # Presenters cleared
        assert wb._subwindow is None
        assert ui_registry.diff_presenter is None
        assert ui_registry.git_repository_presenter is None
        # Application state preserved
        assert ui_registry.application_state is state

    def test_on_subwindow_closed_preserves_command_presenter(self) -> None:
        """_on_subwindow_closed preserves workbench_command_presenter."""
        try:
            import FreeCADGui  # pylint: disable=import-error
        except ImportError:
            pytest.skip("FreeCADGui not available for workbench tests")

        WorkbenchClass = self._get_workbench_class()
        wb = WorkbenchClass()
        wb._subwindow = MagicMock()

        # Register components
        ui_registry.register_diff_presenter(MagicMock())
        ui_registry.register_git_repository_presenter(MagicMock())
        state = ApplicationState(git_repository=None)
        ui_registry.register_application_state(state)

        mock_command_presenter = MagicMock()
        ui_registry.register_workbench_command_presenter(mock_command_presenter)

        wb._on_subwindow_closed()

        # Command presenter preserved
        assert ui_registry.workbench_command_presenter is mock_command_presenter
        # Application state preserved
        assert ui_registry.application_state is state
        # Panel presenters cleared
        assert ui_registry.diff_presenter is None
        assert ui_registry.git_repository_presenter is None