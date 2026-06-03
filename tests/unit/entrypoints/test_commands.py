# SPDX-License-Identifier: LGPL-3.0-or-later
"""File responsibility: Tests for FreeCAD command entry points.

These tests verify that commands correctly instantiate handlers directly
from the container and DialogView, without requiring the diff panel to be open.
"""

from unittest.mock import MagicMock, Mock, patch

from freecad.history_wb.domain.git.models import GitRepository
from freecad.history_wb.entrypoints.commands import (
    _ConfigureAuthorCommand,
    _CommitCommand,
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

    @patch("freecad.history_wb._container.get_container")
    def test_activated_builds_handler_directly(
        self,
        mock_get_container: Mock,
    ) -> None:
        """Activated builds GitIgnoreHandler directly from container + DialogView."""
        mock_container = MagicMock()
        mock_container._freecad_port.get_main_window.return_value = MagicMock()
        mock_get_container.return_value = mock_container

        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        with (
            patch("freecad.history_wb.entrypoints.commands._get_application_repo_or_warn", return_value=repo),
            patch(
                "freecad.history_wb.ui.presenters.git_repository.gitignore_handler.GitIgnoreHandler"
            ) as MockHandler,
        ):
            mock_handler = MagicMock()
            MockHandler.return_value = mock_handler

            command = _UpdateGitIgnoreCommand()
            command.Activated()

            MockHandler.assert_called_once()
            mock_handler.execute.assert_called_once_with(repo)

    @patch("freecad.history_wb.entrypoints.commands._get_application_repo_or_warn")
    @patch("freecad.history_wb._container.get_container")
    def test_activated_returns_early_when_no_repo(
        self,
        mock_get_container: Mock,
        mock_get_repo: Mock,
    ) -> None:
        """Activated returns early when no repository is detected."""
        mock_container = MagicMock()
        mock_container._freecad_port.get_main_window.return_value = MagicMock()
        mock_get_container.return_value = mock_container
        mock_get_repo.return_value = None

        command = _UpdateGitIgnoreCommand()
        command.Activated()

        # Should not raise; handler not called
        mock_get_repo.assert_called_once()


class TestInitializeGitRepositoryCommand:
    """Tests for _InitializeGitRepositoryCommand."""

    @patch("freecad.history_wb._container.get_container")
    @patch("freecad.history_wb.ui.registry.ui_registry")
    def test_activated_builds_handler_directly(
        self,
        mock_ui_registry: Mock,
        mock_get_container: Mock,
    ) -> None:
        """Activated builds InitializeRepositoryHandler directly from container + DialogView."""
        mock_container = MagicMock()
        mock_container._freecad_port.get_main_window.return_value = MagicMock()
        mock_get_container.return_value = mock_container

        with (
            patch(
                "freecad.history_wb.ui.presenters.git_repository.initialize_repository_handler.InitializeRepositoryHandler"
            ) as MockHandler,
            patch("freecad.history_wb.entrypoints.commands._refresh_git_repository_presenter_if_open") as mock_refresh,
        ):
            mock_handler = MagicMock()
            mock_handler.execute.return_value = True
            MockHandler.return_value = mock_handler

            command = _InitializeGitRepositoryCommand()
            command.Activated()

            MockHandler.assert_called_once()
            mock_handler.execute.assert_called_once()
            mock_refresh.assert_called_once()

    @patch("freecad.history_wb._container.get_container")
    @patch("freecad.history_wb.ui.registry.ui_registry")
    def test_activated_skips_refresh_on_handler_failure(
        self,
        mock_ui_registry: Mock,
        mock_get_container: Mock,
    ) -> None:
        """Activated does not refresh presenter when handler returns False."""
        mock_container = MagicMock()
        mock_container._freecad_port.get_main_window.return_value = MagicMock()
        mock_get_container.return_value = mock_container

        with (
            patch(
                "freecad.history_wb.ui.presenters.git_repository.initialize_repository_handler.InitializeRepositoryHandler"
            ) as MockHandler,
            patch("freecad.history_wb.entrypoints.commands._refresh_git_repository_presenter_if_open") as mock_refresh,
        ):
            mock_handler = MagicMock()
            mock_handler.execute.return_value = False
            MockHandler.return_value = mock_handler

            command = _InitializeGitRepositoryCommand()
            command.Activated()

            mock_handler.execute.assert_called_once()
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
        with patch(
            "freecad.history_wb.entrypoints.commands._get_application_repo_or_warn", return_value=repo
        ):
            command = _OpenAllDocumentsInRepositoryCommand()
            command.Activated()

        mock_container.open_all_documents_in_repository_action.execute.assert_called_once_with(repo)

    @patch("freecad.history_wb.entrypoints.commands._get_application_repo_or_warn")
    @patch("freecad.history_wb._container.get_container")
    def test_activated_returns_early_when_no_repo(
        self,
        mock_get_container: Mock,
        mock_get_repo: Mock,
    ) -> None:
        """Activated returns early and does not execute action when no repo."""
        mock_container = MagicMock()
        mock_container._freecad_port.get_main_window.return_value = MagicMock()
        mock_get_container.return_value = mock_container
        mock_get_repo.return_value = None

        command = _OpenAllDocumentsInRepositoryCommand()
        command.Activated()

        mock_container.open_all_documents_in_repository_action.execute.assert_not_called()


class TestConfigureAuthorCommand:
    """Tests for _ConfigureAuthorCommand."""

    @patch("freecad.history_wb._container.get_container")
    def test_activated_builds_handler_directly(
        self,
        mock_get_container: Mock,
    ) -> None:
        """Activated builds AuthorConfigurationHandler directly from container + DialogView."""
        mock_container = MagicMock()
        mock_container._freecad_port.get_main_window.return_value = MagicMock()
        mock_get_container.return_value = mock_container

        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        with (
            patch("freecad.history_wb.entrypoints.commands._get_application_repo_or_warn", return_value=repo),
            patch(
                "freecad.history_wb.entrypoints.commands._build_author_configuration_handler"
            ) as MockBuilder,
        ):
            mock_handler = MagicMock()
            MockBuilder.return_value = mock_handler

            command = _ConfigureAuthorCommand()
            command.Activated()

            MockBuilder.assert_called_once()
            mock_handler.execute.assert_called_once_with(repo)

    @patch("freecad.history_wb.entrypoints.commands._get_application_repo_or_warn")
    @patch("freecad.history_wb._container.get_container")
    def test_activated_returns_early_when_no_repo(
        self,
        mock_get_container: Mock,
        mock_get_repo: Mock,
    ) -> None:
        """Activated returns early when no repository is detected."""
        mock_container = MagicMock()
        mock_container._freecad_port.get_main_window.return_value = MagicMock()
        mock_get_container.return_value = mock_container
        mock_get_repo.return_value = None

        command = _ConfigureAuthorCommand()
        command.Activated()

        mock_get_repo.assert_called_once()


class TestCommitCommand:
    """Tests for _CommitCommand."""

    @patch("freecad.history_wb._container.get_container")
    def test_activated_builds_handler_and_refreshes_on_success(
        self,
        mock_get_container: Mock,
    ) -> None:
        """Activated builds CommitIterationHandler, executes, and refreshes presenter on success."""
        mock_container = MagicMock()
        mock_container._freecad_port.get_main_window.return_value = MagicMock()
        mock_get_container.return_value = mock_container

        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        with (
            patch("freecad.history_wb.entrypoints.commands._get_application_repo_or_warn", return_value=repo),
            patch(
                "freecad.history_wb.entrypoints.commands._build_commit_iteration_handler"
            ) as MockBuilder,
            patch(
                "freecad.history_wb.entrypoints.commands._refresh_git_repository_presenter_if_open"
            ) as mock_refresh,
        ):
            mock_handler = MagicMock()
            mock_handler.execute.return_value = True
            MockBuilder.return_value = mock_handler

            command = _CommitCommand()
            command.Activated()

            MockBuilder.assert_called_once()
            mock_handler.execute.assert_called_once_with(repo)
            mock_refresh.assert_called_once()

    @patch("freecad.history_wb._container.get_container")
    def test_activated_skips_refresh_on_handler_failure(
        self,
        mock_get_container: Mock,
    ) -> None:
        """Activated does not refresh presenter when commit handler returns False."""
        mock_container = MagicMock()
        mock_container._freecad_port.get_main_window.return_value = MagicMock()
        mock_get_container.return_value = mock_container

        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        with (
            patch("freecad.history_wb.entrypoints.commands._get_application_repo_or_warn", return_value=repo),
            patch(
                "freecad.history_wb.entrypoints.commands._build_commit_iteration_handler"
            ) as MockBuilder,
            patch(
                "freecad.history_wb.entrypoints.commands._refresh_git_repository_presenter_if_open"
            ) as mock_refresh,
        ):
            mock_handler = MagicMock()
            mock_handler.execute.return_value = False
            MockBuilder.return_value = mock_handler

            command = _CommitCommand()
            command.Activated()

            mock_handler.execute.assert_called_once_with(repo)
            mock_refresh.assert_not_called()

    @patch("freecad.history_wb.entrypoints.commands._get_application_repo_or_warn")
    @patch("freecad.history_wb._container.get_container")
    def test_activated_returns_early_when_no_repo(
        self,
        mock_get_container: Mock,
        mock_get_repo: Mock,
    ) -> None:
        """Activated returns early when no repository is detected."""
        mock_container = MagicMock()
        mock_container._freecad_port.get_main_window.return_value = MagicMock()
        mock_get_container.return_value = mock_container
        mock_get_repo.return_value = None

        command = _CommitCommand()
        command.Activated()

        mock_get_repo.assert_called_once()

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

    def test_activated_returns_early_when_no_main_window(self) -> None:
        """Activated returns early when FreeCAD main window is not available."""
        mock_container = MagicMock()
        mock_container._freecad_port.get_main_window.return_value = None

        with patch("freecad.history_wb._container.get_container", return_value=mock_container):
            command = _CommitCommand()
            command.Activated()

        # Should not raise; no action executed
