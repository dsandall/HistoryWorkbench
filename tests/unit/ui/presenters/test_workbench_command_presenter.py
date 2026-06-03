# SPDX-License-Identifier: LGPL-3.0-or-later
# File responsibility: Unit tests for WorkbenchCommandPresenter.
# These tests verify that the presenter correctly delegates to its handler
# instances, shows no-project warnings when no repo is set, and creates
# temporary DialogView instances parented to the FreeCAD main window.
"""Unit tests for WorkbenchCommandPresenter."""

from unittest.mock import MagicMock, patch

import pytest

from freecad.history_wb.domain.git.models import GitRepository
from freecad.history_wb.ui.presenters.workbench_command_presenter import WorkbenchCommandPresenter


@pytest.fixture
def mock_application_state() -> MagicMock:
    """Create a mock ApplicationState."""
    return MagicMock()


@pytest.fixture
def mock_main_window() -> MagicMock:
    """Create a mock FreeCAD main window widget."""
    return MagicMock()


@pytest.fixture
def mock_get_main_window(mock_main_window: MagicMock) -> MagicMock:
    """Create a callable that returns the mock main window."""
    return MagicMock(return_value=mock_main_window)


@pytest.fixture
def mock_actions() -> dict:
    """Create a dict of mock container actions."""
    return {
        "get_staged_file_paths_action": MagicMock(),
        "commit_staging_action": MagicMock(),
        "get_git_identity_action": MagicMock(),
        "save_git_identity_action": MagicMock(),
        "can_write_global_git_identity_action": MagicMock(),
        "get_git_repository_init_candidates_action": MagicMock(),
        "initialize_git_repository_action": MagicMock(),
        "get_gitignore_content_action": MagicMock(),
        "update_gitignore_action": MagicMock(),
    }


@pytest.fixture
def presenter(
    mock_application_state: MagicMock,
    mock_get_main_window: MagicMock,
    mock_actions: dict,
) -> WorkbenchCommandPresenter:
    """Create a WorkbenchCommandPresenter with mocked dependencies."""
    return WorkbenchCommandPresenter(
        application_state=mock_application_state,
        get_main_window=mock_get_main_window,
        **mock_actions,
    )


class TestConfigureAuthor:
    """Tests for configure_author flow."""

    def test_configure_author_warns_when_no_repo(
        self,
        presenter: WorkbenchCommandPresenter,
        mock_application_state: MagicMock,
        mock_main_window: MagicMock,
    ) -> None:
        """configure_author() returns False and shows warning when no repo."""
        mock_application_state.git_repository = None

        with patch.object(presenter, "_show_warning_message") as mock_warn:
            result = presenter.configure_author()

        assert result is False
        mock_warn.assert_called_once()
        assert "No Project" in str(mock_warn.call_args)

    def test_configure_author_delegates_to_handler(
        self,
        presenter: WorkbenchCommandPresenter,
        mock_application_state: MagicMock,
    ) -> None:
        """configure_author() delegates to AuthorConfigurationHandler when repo exists."""
        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        mock_application_state.git_repository = repo

        with patch.object(presenter._author_handler, "execute", return_value=True) as mock_exec:
            result = presenter.configure_author()

        mock_exec.assert_called_once_with(repo)
        assert result is True

    def test_configure_author_returns_handler_result(
        self,
        presenter: WorkbenchCommandPresenter,
        mock_application_state: MagicMock,
    ) -> None:
        """configure_author() returns the handler's execute result."""
        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        mock_application_state.git_repository = repo

        with patch.object(presenter._author_handler, "execute", return_value=False) as mock_exec:
            result = presenter.configure_author()

        mock_exec.assert_called_once_with(repo)
        assert result is False


class TestSaveIteration:
    """Tests for save_iteration flow."""

    def test_save_iteration_warns_when_no_repo(
        self,
        presenter: WorkbenchCommandPresenter,
        mock_application_state: MagicMock,
    ) -> None:
        """save_iteration() returns False and shows warning when no repo."""
        mock_application_state.git_repository = None

        with patch.object(presenter, "_show_warning_message") as mock_warn:
            result = presenter.save_iteration()

        assert result is False
        mock_warn.assert_called_once()
        assert "No Project" in str(mock_warn.call_args)

    def test_save_iteration_delegates_to_handler(
        self,
        presenter: WorkbenchCommandPresenter,
        mock_application_state: MagicMock,
    ) -> None:
        """save_iteration() delegates to CommitIterationHandler when repo exists."""
        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        mock_application_state.git_repository = repo

        with patch.object(presenter._commit_handler, "execute", return_value=True) as mock_exec:
            result = presenter.save_iteration()

        mock_exec.assert_called_once_with(repo)
        assert result is True

    def test_save_iteration_returns_handler_result(
        self,
        presenter: WorkbenchCommandPresenter,
        mock_application_state: MagicMock,
    ) -> None:
        """save_iteration() returns the handler's execute result."""
        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        mock_application_state.git_repository = repo

        with patch.object(presenter._commit_handler, "execute", return_value=False) as mock_exec:
            result = presenter.save_iteration()

        mock_exec.assert_called_once_with(repo)
        assert result is False


class TestInitializeRepository:
    """Tests for initialize_repository flow."""

    def test_initialize_repository_delegates_to_handler(
        self,
        presenter: WorkbenchCommandPresenter,
    ) -> None:
        """initialize_repository() delegates to InitializeRepositoryHandler."""
        with patch.object(presenter._init_repo_handler, "execute", return_value=True) as mock_exec:
            result = presenter.initialize_repository()

        mock_exec.assert_called_once()
        assert result is True

    def test_initialize_repository_returns_handler_result(
        self,
        presenter: WorkbenchCommandPresenter,
    ) -> None:
        """initialize_repository() returns the handler's execute result."""
        with patch.object(presenter._init_repo_handler, "execute", return_value=False) as mock_exec:
            result = presenter.initialize_repository()

        mock_exec.assert_called_once()
        assert result is False


class TestUpdateGitignore:
    """Tests for update_gitignore flow."""

    def test_update_gitignore_warns_when_no_repo(
        self,
        presenter: WorkbenchCommandPresenter,
        mock_application_state: MagicMock,
    ) -> None:
        """update_gitignore() shows warning and returns when no repo."""
        mock_application_state.git_repository = None

        with patch.object(presenter, "_show_warning_message") as mock_warn:
            result = presenter.update_gitignore()

        assert result is None
        mock_warn.assert_called_once()
        assert "No Project" in str(mock_warn.call_args)

    def test_update_gitignore_delegates_to_handler(
        self,
        presenter: WorkbenchCommandPresenter,
        mock_application_state: MagicMock,
    ) -> None:
        """update_gitignore() delegates to GitIgnoreHandler when repo exists."""
        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        mock_application_state.git_repository = repo

        with patch.object(presenter._gitignore_handler, "execute") as mock_exec:
            presenter.update_gitignore()

        mock_exec.assert_called_once_with(repo)


class TestDialogHelpers:
    """Tests for dialog helper methods."""

    def test_create_dialog_view_raises_when_no_main_window(
        self,
        mock_application_state: MagicMock,
        mock_actions: dict,
    ) -> None:
        """_create_dialog_view() raises RuntimeError when main window is None."""
        get_main_window = MagicMock(return_value=None)
        presenter = WorkbenchCommandPresenter(
            application_state=mock_application_state,
            get_main_window=get_main_window,
            **mock_actions,
        )

        with pytest.raises(RuntimeError, match="FreeCAD main window not available"):
            presenter._create_dialog_view()

    def test_show_warning_message_creates_dialog_view(
        self,
        presenter: WorkbenchCommandPresenter,
        mock_main_window: MagicMock,
    ) -> None:
        """_show_warning_message creates a DialogView and calls show_warning_message."""
        with patch.object(presenter, "_create_dialog_view") as mock_create:
            mock_dialog = MagicMock()
            mock_create.return_value = mock_dialog

            presenter._show_warning_message("Title", "Message")

            mock_create.assert_called_once()
            mock_dialog.show_warning_message.assert_called_once_with("Title", "Message")

    def test_show_info_message_creates_dialog_view(
        self,
        presenter: WorkbenchCommandPresenter,
    ) -> None:
        """_show_info_message creates a DialogView and calls show_info_message."""
        with patch.object(presenter, "_create_dialog_view") as mock_create:
            mock_dialog = MagicMock()
            mock_create.return_value = mock_dialog

            presenter._show_info_message("Title", "Message")

            mock_create.assert_called_once()
            mock_dialog.show_info_message.assert_called_once_with("Title", "Message")

    def test_show_error_message_creates_dialog_view(
        self,
        presenter: WorkbenchCommandPresenter,
    ) -> None:
        """_show_error_message creates a DialogView and calls show_error_message."""
        with patch.object(presenter, "_create_dialog_view") as mock_create:
            mock_dialog = MagicMock()
            mock_create.return_value = mock_dialog

            presenter._show_error_message("Title", "Message")

            mock_create.assert_called_once()
            mock_dialog.show_error_message.assert_called_once_with("Title", "Message")

    def test_show_warning_message_logs_fallback_on_no_main_window(
        self,
        mock_application_state: MagicMock,
        mock_actions: dict,
    ) -> None:
        """_show_warning_message logs a warning when main window is not available."""
        get_main_window = MagicMock(return_value=None)
        presenter = WorkbenchCommandPresenter(
            application_state=mock_application_state,
            get_main_window=get_main_window,
            **mock_actions,
        )

        # Should not raise; falls back to logging
        presenter._show_warning_message("Title", "Message")


class TestHandlerInstances:
    """Tests for handler instance ownership."""

    def test_single_author_handler_instance(
        self,
        presenter: WorkbenchCommandPresenter,
        mock_application_state: MagicMock,
    ) -> None:
        """Presenter reuses the same AuthorConfigurationHandler across calls."""
        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        mock_application_state.git_repository = repo

        with patch.object(presenter._author_handler, "execute", return_value=True) as mock_exec:
            presenter.configure_author()
            presenter.configure_author()

        assert mock_exec.call_count == 2

    def test_single_commit_handler_instance(
        self,
        presenter: WorkbenchCommandPresenter,
        mock_application_state: MagicMock,
    ) -> None:
        """Presenter reuses the same CommitIterationHandler across calls."""
        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        mock_application_state.git_repository = repo

        with patch.object(presenter._commit_handler, "execute", return_value=True) as mock_exec:
            presenter.save_iteration()
            presenter.save_iteration()

        assert mock_exec.call_count == 2

    def test_single_init_repo_handler_instance(
        self,
        presenter: WorkbenchCommandPresenter,
    ) -> None:
        """Presenter reuses the same InitializeRepositoryHandler across calls."""
        with patch.object(presenter._init_repo_handler, "execute", return_value=True) as mock_exec:
            presenter.initialize_repository()
            presenter.initialize_repository()

        assert mock_exec.call_count == 2

    def test_single_gitignore_handler_instance(
        self,
        presenter: WorkbenchCommandPresenter,
        mock_application_state: MagicMock,
    ) -> None:
        """Presenter reuses the same GitIgnoreHandler across calls."""
        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        mock_application_state.git_repository = repo

        with patch.object(presenter._gitignore_handler, "execute") as mock_exec:
            presenter.update_gitignore()
            presenter.update_gitignore()

        assert mock_exec.call_count == 2
