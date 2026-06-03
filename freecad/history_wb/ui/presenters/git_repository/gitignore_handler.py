# File responsibility: Handle gitignore editor dialog flow and action orchestration.
"""Handle gitignore editor dialog flow and action orchestration."""

from collections.abc import Callable

from ....application.actions.git_config.get_gitignore_content import GetGitIgnoreContentAction
from ....application.actions.git_config.update_gitignore import UpdateGitIgnoreAction
from ....domain.git.models import GitRepository
from ....utils import translate


class GitIgnoreHandler:
    """Own gitignore edit flow for presenter and commands."""

    def __init__(
        self,
        get_content_action: GetGitIgnoreContentAction,
        update_action: UpdateGitIgnoreAction,
        show_editor_dialog: Callable[[str], str | None],
        show_info_message: Callable[[str, str], None],
        show_error_message: Callable[[str, str], None],
    ) -> None:
        """Store action and dialog dependencies."""
        self._get_content_action = get_content_action
        self._update_action = update_action
        self._show_editor_dialog = show_editor_dialog
        self._show_info_message = show_info_message
        self._show_error_message = show_error_message

    def execute(self, repo: GitRepository) -> None:
        """Run full gitignore edit flow."""
        content_result = self._get_content_action.execute(repo)
        if not content_result.is_success:
            self._show_error_message(
                translate("History", "Failed to Read Ignored Files"),
                content_result.message or translate("History", "Unknown error occurred"),
            )
            return

        edited_content = self._show_editor_dialog(str(content_result.data))
        if edited_content is None:
            return

        save_result = self._update_action.execute(repo, edited_content)
        if not save_result.is_success:
            self._show_error_message(
                translate("History", "Failed to Save Ignored Files"),
                save_result.message or translate("History", "Unknown error occurred"),
            )
            return

        self._show_info_message(
            translate("History", "Ignored Files Updated"),
            translate("History", "Updated ignored files list."),
        )
