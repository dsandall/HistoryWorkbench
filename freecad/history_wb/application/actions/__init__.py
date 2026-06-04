"""Module responsibility: Action use cases."""

from .diffs.create_diff import CreateDiffAction
from .diffs.create_document_diffs import CreateDocumentDiffsAction
from .diffs.open_visual_diff import OpenVisualDiffAction
from .documents.get_open_eligible_documents import GetOpenEligibleDocumentsAction
from .documents.open_all_documents_in_repository import OpenAllDocumentsInRepositoryAction
from .documents.open_document import OpenDocumentAction
from .documents.recompute_all_open_documents import RecomputeAllOpenDocumentsAction
from .git_config.can_write_global_git_identity import CanWriteGlobalGitIdentityAction
from .git_config.get_git_identity import GetGitIdentityAction
from .git_config.get_gitignore_content import GetGitIgnoreContentAction
from .git_config.save_git_identity import SaveGitIdentityAction
from .git_config.update_gitignore import UpdateGitIgnoreAction
from .git_history.get_commits import GetCommitsAction
from .git_history.get_committed_file_paths import GetCommittedFilePathsAction
from .git_history.get_staged_file_paths import GetStagedFilePathsAction
from .git_repo.find_active_git_repository import FindActiveGitRepositoryAction
from .git_repo.get_git_repository_init_candidates import GetGitRepositoryInitCandidatesAction
from .git_repo.initialize_git_repository import InitializeGitRepositoryAction
from .git_workflow.commit_staging import CommitStagingAction
from .git_workflow.restore_documents import RestoreDocumentsAction
from .git_workflow.stage_documents import StageDocumentsAction
from .git_workflow.unstage_documents import UnstageDocumentsAction
from .result_models import (
    CompareResult,
    CreateDocumentDiffsRequest,
    DiffIssues,
    DocumentDiffMode,
    DocumentDiffResult,
    GeneralDiffIssue,
    Result,
    SnapshotIssue,
    SnapshotResult,
    SnapshotSummary,
)
from .settings.get_diff_settings import GetDiffSettingsAction
from .settings.save_diff_settings import SaveDiffSettingsAction
from .snapshots.create_document_snapshot_commit import CreateDocumentSnapshotForCommitAction
from .snapshots.create_document_snapshot_working import CreateDocumentSnapshotForWorkingTreeAction


__all__ = [
    # Commands
    "CommitStagingAction",
    "CanWriteGlobalGitIdentityAction",
    # Actions
    "FindActiveGitRepositoryAction",
    "GetCommitsAction",
    "GetCommittedFilePathsAction",
    "GetDiffSettingsAction",
    "GetGitIdentityAction",
    "GetGitIgnoreContentAction",
    "GetOpenEligibleDocumentsAction",
    "GetGitRepositoryInitCandidatesAction",
    "GetStagedFilePathsAction",
    "InitializeGitRepositoryAction",
    "OpenAllDocumentsInRepositoryAction",
    "OpenDocumentAction",
    "OpenVisualDiffAction",
    "RecomputeAllOpenDocumentsAction",
    "RestoreDocumentsAction",
    "SaveDiffSettingsAction",
    "SaveGitIdentityAction",
    "StageDocumentsAction",
    "CreateDocumentSnapshotForWorkingTreeAction",
    "CreateDocumentSnapshotForCommitAction",
    "CreateDiffAction",
    "CreateDocumentDiffsAction",
    "UnstageDocumentsAction",
    "UpdateGitIgnoreAction",
    # Result models
    "Result",
    "SnapshotResult",
    "CompareResult",
    "SnapshotSummary",
    "CreateDocumentDiffsRequest",
    "DocumentDiffMode",
    "SnapshotIssue",
    "GeneralDiffIssue",
    "DiffIssues",
    "DocumentDiffResult",
]
