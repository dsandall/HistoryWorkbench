# SPDX-License-Identifier: LGPL-3.0-or-later
# File responsibility: Unit tests for UIRegistry.
# These tests verify that the UIRegistry correctly manages presenter registration,
# application state, and provides proper error handling when components are not initialized.
"""Unit tests for UIRegistry."""

import pytest

from freecad.history_wb.ui.registry import ui_registry
from freecad.history_wb.ui.state import ApplicationState


class TestUIRegistry:
    """Tests for UIRegistry class."""

    def setup_method(self) -> None:
        """Reset registry state before each test."""
        ui_registry.clear()

    def test_diff_presenter_returns_none_when_not_set(self) -> None:
        """diff_presenter property returns None when not initialized."""
        result = ui_registry.diff_presenter
        assert result is None

    def test_git_repository_presenter_returns_none_when_not_set(self) -> None:
        """git_repository_presenter property returns None when not initialized."""
        result = ui_registry.git_repository_presenter
        assert result is None

    def test_register_diff_presenter_stores_presenter(self) -> None:
        """register_diff_presenter() stores presenter and property returns it."""

        # Create a mock presenter
        class MockDiffPresenter:
            pass

        mock_presenter = MockDiffPresenter()

        # Register the presenter
        ui_registry.register_diff_presenter(mock_presenter)

        # Property should return the stored presenter
        assert ui_registry.diff_presenter is mock_presenter

    def test_register_git_repository_presenter_stores_presenter(self) -> None:
        """register_git_repository_presenter() stores presenter and property returns it."""

        # Create a mock presenter
        class MockGitRepositoryPresenter:
            pass

        mock_presenter = MockGitRepositoryPresenter()

        ui_registry.register_git_repository_presenter(mock_presenter)

        assert ui_registry.git_repository_presenter is mock_presenter

    def test_clear_resets_all_components(self) -> None:
        """clear() resets all components including command presenter."""

        # Register components
        class MockDiffPresenter:
            pass

        class MockGitRepositoryPresenter:
            pass

        class MockCommandPresenter:
            pass

        ui_registry.register_git_repository_presenter(MockGitRepositoryPresenter())
        ui_registry.register_diff_presenter(MockDiffPresenter())
        ui_registry.register_application_state(ApplicationState(git_repository=None))
        ui_registry.register_workbench_command_presenter(MockCommandPresenter())

        # Verify they're set
        assert ui_registry.git_repository_presenter is not None
        assert ui_registry.diff_presenter is not None
        assert ui_registry.application_state is not None
        assert ui_registry.workbench_command_presenter is not None

        # Clear the registry
        ui_registry.clear()

        # Verify all are reset to initial state
        assert ui_registry.diff_presenter is None
        assert ui_registry.git_repository_presenter is None
        with pytest.raises(RuntimeError):
            _ = ui_registry.application_state
        with pytest.raises(RuntimeError):
            _ = ui_registry.workbench_command_presenter

    def test_clear_presenters_clears_presenters_only(self) -> None:
        """clear_presenters() clears panel presenters but preserves app-scoped components."""

        # Register components
        class MockDiffPresenter:
            pass

        class MockGitRepositoryPresenter:
            pass

        class MockCommandPresenter:
            pass

        state = ApplicationState(git_repository=None)
        ui_registry.register_git_repository_presenter(MockGitRepositoryPresenter())
        ui_registry.register_diff_presenter(MockDiffPresenter())
        ui_registry.register_application_state(state)
        ui_registry.register_workbench_command_presenter(MockCommandPresenter())

        # Clear panel presenters only
        ui_registry.clear_presenters()

        # Panel presenters cleared
        assert ui_registry.diff_presenter is None
        assert ui_registry.git_repository_presenter is None

        # Application state preserved
        assert ui_registry.application_state is state

        # Command presenter preserved
        assert ui_registry.workbench_command_presenter is not None

    def test_clear_panel_presenters_clears_presenters_only(self) -> None:
        """clear_panel_presenters() clears panel presenters but preserves app-scoped components."""

        # Register components
        class MockDiffPresenter:
            pass

        class MockGitRepositoryPresenter:
            pass

        class MockCommandPresenter:
            pass

        state = ApplicationState(git_repository=None)
        ui_registry.register_git_repository_presenter(MockGitRepositoryPresenter())
        ui_registry.register_diff_presenter(MockDiffPresenter())
        ui_registry.register_application_state(state)
        ui_registry.register_workbench_command_presenter(MockCommandPresenter())

        # Clear panel presenters only
        ui_registry.clear_panel_presenters()

        # Panel presenters cleared
        assert ui_registry.diff_presenter is None
        assert ui_registry.git_repository_presenter is None

        # Application state preserved
        assert ui_registry.application_state is state

        # Command presenter preserved
        assert ui_registry.workbench_command_presenter is not None

    def test_workbench_command_presenter_raises_runtime_error_when_not_set(self) -> None:
        """workbench_command_presenter property raises RuntimeError when not initialized."""
        with pytest.raises(RuntimeError) as exc_info:
            _ = ui_registry.workbench_command_presenter

        assert "Workbench command presenter not initialized" in str(exc_info.value)
        assert "Workbench must be activated first" in str(exc_info.value)

    def test_register_workbench_command_presenter_stores_presenter(self) -> None:
        """register_workbench_command_presenter() stores presenter and property returns it."""

        class MockCommandPresenter:
            pass

        mock_presenter = MockCommandPresenter()

        ui_registry.register_workbench_command_presenter(mock_presenter)

        assert ui_registry.workbench_command_presenter is mock_presenter

    def test_application_state_can_be_imported_from_new_location(self) -> None:
        """ApplicationState can be imported from new location (ui.state)."""
        assert ApplicationState is not None

        # Verify it's the correct type
        state = ApplicationState(git_repository=None)
        assert state.git_repository is None

    def test_application_state_raises_runtime_error_when_not_set(self) -> None:
        """application_state property raises RuntimeError when not initialized."""
        with pytest.raises(RuntimeError) as exc_info:
            _ = ui_registry.application_state

        assert "Application state not initialized" in str(exc_info.value)
        assert "Workbench must be activated first" in str(exc_info.value)

    def test_register_application_state_stores_state_and_property_returns_it(self) -> None:
        """register_application_state() stores state and property returns it."""
        state = ApplicationState(git_repository=None)

        ui_registry.register_application_state(state)

        assert ui_registry.application_state is state
