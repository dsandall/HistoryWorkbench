# File responsibility: Build and execute visual diff requests for history selections.
"""Build and execute visual diff requests for history selections."""

from ....application.actions.open_visual_diff import (
    OpenVisualDiffAction,
    OpenVisualDiffRequest,
    VisualDiffRequestType,
)
from ....domain.git.models import GitRepository
from ....utils import Log
from ...views.history.models import HistorySelection


class DocumentVisualDiffHandler:
    """Own visual-diff request mapping and action execution."""

    def __init__(self, open_visual_feature_diff_action: OpenVisualDiffAction) -> None:
        """Store visual-diff action dependency."""
        self._open_visual_feature_diff = open_visual_feature_diff_action

    def open_visual_diff(
        self,
        selection: HistorySelection,
        repo: GitRepository,
        git_path: str,
        node_path: str,
    ) -> None:
        """Build request for selection and invoke visual-diff action."""
        request = self._build_visual_diff_request(selection, repo, git_path, node_path)
        if request is None:
            return

        result = self._open_visual_feature_diff.execute(request)
        if not result.is_success and result.message:
            Log.warning(result.message)

    def _build_visual_diff_request(
        self,
        selection: HistorySelection,
        repo: GitRepository,
        git_path: str,
        node_path: str,
    ) -> OpenVisualDiffRequest | None:
        """Map history selection to visual-diff request payload."""
        if selection.item_kind == "WORKING_TREE":
            return OpenVisualDiffRequest(
                repo=repo,
                git_path=git_path,
                node_path=node_path,
                type=VisualDiffRequestType.WORKING,
            )

        if selection.item_kind == "STAGING":
            return OpenVisualDiffRequest(
                repo=repo,
                git_path=git_path,
                node_path=node_path,
                type=VisualDiffRequestType.STAGING,
            )

        if selection.item_kind == "COMMIT" and selection.commit_hash:
            return OpenVisualDiffRequest(
                repo=repo,
                git_path=git_path,
                node_path=node_path,
                type=VisualDiffRequestType.COMMIT,
                old_commit=f"{selection.commit_hash}~1",
                new_commit=selection.commit_hash,
            )

        Log.warning("Commit selection missing commit hash for visual diff")
        return None
