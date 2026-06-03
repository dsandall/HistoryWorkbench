# SPDX-License-Identifier: LGPL-3.0-or-later
# File responsibility: Presents git repository information and manages commit loading in the UI.
"""Git repository presenter for UI layer."""

from collections.abc import Callable
from time import monotonic

from freecad.history_wb.application.actions.find_active_git_repository import (
    FindActiveGitRepositoryAction,
)
from freecad.history_wb.application.actions.get_commits import GetCommitsAction
from freecad.history_wb.domain.git.models import GitRepository
from freecad.history_wb.ui.state import ApplicationState
from freecad.history_wb.ui.views.diff_panel.dialog_view import DialogView
from freecad.history_wb.ui.views.history.panel import HistoryPanelWidget
from freecad.history_wb.utils import Log

from .workbench_command_presenter import WorkbenchCommandPresenter


class GitRepositoryPresenter:
    """Handles git repository detection and UI display.

    This presenter is responsible for:
    1. Detecting the active git repository when the workbench is activated
    2. Updating the UI state with the detected repository
    3. Displaying the repository information in the view
    4. Loading and displaying commits for the repository

    Shared command flows (save iteration, configure author, initialize repo,
    update gitignore) are delegated to WorkbenchCommandPresenter to avoid
    duplicating handler construction and dialog lifecycle management.

    Attributes:
        _view: The HistoryPanelView instance for displaying repository info.
        _find_git_repo_action: The action for finding the active git repository.
        _application_state: The application-scoped state holder for storing repository.
    """

    def __init__(
        self,
        history_view: HistoryPanelWidget,
        dialog_view: DialogView,
        find_git_repo_action: FindActiveGitRepositoryAction,
        get_commits_action: GetCommitsAction,
        application_state: ApplicationState,
        clear_doc_diffs: Callable[[], None],
        workbench_command_presenter: WorkbenchCommandPresenter,
    ) -> None:
        """Initialize the presenter with required dependencies.

        Args:
            history_view: History-column view implementation.
            dialog_view: Dialog and message view implementation.
            find_git_repo_action: The action for finding the active git repository.
            get_commits_action: The action for getting git commits.
            application_state: Application-scoped state holder for storing repository.
            clear_doc_diffs: Callback to clear document diffs.
            workbench_command_presenter: App-scoped presenter for shared command flows.
        """
        self._history_view = history_view
        self._dialog_view = dialog_view
        self._find_git_repo_action = find_git_repo_action
        self._get_commits_action = get_commits_action
        self._application_state = application_state
        self._clear_doc_diffs = clear_doc_diffs
        self._command_presenter = workbench_command_presenter
        self._page_size = 20
        self._loaded_commit_count = 0
        self._has_more_commits = False
        self._is_loading_commits = False
        self._active_repo_path: str | None = None
        self._last_scroll_load_ts = 0.0
        self._scroll_load_interval_seconds = 0.2

    def on_workbench_activated(self) -> None:
        """Detect and display git repository when workbench activates.

        This method is called when the workbench is activated to detect
        the current git repository and display it in the UI.
        """
        self.refresh_repository_and_commits()

    def refresh_repository_and_commits(self) -> None:
        """Refresh repository detection and reload commit list.

        This method provides a UI-agnostic entry point for any caller
        that needs to re-detect the current repository, update UI state,
        and repopulate commits in the view.
        """
        self._detect_git_repository()

    def save_iteration(self) -> None:
        """Execute save-iteration flow from toolbar or panel button."""
        success = self._command_presenter.save_iteration()
        if success:
            Log.info("Commit successful")
            self.refresh_repository_and_commits()

    def initialize_repository(self) -> None:
        """Execute repository initialization flow from toolbar command."""
        initialized = self._command_presenter.initialize_repository()
        if initialized:
            self.refresh_repository_and_commits()

    def update_gitignore(self) -> None:
        """Execute gitignore editor flow from toolbar command."""
        self._command_presenter.update_gitignore()

    def _detect_git_repository(self) -> None:
        """Detect git repository and update UI and application state.

        This protected method encapsulates the common logic for git repository
        detection used by both workbench activation and refresh button clicks.
        """
        result = self._find_git_repo_action.execute()

        if result.is_success:
            repo = result.data
            self._application_state.git_repository = repo
            self._history_view.show_repository(repo)
            self._reset_commit_pagination(repo)

            # After detecting repository, load commits
            if repo is not None:
                self._load_initial_commits(repo)
        else:
            self._application_state.git_repository = None
            self._reset_commit_pagination(None)
            self._history_view.show_repository(None)
            self._history_view.show_commits([], show_special_items=False)
            self._clear_doc_diffs()
            Log.info(f"Git detection failed: {result.message}")

    def _load_initial_commits(self, repo: GitRepository) -> None:
        """Load first commit page and replace list content.

        Args:
            repo: The GitRepository to load commits from.
        """
        if self._is_loading_commits:
            return
        self._is_loading_commits = True
        result = self._get_commits_action.execute(repo)
        self._is_loading_commits = False

        if result.is_success:
            commits = result.data
            self._loaded_commit_count = len(commits)
            self._has_more_commits = len(commits) == self._page_size
            self._clear_doc_diffs()
            self._history_view.show_commits(commits)
        else:
            self._loaded_commit_count = 0
            self._has_more_commits = False
            self._clear_doc_diffs()
            # Show empty list on failure
            self._history_view.show_commits([])
            Log.warning(f"Failed to load commits: {result.message}")

    def load_more_commits(self) -> None:
        """Load next commit page when history scroll reaches bottom area."""
        now = monotonic()
        if now - self._last_scroll_load_ts < self._scroll_load_interval_seconds:
            return

        repo = self._application_state.git_repository
        if repo is None:
            return
        if self._active_repo_path != repo.absolute_path:
            return
        if self._is_loading_commits or not self._has_more_commits:
            return

        self._last_scroll_load_ts = now
        self._is_loading_commits = True
        result = self._get_commits_action.execute(
            repo,
            limit=self._page_size,
            skip=self._loaded_commit_count,
        )
        self._is_loading_commits = False

        if not result.is_success:
            self._has_more_commits = False
            Log.warning(f"Failed to load more commits: {result.message}")
            return

        commits = result.data
        if not commits:
            self._has_more_commits = False
            return

        self._history_view.append_commits(commits)
        self._loaded_commit_count += len(commits)
        self._has_more_commits = len(commits) == self._page_size

    def _reset_commit_pagination(self, repo: GitRepository | None) -> None:
        """Reset pagination state for current repository."""
        self._loaded_commit_count = 0
        self._has_more_commits = repo is not None
        self._is_loading_commits = False
        self._active_repo_path = repo.absolute_path if repo is not None else None
        self._last_scroll_load_ts = 0.0
