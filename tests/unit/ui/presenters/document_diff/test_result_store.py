# SPDX-License-Identifier: LGPL-3.0-or-later
# File responsibility: Unit tests for document-diff presenter result cache store.

from __future__ import annotations

from datetime import datetime

import pytest

from freecad.history_wb.application.actions.result_models import DiffIssues, DocumentDiffResult
from freecad.history_wb.domain.diff.models import DiffResult, DiffState
from freecad.history_wb.domain.snapshots.models import Snapshot
from freecad.history_wb.ui.presenters.document_diff.result_store import DocumentDiffResultStore


def _make_snapshot(git_path: str) -> Snapshot:
    return Snapshot(
        snapshot_id=git_path,
        document_name=git_path,
        timestamp=datetime.now(),
        git_path=git_path,
    )


def _make_result(git_path: str, *, with_diff: bool = True) -> DocumentDiffResult:
    snapshot = _make_snapshot(git_path)
    snapshot_diff = DiffResult(old_snapshot=snapshot, new_snapshot=snapshot) if with_diff else None
    return DocumentDiffResult(
        git_path=git_path,
        document_state=DiffState.MODIFIED,
        issues=DiffIssues(),
        snapshot_diff=snapshot_diff,
    )


def test_require_accessors_raise_for_impossible_missing_cache_state() -> None:
    """Strict accessors fail fast when presenter cache invariant is broken."""
    store = DocumentDiffResultStore()

    with pytest.raises(RuntimeError, match="missing.FCStd"):
        store.require_document_result("missing.FCStd")

    with pytest.raises(RuntimeError, match="missing.FCStd"):
        store.require_diff_result("missing.FCStd")


def test_require_diff_result_raises_when_cached_row_has_no_snapshot_diff() -> None:
    """Strict diff accessor fails when cached row lacks diff payload."""
    store = DocumentDiffResultStore()
    store.store_results([_make_result("closed.FCStd", with_diff=False)])

    with pytest.raises(RuntimeError, match="closed.FCStd"):
        store.require_diff_result("closed.FCStd")


def test_optional_accessors_preserve_stale_row_lookup_behavior() -> None:
    """Optional accessors return None for legitimate stale-row lookups."""
    store = DocumentDiffResultStore()

    assert store.get_document_result("missing.FCStd") is None
    assert store.get_diff_result("missing.FCStd") is None


def test_has_diff_results_only_counts_rows_with_snapshot_diffs() -> None:
    """Diff-result presence depends on cached snapshot diff payloads."""
    store = DocumentDiffResultStore()
    store.store_results([_make_result("closed.FCStd", with_diff=False)])

    assert store.has_diff_results() is False

    store.store_results([_make_result("open.FCStd")])

    assert store.has_diff_results() is True


def test_store_results_and_remove_path_keep_remaining_results_sorted() -> None:
    """Store returns sorted remainder after path removal."""
    store = DocumentDiffResultStore()
    result_a = _make_result("b.FCStd")
    result_b = _make_result("a.FCStd")
    result_c = _make_result("closed.FCStd", with_diff=False)
    store.store_results([result_a, result_b, result_c])

    remaining = store.remove_path("b.FCStd")

    assert store.require_document_result("a.FCStd") == result_b
    assert store.require_diff_result("a.FCStd") == result_b.snapshot_diff
    assert store.get_diff_result("closed.FCStd") is None
    assert [result.git_path for result in remaining] == ["a.FCStd", "closed.FCStd"]
