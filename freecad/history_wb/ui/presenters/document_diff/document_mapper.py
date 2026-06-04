# File responsibility: Pure document-diff to diff-tree presentation mapping.
"""Pure document-diff to diff-tree presentation mapping helpers."""

from ....application.actions.result_models import DocumentDiffResult, SnapshotIssue
from ....domain.diff.models import DiffState
from ..presentation_models import DiffTreePresentation
from .indicator_mapper import get_document_indicators
from .node_mapper import format_node


def build_document_presentations(
    document_results: list[DocumentDiffResult],
    is_working_tree: bool,
) -> list[DiffTreePresentation]:
    """Build document presentations from action-level document results."""
    presentations: list[DiffTreePresentation] = []
    for document_result in document_results:
        if not _should_display_document_result(document_result):
            continue

        nodes = []
        if document_result.snapshot_diff is not None:
            nodes = [format_node(node) for node in document_result.snapshot_diff.hierarchy.roots]

        presentations.append(
            DiffTreePresentation(
                nodes=nodes,
                git_path=document_result.git_path,
                indicators=get_document_indicators(document_result.issues, is_working_tree),
                document_state=document_result.document_state,
                stage_button_enabled=compute_stage_button_state(document_result, is_working_tree),
            )
        )
    return presentations


def compute_stage_button_state(document_result: DocumentDiffResult, is_working_tree: bool) -> bool:
    """Compute whether stage action is enabled for one document row."""
    if not is_working_tree:
        return False

    # Deleted documents stage by path and never require a new-side snapshot payload.
    if document_result.document_state == DiffState.DELETED:
        return True

    has_changes = document_result.document_state != DiffState.UNCHANGED
    needs_snapshot = document_result.issues.old_snapshot is not None

    # Missing new snapshot means closed dirty document. Block stage until reopened.
    is_closed_dirty_document = (
        has_changes or needs_snapshot
    ) and document_result.issues.new_snapshot == SnapshotIssue.MISSING

    return not is_closed_dirty_document


def _should_display_document_result(document_result: DocumentDiffResult) -> bool:
    """Return whether one document result belongs in document tree output."""
    if document_result.document_state != DiffState.UNCHANGED:
        return True
    if document_result.snapshot_diff is not None and document_result.snapshot_diff.has_changes:
        return True
    return document_result.issues.has_any()
