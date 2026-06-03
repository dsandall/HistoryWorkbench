# File responsibility: Load document diff results for working-tree, staging, and commit selections.
"""Load document diff results for presenter selection flows."""

from ....application.actions.diffs.create_document_diffs import CreateDocumentDiffsAction
from ....application.actions.documents.get_open_eligible_documents import GetOpenEligibleDocumentsAction
from ....application.actions.result_models import (
    CreateDocumentDiffsRequest,
    DocumentDiffMode,
    DocumentDiffResult,
)
from ....domain.freecad_ports import DocumentLike
from ....domain.git.models import GitRepository
from ....utils import Log


class DocumentDiffLoader:
    """Own document-diff loading flows for history selections."""

    def __init__(
        self,
        get_eligible_docs_action: GetOpenEligibleDocumentsAction,
        create_document_diffs_action: CreateDocumentDiffsAction,
    ) -> None:
        """Store action dependencies used by selection flows."""
        self._get_eligible_docs = get_eligible_docs_action
        self._create_document_diffs = create_document_diffs_action

    def load_working_tree(self, repo: GitRepository) -> list[DocumentDiffResult]:
        """Load working-tree document diffs for repository."""
        eligible_docs = self._get_eligible_documents(repo)
        if eligible_docs is None:
            return []

        return self._load_diffs(
            CreateDocumentDiffsRequest(
                mode=DocumentDiffMode.WORKING_TREE,
                repo=repo,
                eligible_docs=eligible_docs,
            )
        )

    def load_staging(self, repo: GitRepository) -> list[DocumentDiffResult]:
        """Load staging document diffs for repository."""
        return self._load_diffs(CreateDocumentDiffsRequest(mode=DocumentDiffMode.STAGING, repo=repo))

    def load_commit(self, repo: GitRepository, commit_hash: str) -> list[DocumentDiffResult]:
        """Load commit document diffs for repository and commit."""
        return self._load_diffs(
            CreateDocumentDiffsRequest(mode=DocumentDiffMode.COMMIT, repo=repo, commit_hash=commit_hash)
        )

    def _get_eligible_documents(self, repo: GitRepository) -> list[DocumentLike] | None:
        """Load eligible open documents for working-tree diffing."""
        docs_result = self._get_eligible_docs.execute(repo)
        if not docs_result.is_success:
            Log.warning(f"Failed to get eligible documents: {docs_result.message}")
            return None

        return docs_result.data

    def _load_diffs(self, request: CreateDocumentDiffsRequest) -> list[DocumentDiffResult]:
        """Execute diff action request and log failures."""
        result = self._create_document_diffs.execute(request)
        if not result.is_success:
            Log.warning(f"Failed to create document diffs: {result.message}")
            return []

        return result.data
