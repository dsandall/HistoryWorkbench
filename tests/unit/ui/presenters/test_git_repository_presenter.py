# SPDX-License-Identifier: LGPL-3.0-or-later
# File responsibility: Unit tests for GitRepositoryPresenter.
# These tests verify that the presenter correctly orchestrates git repository
# detection, commit loading, and delegates to handlers for identity and commit flows.
"""Unit tests for GitRepositoryPresenter."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from freecad.history_wb.domain.git.models import GitCommit, GitRepository
from freecad.history_wb.ui.presenters.git_repository_presenter import GitRepositoryPresenter


@pytest.fixture
def mock_view() -> MagicMock:
    """Create a mock HistoryView."""
    return MagicMock()


@pytest.fixture
def mock_dialog_view() -> MagicMock:
    """Create a mock DialogView."""
    return MagicMock()


@pytest.fixture
def mock_find_action() -> MagicMock:
    """Create a mock FindActiveGitRepositoryAction."""
    return MagicMock()


@pytest.fixture
def mock_get_commits_action() -> MagicMock:
    """Create a mock GetCommitsAction."""
    return MagicMock()


@pytest.fixture
def mock_get_staged_file_paths_action() -> MagicMock:
    """Create a mock GetStagedFilePathsAction."""
    return MagicMock()


@pytest.fixture
def mock_commit_staging_action() -> MagicMock:
    """Create a mock CommitStagingAction."""
    return MagicMock()


@pytest.fixture
def mock_get_git_identity_action() -> MagicMock:
    """Create a mock GetGitIdentityAction."""
    return MagicMock()


@pytest.fixture
def mock_save_git_identity_action() -> MagicMock:
    """Create a mock SaveGitIdentityAction."""
    return MagicMock()


@pytest.fixture
def mock_can_write_global_git_identity_action() -> MagicMock:
    """Create a mock CanWriteGlobalGitIdentityAction."""
    return MagicMock()


@pytest.fixture
def mock_get_git_repository_init_candidates_action() -> MagicMock:
    """Create a mock GetGitRepositoryInitCandidatesAction."""
    return MagicMock()


@pytest.fixture
def mock_initialize_git_repository_action() -> MagicMock:
    """Create a mock InitializeGitRepositoryAction."""
    return MagicMock()


@pytest.fixture
def mock_get_gitignore_content_action() -> MagicMock:
    """Create a mock GetGitIgnoreContentAction."""
    return MagicMock()


@pytest.fixture
def mock_update_gitignore_action() -> MagicMock:
    """Create a mock UpdateGitIgnoreAction."""
    return MagicMock()


@pytest.fixture
def mock_application_state() -> MagicMock:
    """Create a mock ApplicationState."""
    return MagicMock()


@pytest.fixture
def presenter(
    mock_view: MagicMock,
    mock_dialog_view: MagicMock,
    mock_find_action: MagicMock,
    mock_get_commits_action: MagicMock,
    mock_get_staged_file_paths_action: MagicMock,
    mock_commit_staging_action: MagicMock,
    mock_get_git_identity_action: MagicMock,
    mock_save_git_identity_action: MagicMock,
    mock_can_write_global_git_identity_action: MagicMock,
    mock_get_git_repository_init_candidates_action: MagicMock,
    mock_initialize_git_repository_action: MagicMock,
    mock_get_gitignore_content_action: MagicMock,
    mock_update_gitignore_action: MagicMock,
    mock_application_state: MagicMock,
) -> GitRepositoryPresenter:
    """Create a GitRepositoryPresenter instance with mocked dependencies."""
    return GitRepositoryPresenter(
        history_view=mock_view,
        dialog_view=mock_dialog_view,
        find_git_repo_action=mock_find_action,
        get_commits_action=mock_get_commits_action,
        get_staged_file_paths_action=mock_get_staged_file_paths_action,
        commit_staging_action=mock_commit_staging_action,
        get_git_identity_action=mock_get_git_identity_action,
        save_git_identity_action=mock_save_git_identity_action,
        can_write_global_git_identity_action=mock_can_write_global_git_identity_action,
        get_git_repository_init_candidates_action=mock_get_git_repository_init_candidates_action,
        initialize_git_repository_action=mock_initialize_git_repository_action,
        get_gitignore_content_action=mock_get_gitignore_content_action,
        update_gitignore_action=mock_update_gitignore_action,
        application_state=mock_application_state,
        clear_doc_diffs=MagicMock(),
    )


class TestGitRepositoryPresenter:
    """Tests for GitRepositoryPresenter."""

    def test_on_workbench_activated_with_successful_detection(
        self,
        presenter: GitRepositoryPresenter,
        mock_view: MagicMock,
        mock_find_action: MagicMock,
        mock_application_state: MagicMock,
    ) -> None:
        """on_workbench_activated() updates state and view when detection succeeds."""
        repo = GitRepository(name="test_project", absolute_path="/home/user/test_project")
        mock_result = MagicMock()
        mock_result.is_success = True
        mock_result.data = repo
        mock_find_action.execute.return_value = mock_result

        presenter.on_workbench_activated()

        mock_find_action.execute.assert_called_once()
        mock_application_state.git_repository = repo
        mock_view.show_repository.assert_called_once_with(repo)

    def test_on_workbench_activated_with_failed_detection(
        self,
        presenter: GitRepositoryPresenter,
        mock_view: MagicMock,
        mock_find_action: MagicMock,
        mock_application_state: MagicMock,
    ) -> None:
        """on_workbench_activated() sets state to None and shows no repo message on failure."""
        mock_result = MagicMock()
        mock_result.is_success = False
        mock_result.message = "No active document"
        mock_find_action.execute.return_value = mock_result

        presenter.on_workbench_activated()

        mock_find_action.execute.assert_called_once()
        mock_application_state.git_repository = None
        mock_view.show_repository.assert_called_once_with(None)
        mock_view.show_commits.assert_called_once_with([], show_special_items=False)

    def test_on_workbench_activated_with_none_repository(
        self,
        presenter: GitRepositoryPresenter,
        mock_view: MagicMock,
        mock_find_action: MagicMock,
        mock_application_state: MagicMock,
    ) -> None:
        """on_workbench_activated() handles case where action returns None repository."""
        mock_result = MagicMock()
        mock_result.is_success = True
        mock_result.data = None  # Action succeeded but found no repo
        mock_find_action.execute.return_value = mock_result

        presenter.on_workbench_activated()

        mock_find_action.execute.assert_called_once()
        mock_application_state.git_repository = None
        mock_view.show_repository.assert_called_once_with(None)

    def test_presenter_initialization_stores_dependencies(
        self,
        mock_view: MagicMock,
        mock_dialog_view: MagicMock,
        mock_find_action: MagicMock,
        mock_get_commits_action: MagicMock,
        mock_get_staged_file_paths_action: MagicMock,
        mock_commit_staging_action: MagicMock,
        mock_get_git_identity_action: MagicMock,
        mock_save_git_identity_action: MagicMock,
        mock_can_write_global_git_identity_action: MagicMock,
        mock_get_git_repository_init_candidates_action: MagicMock,
        mock_initialize_git_repository_action: MagicMock,
        mock_get_gitignore_content_action: MagicMock,
        mock_update_gitignore_action: MagicMock,
        mock_application_state: MagicMock,
    ) -> None:
        """Presenter stores all dependencies correctly on initialization."""
        presenter = GitRepositoryPresenter(
            history_view=mock_view,
            dialog_view=mock_dialog_view,
            find_git_repo_action=mock_find_action,
            get_commits_action=mock_get_commits_action,
            get_staged_file_paths_action=mock_get_staged_file_paths_action,
            commit_staging_action=mock_commit_staging_action,
            get_git_identity_action=mock_get_git_identity_action,
            save_git_identity_action=mock_save_git_identity_action,
            can_write_global_git_identity_action=mock_can_write_global_git_identity_action,
            get_git_repository_init_candidates_action=mock_get_git_repository_init_candidates_action,
            initialize_git_repository_action=mock_initialize_git_repository_action,
            get_gitignore_content_action=mock_get_gitignore_content_action,
            update_gitignore_action=mock_update_gitignore_action,
            application_state=mock_application_state,
            clear_doc_diffs=MagicMock(),
        )

        assert presenter._history_view is mock_view
        assert presenter._dialog_view is mock_dialog_view
        assert presenter._find_git_repo_action is mock_find_action
        assert presenter._get_commits_action is mock_get_commits_action
        assert presenter._application_state is mock_application_state

    def test_refresh_repository_and_commits_with_successful_detection(
        self,
        presenter: GitRepositoryPresenter,
        mock_view: MagicMock,
        mock_find_action: MagicMock,
        mock_application_state: MagicMock,
    ) -> None:
        """refresh_repository_and_commits() updates state and view when detection succeeds."""
        repo = GitRepository(name="test_project", absolute_path="/home/user/test_project")
        mock_result = MagicMock()
        mock_result.is_success = True
        mock_result.data = repo
        mock_find_action.execute.return_value = mock_result

        presenter.refresh_repository_and_commits()

        mock_find_action.execute.assert_called_once()
        mock_application_state.git_repository = repo
        mock_view.show_repository.assert_called_once_with(repo)

    def test_refresh_repository_and_commits_with_failed_detection(
        self,
        presenter: GitRepositoryPresenter,
        mock_view: MagicMock,
        mock_find_action: MagicMock,
        mock_application_state: MagicMock,
    ) -> None:
        """refresh_repository_and_commits() sets state to None and shows no repo message on failure."""
        mock_result = MagicMock()
        mock_result.is_success = False
        mock_result.message = "No active document"
        mock_find_action.execute.return_value = mock_result

        presenter.refresh_repository_and_commits()

        mock_find_action.execute.assert_called_once()
        mock_application_state.git_repository = None
        mock_view.show_repository.assert_called_once_with(None)
        mock_view.show_commits.assert_called_once_with([], show_special_items=False)

    def test_refresh_repository_and_commits_with_none_repository(
        self,
        presenter: GitRepositoryPresenter,
        mock_view: MagicMock,
        mock_find_action: MagicMock,
        mock_application_state: MagicMock,
    ) -> None:
        """refresh_repository_and_commits() handles case where action returns None repository."""
        mock_result = MagicMock()
        mock_result.is_success = True
        mock_result.data = None  # Action succeeded but found no repo
        mock_find_action.execute.return_value = mock_result

        presenter.refresh_repository_and_commits()

        mock_find_action.execute.assert_called_once()
        mock_application_state.git_repository = None
        mock_view.show_repository.assert_called_once_with(None)

    def test_on_workbench_activated_delegates_to_refresh_repository_and_commits(
        self,
        presenter: GitRepositoryPresenter,
    ) -> None:
        """on_workbench_activated() delegates to refresh_repository_and_commits()."""
        with patch.object(presenter, "refresh_repository_and_commits") as mock_refresh:
            presenter.on_workbench_activated()

        mock_refresh.assert_called_once_with()


class TestSaveIterationFlow:
    """Tests for save-iteration orchestration in GitRepositoryPresenter."""

    def test_save_iteration_warns_when_no_repository(
        self,
        presenter: GitRepositoryPresenter,
        mock_application_state: MagicMock,
    ) -> None:
        """No repository shows warning and exits early."""
        mock_application_state.git_repository = None
        mock_handler = MagicMock()
        presenter._commit_handler = mock_handler

        presenter.save_iteration()

        presenter._dialog_view.show_warning_message.assert_called_once()
        mock_handler.execute.assert_not_called()

    def test_save_iteration_delegates_to_commit_handler(
        self,
        presenter: GitRepositoryPresenter,
        mock_application_state: MagicMock,
    ) -> None:
        """Presenter delegates save-iteration to CommitIterationHandler."""
        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        mock_application_state.git_repository = repo
        mock_handler = MagicMock()
        mock_handler.execute.return_value = True
        presenter._commit_handler = mock_handler

        with patch.object(presenter, "refresh_repository_and_commits") as refresh:
            presenter.save_iteration()

        mock_handler.execute.assert_called_once_with(repo)
        refresh.assert_called_once_with()

    def test_save_iteration_skips_refresh_on_handler_failure(
        self,
        presenter: GitRepositoryPresenter,
        mock_application_state: MagicMock,
    ) -> None:
        """Presenter does not refresh when commit handler returns False."""
        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        mock_application_state.git_repository = repo
        mock_handler = MagicMock()
        mock_handler.execute.return_value = False
        presenter._commit_handler = mock_handler

        with patch.object(presenter, "refresh_repository_and_commits") as refresh:
            presenter.save_iteration()

        mock_handler.execute.assert_called_once_with(repo)
        refresh.assert_not_called()


class TestConfigureAuthorFlow:
    """Tests for configure-author orchestration in GitRepositoryPresenter."""

    def test_configure_author_warns_when_no_repository(
        self,
        presenter: GitRepositoryPresenter,
        mock_application_state: MagicMock,
    ) -> None:
        """No repository shows warning and exits early."""
        mock_application_state.git_repository = None

        presenter.configure_author()

        presenter._dialog_view.show_warning_message.assert_called_once()

    def test_configure_author_delegates_to_author_handler(
        self,
        presenter: GitRepositoryPresenter,
        mock_application_state: MagicMock,
    ) -> None:
        """Presenter delegates configure-author to AuthorConfigurationHandler."""
        repo = GitRepository(name="proj", absolute_path="/home/user/proj")
        mock_application_state.git_repository = repo
        mock_handler = MagicMock()
        presenter._author_handler = mock_handler

        presenter.configure_author()

        mock_handler.execute.assert_called_once_with(repo)


class TestCommitLoading:
    """Tests for GitRepositoryPresenter commit loading functionality."""

    def test_load_commits_calls_show_commits_on_success(
        self,
        presenter: GitRepositoryPresenter,
        mock_view: MagicMock,
        mock_get_commits_action: MagicMock,
    ) -> None:
        """_load_commits() calls show_commits with commits on success."""
        commits = [
            GitCommit(
                id="a1b2c3d4e5f67890",
                message="Test commit",
                author="Test Author",
                timestamp=datetime.fromisoformat("2024-01-15T10:30:00+00:00"),
            ),
        ]
        mock_result = MagicMock()
        mock_result.is_success = True
        mock_result.data = commits
        mock_get_commits_action.execute.return_value = mock_result

        repo = GitRepository(name="test_project", absolute_path="/home/user/test_project")

        presenter._load_commits(repo)

        mock_get_commits_action.execute.assert_called_once_with(repo)
        mock_view.show_commits.assert_called_once_with(commits)

    def test_load_commits_shows_empty_list_on_failure(
        self,
        presenter: GitRepositoryPresenter,
        mock_view: MagicMock,
        mock_get_commits_action: MagicMock,
    ) -> None:
        """_load_commits() shows empty list when action fails."""
        mock_result = MagicMock()
        mock_result.is_success = False
        mock_result.message = "Git error"
        mock_get_commits_action.execute.return_value = mock_result

        repo = GitRepository(name="test_project", absolute_path="/home/user/test_project")

        presenter._load_commits(repo)

        mock_view.show_commits.assert_called_once_with([])

    def test_detect_git_repository_loads_commits_on_success(
        self,
        presenter: GitRepositoryPresenter,
        mock_view: MagicMock,
        mock_find_action: MagicMock,
        mock_get_commits_action: MagicMock,
        mock_application_state: MagicMock,
    ) -> None:
        """_detect_git_repository() loads commits after detecting repository."""
        repo = GitRepository(name="test_project", absolute_path="/home/user/test_project")

        # Mock find action to return repo
        mock_find_result = MagicMock()
        mock_find_result.is_success = True
        mock_find_result.data = repo
        mock_find_action.execute.return_value = mock_find_result

        # Mock get commits action to return commits
        commits = [
            GitCommit(
                id="a1b2c3d",
                message="Test",
                author="Test",
                timestamp=datetime.fromisoformat("2024-01-15T10:30:00+00:00"),
            )
        ]
        mock_commit_result = MagicMock()
        mock_commit_result.is_success = True
        mock_commit_result.data = commits
        mock_get_commits_action.execute.return_value = mock_commit_result

        presenter._detect_git_repository()

        mock_get_commits_action.execute.assert_called_once_with(repo)
        mock_view.show_commits.assert_called_once()

    def test_load_more_commits_loads_next_page(self, presenter: GitRepositoryPresenter) -> None:
        """Scroll near bottom loads next commit page with skip offset."""
        repo = GitRepository(name="test_project", absolute_path="/home/user/test_project")
        presenter._application_state.git_repository = repo
        presenter._active_repo_path = repo.absolute_path
        presenter._loaded_commit_count = 20
        presenter._has_more_commits = True

        commits = [
            GitCommit(
                id="z9y8x7w",
                message="Older commit",
                author="Dev",
                timestamp=datetime.fromisoformat("2024-01-10T10:30:00+00:00"),
            )
        ]
        result = MagicMock()
        result.is_success = True
        result.data = commits
        presenter._get_commits_action.execute.return_value = result

        presenter.load_more_commits()

        presenter._get_commits_action.execute.assert_called_once_with(repo, limit=20, skip=20)
        presenter._history_view.append_commits.assert_called_once_with(commits)

    def test_load_more_commits_skips_when_no_more(self, presenter: GitRepositoryPresenter) -> None:
        """Scroll near bottom does nothing when no further pages exist."""
        repo = GitRepository(name="test_project", absolute_path="/home/user/test_project")
        presenter._application_state.git_repository = repo
        presenter._active_repo_path = repo.absolute_path
        presenter._has_more_commits = False

        presenter.load_more_commits()

        presenter._get_commits_action.execute.assert_not_called()

    def test_load_more_commits_throttles_rapid_calls(self, presenter: GitRepositoryPresenter) -> None:
        """Rapid bottom-scroll callbacks are throttled to one load call."""
        repo = GitRepository(name="test_project", absolute_path="/home/user/test_project")
        presenter._application_state.git_repository = repo
        presenter._active_repo_path = repo.absolute_path
        presenter._loaded_commit_count = 20
        presenter._has_more_commits = True

        result = MagicMock()
        result.is_success = True
        result.data = []
        presenter._get_commits_action.execute.return_value = result

        with patch("freecad.history_wb.ui.presenters.git_repository_presenter.monotonic", return_value=10.0):
            presenter.load_more_commits()
            presenter.load_more_commits()

        presenter._get_commits_action.execute.assert_called_once_with(repo, limit=20, skip=20)
