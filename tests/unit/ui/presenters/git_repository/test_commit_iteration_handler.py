# File responsibility: Unit tests for CommitIterationHandler.
"""Unit tests for CommitIterationHandler."""

from unittest.mock import MagicMock

import pytest

from freecad.history_wb.application.actions.result_models import Result
from freecad.history_wb.domain.git.models import GitIdentity, GitRepository
from freecad.history_wb.ui.presenters.git_repository.commit_iteration_handler import (
    CommitIterationHandler,
)


@pytest.fixture
def mock_get_staged_action() -> MagicMock:
    """Create a mock GetStagedFilePathsAction."""
    return MagicMock()


@pytest.fixture
def mock_commit_action() -> MagicMock:
    """Create a mock CommitStagingAction."""
    return MagicMock()


@pytest.fixture
def mock_get_identity_action() -> MagicMock:
    """Create a mock GetGitIdentityAction."""
    return MagicMock()


@pytest.fixture
def mock_author_handler() -> MagicMock:
    """Create a mock AuthorConfigurationHandler."""
    return MagicMock()


@pytest.fixture
def handler(
    mock_get_staged_action: MagicMock,
    mock_commit_action: MagicMock,
    mock_get_identity_action: MagicMock,
    mock_author_handler: MagicMock,
) -> CommitIterationHandler:
    """Create a CommitIterationHandler with mocked dependencies."""
    return CommitIterationHandler(
        get_staged_file_paths_action=mock_get_staged_action,
        commit_staging_action=mock_commit_action,
        get_git_identity_action=mock_get_identity_action,
        author_configuration_handler=mock_author_handler,
        show_save_iteration_dialog=MagicMock(),
        show_warning_message=MagicMock(),
        show_info_message=MagicMock(),
        show_error_message=MagicMock(),
    )


class TestCommitIterationHandler:
    """Tests for CommitIterationHandler."""

    def test_execute_skips_author_dialog_when_identity_configured(
        self,
        handler: CommitIterationHandler,
        mock_get_staged_action: MagicMock,
        mock_get_identity_action: MagicMock,
        mock_commit_action: MagicMock,
    ) -> None:
        """execute() skips author handler when identity is already configured."""
        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        mock_get_staged_action.execute.return_value = Result.success(["a.FCStd"])
        mock_get_identity_action.execute.return_value = Result.success(
            GitIdentity(name="User", email="user@example.com")
        )
        handler._show_save_iteration_dialog.return_value = "message"
        mock_commit_action.execute.return_value = Result.success(True)

        result = handler.execute(repo)

        assert result is True
        handler._author_handler.execute.assert_not_called()
        mock_commit_action.execute.assert_called_once_with(repo, "message")

    def test_execute_commits_successfully(
        self,
        handler: CommitIterationHandler,
        mock_get_staged_action: MagicMock,
        mock_get_identity_action: MagicMock,
        mock_commit_action: MagicMock,
        mock_author_handler: MagicMock,
    ) -> None:
        """execute() commits and returns True on full success."""
        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        mock_get_staged_action.execute.return_value = Result.success(["a.FCStd"])
        mock_get_identity_action.execute.return_value = Result.success(None)
        mock_author_handler.execute.return_value = True
        handler._show_save_iteration_dialog.return_value = "  commit message  "
        mock_commit_action.execute.return_value = Result.success(True)

        result = handler.execute(repo)

        assert result is True
        mock_commit_action.execute.assert_called_once_with(repo, "commit message")

    def test_execute_shows_info_when_no_staged_files(
        self,
        handler: CommitIterationHandler,
        mock_get_staged_action: MagicMock,
    ) -> None:
        """execute() shows info and returns False when no staged files."""
        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        mock_get_staged_action.execute.return_value = Result.success([])

        result = handler.execute(repo)

        assert result is False
        handler._show_info_message.assert_called_once()
        handler._author_handler.execute.assert_not_called()

    def test_execute_aborts_when_author_handler_fails(
        self,
        handler: CommitIterationHandler,
        mock_get_staged_action: MagicMock,
        mock_get_identity_action: MagicMock,
        mock_author_handler: MagicMock,
    ) -> None:
        """execute() returns False when author configuration fails."""
        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        mock_get_staged_action.execute.return_value = Result.success(["a.FCStd"])
        mock_get_identity_action.execute.return_value = Result.success(None)
        mock_author_handler.execute.return_value = False

        result = handler.execute(repo)

        assert result is False
        handler._show_save_iteration_dialog.assert_not_called()
        handler._commit_staging_action.execute.assert_not_called()

    def test_execute_aborts_on_dialog_cancel(
        self,
        handler: CommitIterationHandler,
        mock_get_staged_action: MagicMock,
        mock_get_identity_action: MagicMock,
        mock_author_handler: MagicMock,
    ) -> None:
        """execute() returns False when user cancels the save dialog."""
        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        mock_get_staged_action.execute.return_value = Result.success(["a.FCStd"])
        mock_get_identity_action.execute.return_value = Result.success(None)
        mock_author_handler.execute.return_value = True
        handler._show_save_iteration_dialog.return_value = None

        result = handler.execute(repo)

        assert result is False
        handler._commit_staging_action.execute.assert_not_called()

    def test_execute_warns_on_empty_message(
        self,
        handler: CommitIterationHandler,
        mock_get_staged_action: MagicMock,
        mock_get_identity_action: MagicMock,
        mock_author_handler: MagicMock,
    ) -> None:
        """execute() shows warning and returns False for empty commit message."""
        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        mock_get_staged_action.execute.return_value = Result.success(["a.FCStd"])
        mock_get_identity_action.execute.return_value = Result.success(None)
        mock_author_handler.execute.return_value = True
        handler._show_save_iteration_dialog.return_value = "   "

        result = handler.execute(repo)

        assert result is False
        handler._show_warning_message.assert_called_once()
        handler._commit_staging_action.execute.assert_not_called()

    def test_execute_shows_error_on_commit_failure(
        self,
        handler: CommitIterationHandler,
        mock_get_staged_action: MagicMock,
        mock_get_identity_action: MagicMock,
        mock_commit_action: MagicMock,
        mock_author_handler: MagicMock,
    ) -> None:
        """execute() shows error and returns False when commit fails."""
        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        mock_get_staged_action.execute.return_value = Result.success(["a.FCStd"])
        mock_get_identity_action.execute.return_value = Result.success(None)
        mock_author_handler.execute.return_value = True
        handler._show_save_iteration_dialog.return_value = "message"
        mock_commit_action.execute.return_value = Result.failure("git error")

        result = handler.execute(repo)

        assert result is False
        handler._show_error_message.assert_called_once()
