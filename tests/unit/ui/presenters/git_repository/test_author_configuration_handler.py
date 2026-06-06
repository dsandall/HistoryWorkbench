# File responsibility: Unit tests for AuthorConfigurationHandler.
"""Unit tests for AuthorConfigurationHandler."""

from unittest.mock import MagicMock

import pytest

from freecad.history_wb.application.actions.result_models import Result
from freecad.history_wb.domain.git.models import GitIdentity, GitRepository
from freecad.history_wb.ui.presenters.git_repository.author_configuration_handler import (
    AuthorConfigurationHandler,
)
from freecad.history_wb.ui.views.diff_panel.dialogs import GitConfigDialogResult


@pytest.fixture
def mock_get_identity_action() -> MagicMock:
    """Create a mock GetGitIdentityAction."""
    return MagicMock()


@pytest.fixture
def mock_save_identity_action() -> MagicMock:
    """Create a mock SaveGitIdentityAction."""
    return MagicMock()


@pytest.fixture
def mock_can_write_global_action() -> MagicMock:
    """Create a mock CanWriteGlobalGitIdentityAction."""
    return MagicMock()


@pytest.fixture
def handler(
    mock_get_identity_action: MagicMock,
    mock_save_identity_action: MagicMock,
    mock_can_write_global_action: MagicMock,
) -> AuthorConfigurationHandler:
    """Create an AuthorConfigurationHandler with mocked dependencies."""
    return AuthorConfigurationHandler(
        get_git_identity_action=mock_get_identity_action,
        save_git_identity_action=mock_save_identity_action,
        can_write_global_git_identity_action=mock_can_write_global_action,
        show_configure_author_dialog=MagicMock(),
        show_warning_message=MagicMock(),
        show_error_message=MagicMock(),
    )


class TestAuthorConfigurationHandler:
    """Tests for AuthorConfigurationHandler."""

    def test_execute_saves_identity_successfully(
        self,
        handler: AuthorConfigurationHandler,
        mock_get_identity_action: MagicMock,
        mock_save_identity_action: MagicMock,
        mock_can_write_global_action: MagicMock,
    ) -> None:
        """execute() saves identity and returns True on success."""
        mock_get_identity_action.execute.return_value = Result.success(None)
        mock_save_identity_action.execute.return_value = Result.success(True)
        mock_can_write_global_action.execute.return_value = Result.success(True)

        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        dialog_result = GitConfigDialogResult(
            author_name="Test User",
            author_email="test@example.com",
            should_save_globally=False,
        )
        handler._show_configure_author_dialog.return_value = dialog_result

        result = handler.execute(repo)

        assert result is True
        mock_save_identity_action.execute.assert_called_once_with(
            repo,
            GitIdentity(name="Test User", email="test@example.com"),
            False,
        )

    def test_execute_returns_false_on_dialog_cancel(
        self,
        handler: AuthorConfigurationHandler,
        mock_get_identity_action: MagicMock,
        mock_can_write_global_action: MagicMock,
    ) -> None:
        """execute() returns False when user cancels the dialog."""
        mock_get_identity_action.execute.return_value = Result.success(None)
        mock_can_write_global_action.execute.return_value = Result.success(True)
        handler._show_configure_author_dialog.return_value = None

        repo = GitRepository(name="proj", absolute_path="/home/user/proj")

        result = handler.execute(repo)

        assert result is False
        handler._save_git_identity_action.execute.assert_not_called()

    def test_execute_requires_name_and_email(
        self,
        handler: AuthorConfigurationHandler,
        mock_get_identity_action: MagicMock,
        mock_can_write_global_action: MagicMock,
    ) -> None:
        """execute() returns False and shows warning when name/email is empty."""
        mock_get_identity_action.execute.return_value = Result.success(None)
        mock_can_write_global_action.execute.return_value = Result.success(True)

        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        dialog_result = GitConfigDialogResult(
            author_name="",
            author_email="test@example.com",
            should_save_globally=False,
        )
        handler._show_configure_author_dialog.return_value = dialog_result

        result = handler.execute(repo)

        assert result is False
        handler._show_warning_message.assert_called_once()
        handler._save_git_identity_action.execute.assert_not_called()

    def test_execute_retries_on_global_save_failure(
        self,
        handler: AuthorConfigurationHandler,
        mock_get_identity_action: MagicMock,
        mock_save_identity_action: MagicMock,
        mock_can_write_global_action: MagicMock,
    ) -> None:
        """execute() retries with local-only fallback when global save fails."""
        mock_get_identity_action.execute.return_value = Result.success(None)
        mock_can_write_global_action.execute.return_value = Result.success(True)

        repo = GitRepository(name="proj", absolute_path="/home/user/proj")

        # First call: global save fails
        # Second call: local save succeeds
        mock_save_identity_action.execute.side_effect = [
            Result.failure("Global save failed"),
            Result.success(True),
        ]

        dialog_result_global = GitConfigDialogResult(
            author_name="Test User",
            author_email="test@example.com",
            should_save_globally=True,
        )
        dialog_result_local = GitConfigDialogResult(
            author_name="Test User",
            author_email="test@example.com",
            should_save_globally=False,
        )
        handler._show_configure_author_dialog.side_effect = [
            dialog_result_global,
            dialog_result_local,
        ]

        result = handler.execute(repo)

        assert result is True
        assert mock_save_identity_action.execute.call_count == 2

    def test_execute_returns_false_on_local_save_failure(
        self,
        handler: AuthorConfigurationHandler,
        mock_get_identity_action: MagicMock,
        mock_save_identity_action: MagicMock,
        mock_can_write_global_action: MagicMock,
    ) -> None:
        """execute() returns False and shows error when local save fails."""
        mock_get_identity_action.execute.return_value = Result.success(None)
        mock_save_identity_action.execute.return_value = Result.failure("Local save failed")
        mock_can_write_global_action.execute.return_value = Result.success(True)

        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        dialog_result = GitConfigDialogResult(
            author_name="Test User",
            author_email="test@example.com",
            should_save_globally=False,
        )
        handler._show_configure_author_dialog.return_value = dialog_result

        result = handler.execute(repo)

        assert result is False
        handler._show_error_message.assert_called_once()

    def test_execute_uses_existing_identity_as_defaults(
        self,
        handler: AuthorConfigurationHandler,
        mock_get_identity_action: MagicMock,
        mock_save_identity_action: MagicMock,
        mock_can_write_global_action: MagicMock,
    ) -> None:
        """execute() pre-fills dialog with existing identity when available."""
        existing_identity = GitIdentity(name="Existing User", email="existing@example.com")
        mock_get_identity_action.execute.return_value = Result.success(existing_identity)
        mock_save_identity_action.execute.return_value = Result.success(True)
        mock_can_write_global_action.execute.return_value = Result.success(True)

        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        dialog_result = GitConfigDialogResult(
            author_name="Existing User",
            author_email="existing@example.com",
            should_save_globally=False,
        )
        handler._show_configure_author_dialog.return_value = dialog_result

        handler.execute(repo)

        # Verify dialog was called with the existing identity as initial values
        call_kwargs = handler._show_configure_author_dialog.call_args.kwargs
        assert call_kwargs["initial_values"] == GitConfigDialogResult(
            author_name="Existing User",
            author_email="existing@example.com",
            should_save_globally=False,
        )
