# SPDX-License-Identifier: LGPL-3.0-or-later
# File responsibility: Tests for FreeCAD command entry points.
# These tests verify that commands delegate to ui_registry.workbench_command_presenter
# for shared command flows, keeping them usable after the diff panel is closed.
"""Tests for FreeCAD command entry points."""

from unittest.mock import MagicMock, Mock, patch

from freecad.history_wb.domain.git.models import GitRepository
from freecad.history_wb.entrypoints.commands import (
    _CommitCommand,
    _ConfigureAuthorCommand,
    _InitializeGitRepositoryCommand,
    _OpenAllDocumentsInRepositoryCommand,
    _RecomputeAllOpenDocumentsCommand,
    _RefreshRepositoryCommand,
    _UpdateGitIgnoreCommand,
)


class TestRefreshRepositoryCommand:
    """Tests for _RefreshRepositoryCommand."""

    @patch("freecad.history_wb.ui.registry.ui_registry")
    def test_activated_calls_presenter_when_available(
        self,
        mock_ui_registry: Mock,
    ) -> None:
        """Activated delegates to presenter when panel is open."""
        mock_presenter = MagicMock()
        mock_ui_registry.git_repository_presenter = mock_presenter

        command = _RefreshRepositoryCommand()
        command.Activated()

        mock_presenter.refresh_repository_and_commits.assert_called_once_with()

    @patch("freecad.history_wb.ui.registry.ui_registry")
    @patch("freecad.history_wb._container.get_container")
    def test_activated_runs_detection_directly_when_presenter_none(
        self,
        mock_get_container: Mock,
        mock_ui_registry: Mock,
    ) -> None:
        """Activated runs find action directly and updates state when panel is closed."""
        mock_ui_registry.git_repository_presenter = None
        mock_container = MagicMock()
        mock_get_container.return_value = mock_container

        repo = GitRepository(name="test", absolute_path="/home/user/test")
        mock_result = MagicMock()
        mock_result.is_success = True
        mock_result.data = repo
        mock_container.find_active_git_repository_action.execute.return_value = mock_result

        command = _RefreshRepositoryCommand()
        command.Activated()

        mock_container.find_active_git_repository_action.execute.assert_called_once()
        assert mock_ui_registry.application_state.git_repository == repo

    @patch("freecad.history_wb.ui.registry.ui_registry")
    @patch("freecad.history_wb._container.get_container")
    def test_activated_clears_stale_repo_on_detection_failure(
        self,
        mock_get_container: Mock,
        mock_ui_registry: Mock,
    ) -> None:
        """Activated clears stale repo state when detection fails and panel is closed."""
        mock_ui_registry.git_repository_presenter = None
        mock_container = MagicMock()
        mock_get_container.return_value = mock_container

        mock_result = MagicMock()
        mock_result.is_success = False
        mock_container.find_active_git_repository_action.execute.return_value = mock_result

        # Pre-set stale repo
        mock_ui_registry.application_state.git_repository = GitRepository(
            name="old", absolute_path="/home/user/old"
        )

        command = _RefreshRepositoryCommand()
        command.Activated()

        assert mock_ui_registry.application_state.git_repository is None


class TestRecomputeAllOpenDocumentsCommand:
    """Tests for _RecomputeAllOpenDocumentsCommand."""

    @patch("freecad.history_wb._container.get_container")
    def test_activated_calls_application_action(self, mock_get_container: Mock) -> None:
        """Activated delegates to application action execute API."""
        mock_container = MagicMock()
        mock_get_container.return_value = mock_container

        command = _RecomputeAllOpenDocumentsCommand()
        command.Activated()

        mock_container.recompute_all_open_documents_action.execute.assert_called_once_with()


class TestUpdateGitIgnoreCommand:
    """Tests for _UpdateGitIgnoreCommand."""

    @patch("freecad.history_wb.ui.registry.ui_registry")
    def test_activated_delegates_to_command_presenter(
        self,
        mock_ui_registry: Mock,
    ) -> None:
        """Activated delegates to workbench_command_presenter.update_gitignore()."""
        mock_command_presenter = MagicMock()
        mock_ui_registry.workbench_command_presenter = mock_command_presenter

        command = _UpdateGitIgnoreCommand()
        command.Activated()

        mock_command_presenter.update_gitignore.assert_called_once()


class TestInitializeGitRepositoryCommand:
    """Tests for _InitializeGitRepositoryCommand."""

    @patch("freecad.history_wb.ui.registry.ui_registry")
    def test_activated_delegates_to_command_presenter(
        self,
        mock_ui_registry: Mock,
    ) -> None:
        """Activated delegates to workbench_command_presenter.initialize_repository()."""
        mock_command_presenter = MagicMock()
        mock_command_presenter.initialize_repository.return_value = True
        mock_ui_registry.workbench_command_presenter = mock_command_presenter

        with patch(
            "freecad.history_wb.entrypoints.commands._refresh_git_repository_presenter_if_open"
        ) as mock_refresh:
            command = _InitializeGitRepositoryCommand()
            command.Activated()

            mock_command_presenter.initialize_repository.assert_called_once()
            mock_refresh.assert_called_once()

    @patch("freecad.history_wb.ui.registry.ui_registry")
    def test_activated_skips_refresh_on_failure(
        self,
        mock_ui_registry: Mock,
    ) -> None:
        """Activated does not refresh presenter when command presenter returns False."""
        mock_command_presenter = MagicMock()
        mock_command_presenter.initialize_repository.return_value = False
        mock_ui_registry.workbench_command_presenter = mock_command_presenter

        with patch(
            "freecad.history_wb.entrypoints.commands._refresh_git_repository_presenter_if_open"
        ) as mock_refresh:
            command = _InitializeGitRepositoryCommand()
            command.Activated()

            mock_command_presenter.initialize_repository.assert_called_once()
            mock_refresh.assert_not_called()


class TestOpenAllDocumentsInRepositoryCommand:
    """Tests for _OpenAllDocumentsInRepositoryCommand."""

    @patch("freecad.history_wb._container.get_container")
    def test_activated_calls_open_action_when_repository_present(
        self,
        mock_get_container: Mock,
    ) -> None:
        """Activated executes open-all action when repository is set."""
        mock_container = MagicMock()
        mock_container._freecad_port.get_main_window.return_value = MagicMock()
        mock_get_container.return_value = mock_container

        repo = GitRepository(name="repo", absolute_path="/home/user/dir/repo")
        with (
            patch("freecad.history_wb.ui.registry.ui_registry") as mock_ui_registry,
            patch("freecad.history_wb.entrypoints.commands._create_dialog_view") as mock_create_dialog,
        ):
            mock_ui_registry.application_state.git_repository = repo
            mock_create_dialog.return_value = MagicMock()

            command = _OpenAllDocumentsInRepositoryCommand()
            command.Activated()

        mock_container.open_all_documents_in_repository_action.execute.assert_called_once_with(repo)

    @patch("freecad.history_wb.ui.registry.ui_registry")
    @patch("freecad.history_wb._container.get_container")
    def test_activated_returns_early_when_no_repo(
        self,
        mock_get_container: Mock,
        mock_ui_registry: Mock,
    ) -> None:
        """Activated returns early and does not execute action when no repo."""
        mock_container = MagicMock()
        mock_container._freecad_port.get_main_window.return_value = MagicMock()
        mock_get_container.return_value = mock_container
        mock_ui_registry.application_state.git_repository = None

        with patch("freecad.history_wb.entrypoints.commands._create_dialog_view") as mock_create_dialog:
            mock_dialog = MagicMock()
            mock_create_dialog.return_value = mock_dialog

            command = _OpenAllDocumentsInRepositoryCommand()
            command.Activated()

        mock_container.open_all_documents_in_repository_action.execute.assert_not_called()
        mock_dialog.show_warning_message.assert_called_once()


class TestConfigureAuthorCommand:
    """Tests for _ConfigureAuthorCommand."""

    @patch("freecad.history_wb.ui.registry.ui_registry")
    def test_activated_delegates_to_command_presenter(
        self,
        mock_ui_registry: Mock,
    ) -> None:
        """Activated delegates to workbench_command_presenter.configure_author()."""
        mock_command_presenter = MagicMock()
        mock_ui_registry.workbench_command_presenter = mock_command_presenter

        command = _ConfigureAuthorCommand()
        command.Activated()

        mock_command_presenter.configure_author.assert_called_once()


class TestCommitCommand:
    """Tests for _CommitCommand."""

    @patch("freecad.history_wb.ui.registry.ui_registry")
    def test_activated_delegates_to_command_presenter_and_refreshes_on_success(
        self,
        mock_ui_registry: Mock,
    ) -> None:
        """Activated delegates to command presenter, refreshes presenter on success."""
        mock_command_presenter = MagicMock()
        mock_command_presenter.save_iteration.return_value = True
        mock_ui_registry.workbench_command_presenter = mock_command_presenter

        with patch(
            "freecad.history_wb.entrypoints.commands._refresh_git_repository_presenter_if_open"
        ) as mock_refresh:
            command = _CommitCommand()
            command.Activated()

            mock_command_presenter.save_iteration.assert_called_once()
            mock_refresh.assert_called_once()

    @patch("freecad.history_wb.ui.registry.ui_registry")
    def test_activated_skips_refresh_on_failure(
        self,
        mock_ui_registry: Mock,
    ) -> None:
        """Activated does not refresh presenter when command presenter returns False."""
        mock_command_presenter = MagicMock()
        mock_command_presenter.save_iteration.return_value = False
        mock_ui_registry.workbench_command_presenter = mock_command_presenter

        with patch(
            "freecad.history_wb.entrypoints.commands._refresh_git_repository_presenter_if_open"
        ) as mock_refresh:
            command = _CommitCommand()
            command.Activated()

            mock_command_presenter.save_iteration.assert_called_once()
            mock_refresh.assert_not_called()

    def test_command_resources_correct(self) -> None:
        """Menu text, tooltips, icons are correct."""
        command = _CommitCommand()
        resources = command.GetResources()

        assert "MenuText" in resources
        assert "ToolTip" in resources
        assert "Pixmap" in resources
        assert resources["MenuText"] == "Save Iteration"
        assert "iteration" in resources["ToolTip"].lower()
        assert "Commit.svg" in resources["Pixmap"]

    def test_command_is_active_returns_true(self) -> None:
        """Command is always active."""
        command = _CommitCommand()
        assert command.IsActive() is True
