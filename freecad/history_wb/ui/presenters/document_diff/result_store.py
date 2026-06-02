# File responsibility: Cache document-diff action results for presenter flows.
"""Cache document-diff action results for presenter flows."""

from ....application.actions.result_models import DocumentDiffResult
from ....domain.diff.engine import DiffResult


class DocumentDiffResultStore:
    """Own cached document results keyed by git path."""

    def __init__(self) -> None:
        """Initialize empty cache."""
        self.clear()

    def clear(self) -> None:
        """Clear cached document results."""
        self._document_results_by_path: dict[str, DocumentDiffResult] = {}

    def store_results(self, document_results: list[DocumentDiffResult]) -> None:
        """Replace cache contents with fresh action results."""
        self.clear()
        self._document_results_by_path = {result.git_path: result for result in document_results}

    def has_diff_results(self) -> bool:
        """Return whether any cached document result still carries a snapshot diff."""
        return any(result.snapshot_diff is not None for result in self._document_results_by_path.values())

    def get_document_result(self, git_path: str) -> DocumentDiffResult | None:
        """Return cached document result or None for stale/missing rows."""
        return self._document_results_by_path.get(git_path)

    def require_document_result(self, git_path: str) -> DocumentDiffResult:
        """Return cached document result or raise for impossible missing state."""
        document_result = self.get_document_result(git_path)
        if document_result is None:
            raise RuntimeError(f"Document result missing from cache for {git_path}")
        return document_result

    def get_diff_result(self, git_path: str) -> DiffResult | None:
        """Return cached diff result or None for stale/missing rows."""
        document_result = self.get_document_result(git_path)

        if document_result is None:
            return None

        return document_result.snapshot_diff

    def require_diff_result(self, git_path: str) -> DiffResult:
        """Return cached diff result or raise for impossible missing state."""
        diff_result = self.require_document_result(git_path).snapshot_diff
        if diff_result is None:
            raise RuntimeError(f"Diff result missing from cache for {git_path}")
        return diff_result

    def get_document_results(self) -> list[DocumentDiffResult]:
        """Return cached document results in insertion order."""
        return list(self._document_results_by_path.values())

    def remove_path(self, git_path: str) -> list[DocumentDiffResult]:
        """Remove one cached path and return remaining results sorted by path."""
        self._document_results_by_path.pop(git_path, None)
        return sorted(self._document_results_by_path.values(), key=lambda result: result.git_path)
