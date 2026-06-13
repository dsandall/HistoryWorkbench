# File responsibility: Unit tests for OpenVisualDiffAction orchestration and failure handling.
"""Unit tests for OpenVisualDiffAction orchestration and failure handling."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from freecad.history_wb.application.actions.diffs.open_visual_diff import (
    OpenVisualDiffAction,
    OpenVisualDiffRequest,
    VisualDiffFailureReason,
    VisualDiffRequestType,
)
from freecad.history_wb.domain.freecad_ports import BrepLookupResult, FreeCadFileManagerPort
from freecad.history_wb.domain.git.git_service import GitService
from freecad.history_wb.domain.git.models import GitRepository
from tests.fakes import FakeFreeCadPort, FakeGitPort, MockDocument


@dataclass
class FakeVisualDiff:
    old_brep: bytes | None = None
    new_brep: bytes | None = None
    document_name: str | None = None

    def open_brep_visual_diff(
        self,
        old_brep: bytes | None,
        new_brep: bytes | None,
        document_name: str,
    ) -> object:
        self.old_brep = old_brep
        self.new_brep = new_brep
        self.document_name = document_name
        return object()


class FakeFileManager(FreeCadFileManagerPort):
    """Fake implementation of FreeCadFileManagerPort for testing."""

    def __init__(self) -> None:
        self._results: dict[tuple[str, str], BrepLookupResult] = {}
        self.requested_breps: list[tuple[str, str]] = []

    def get_brep(self, repo: GitRepository, git_path: str, revision: str, brep_name: str) -> BrepLookupResult:
        self.requested_breps.append((revision, brep_name))
        return self._results.get((revision, brep_name), BrepLookupResult(document_exists=False, brep=None))

    def set_brep(self, revision: str, brep_name: str, document_exists: bool, brep: bytes | None) -> None:
        self._results[(revision, brep_name)] = BrepLookupResult(document_exists=document_exists, brep=brep)


def _action(
    fake_port: FakeGitPort,
    visual_diff: FakeVisualDiff,
    file_manager: FakeFileManager,
    freecad_port: FakeFreeCadPort | None = None,
) -> OpenVisualDiffAction:
    return OpenVisualDiffAction(
        git_service=GitService(git_port=fake_port),
        visual_diff=visual_diff,
        file_manager=file_manager,
        freecad_port=freecad_port or FakeFreeCadPort(),
    )


def _add_brep(file_manager: FakeFileManager, revision: str, content: bytes, object_name: str = "Pad") -> None:
    file_manager.set_brep(revision, f"{object_name}.Shape.brp", True, content)


def test_document_name_construction() -> None:
    repo = GitRepository(name="repo", absolute_path="/repo")
    fake_port = FakeGitPort()
    visual_diff = FakeVisualDiff()
    file_manager = FakeFileManager()
    _add_brep(file_manager, "staging", b"old")
    _add_brep(file_manager, "working", b"new")

    action = _action(fake_port, visual_diff, file_manager)
    result = action.execute(OpenVisualDiffRequest(repo, "BasicFile.FCStd", "Body/Pad", VisualDiffRequestType.WORKING))

    assert result.is_success is True
    assert visual_diff.document_name == "Diff_BasicFile_Pad"


def test_execute_opens_visual_diff_when_shape_present() -> None:
    repo = GitRepository(name="repo", absolute_path="/repo")
    fake_port = FakeGitPort()
    visual_diff = FakeVisualDiff()
    file_manager = FakeFileManager()
    _add_brep(file_manager, "staging", b"old")
    _add_brep(file_manager, "working", b"new")

    action = _action(fake_port, visual_diff, file_manager)
    result = action.execute(OpenVisualDiffRequest(repo, "doc.FCStd", "Body/Pad", VisualDiffRequestType.WORKING))

    assert result.is_success is True
    assert file_manager.requested_breps == [("staging", "Pad.Shape.brp"), ("working", "Pad.Shape.brp")]
    assert visual_diff.old_brep == b"old"
    assert visual_diff.new_brep == b"new"


def test_execute_opens_visual_diff_when_new_brep_missing() -> None:
    repo = GitRepository(name="repo", absolute_path="/repo")
    fake_port = FakeGitPort()
    visual_diff = FakeVisualDiff()
    file_manager = FakeFileManager()
    _add_brep(file_manager, "staging", b"old")
    file_manager.set_brep("working", "Pad.Shape.brp", True, None)

    action = _action(fake_port, visual_diff, file_manager)
    result = action.execute(OpenVisualDiffRequest(repo, "doc.FCStd", "Body/Pad", VisualDiffRequestType.WORKING))

    assert result.is_success is True
    assert visual_diff.old_brep == b"old"
    assert visual_diff.new_brep is None


def test_execute_opens_visual_diff_when_old_brep_missing() -> None:
    repo = GitRepository(name="repo", absolute_path="/repo")
    fake_port = FakeGitPort()
    visual_diff = FakeVisualDiff()
    file_manager = FakeFileManager()
    file_manager.set_brep("staging", "Pad.Shape.brp", True, None)
    _add_brep(file_manager, "working", b"new")

    action = _action(fake_port, visual_diff, file_manager)
    result = action.execute(OpenVisualDiffRequest(repo, "doc.FCStd", "Body/Pad", VisualDiffRequestType.WORKING))

    assert result.is_success is True
    assert visual_diff.old_brep is None
    assert visual_diff.new_brep == b"new"


def test_execute_fails_when_brep_missing_from_both_sides() -> None:
    repo = GitRepository(name="repo", absolute_path="/repo")
    fake_port = FakeGitPort()
    visual_diff = FakeVisualDiff()
    file_manager = FakeFileManager()
    file_manager.set_brep("staging", "Pad.Shape.brp", True, None)
    file_manager.set_brep("working", "Pad.Shape.brp", True, None)

    action = _action(fake_port, visual_diff, file_manager)
    result = action.execute(OpenVisualDiffRequest(repo, "doc.FCStd", "Body/Pad", VisualDiffRequestType.WORKING))

    assert result.is_success is False
    assert result.message == VisualDiffFailureReason.MISSING_BREP.value


def test_execute_fails_when_fcstd_missing_on_both_sides() -> None:
    repo = GitRepository(name="repo", absolute_path="/repo")
    fake_port = FakeGitPort()
    visual_diff = FakeVisualDiff()
    file_manager = FakeFileManager()

    action = _action(fake_port, visual_diff, file_manager)
    result = action.execute(OpenVisualDiffRequest(repo, "doc.FCStd", "Body/Pad", VisualDiffRequestType.WORKING))

    assert result.is_success is False
    assert result.message == VisualDiffFailureReason.MISSING_FCSTD.value


def test_execute_uses_head_and_staging_for_staging_request() -> None:
    repo = GitRepository(name="repo", absolute_path="/repo")
    fake_port = FakeGitPort()
    visual_diff = FakeVisualDiff()
    file_manager = FakeFileManager()
    _add_brep(file_manager, "HEAD", b"old")
    _add_brep(file_manager, "staging", b"new")

    action = _action(fake_port, visual_diff, file_manager)
    result = action.execute(OpenVisualDiffRequest(repo, "doc.FCStd", "Body/Pad", VisualDiffRequestType.STAGING))

    assert result.is_success is True
    assert file_manager.requested_breps == [("HEAD", "Pad.Shape.brp"), ("staging", "Pad.Shape.brp")]


def test_execute_uses_commit_revisions_for_commit_request() -> None:
    repo = GitRepository(name="repo", absolute_path="/repo")
    fake_port = FakeGitPort()
    visual_diff = FakeVisualDiff()
    file_manager = FakeFileManager()
    _add_brep(file_manager, "abc~1", b"old")
    _add_brep(file_manager, "abc", b"new")

    action = _action(fake_port, visual_diff, file_manager)
    result = action.execute(
        OpenVisualDiffRequest(repo, "doc.FCStd", "Body/Pad", VisualDiffRequestType.COMMIT, "abc~1", "abc")
    )

    assert result.is_success is True
    assert file_manager.requested_breps == [("abc~1", "Pad.Shape.brp"), ("abc", "Pad.Shape.brp")]


def test_execute_fails_when_commit_request_missing_commits() -> None:
    repo = GitRepository(name="repo", absolute_path="/repo")
    fake_port = FakeGitPort()
    visual_diff = FakeVisualDiff()
    file_manager = FakeFileManager()

    action = _action(fake_port, visual_diff, file_manager)
    result = action.execute(OpenVisualDiffRequest(repo, "doc.FCStd", "Body/Pad", VisualDiffRequestType.COMMIT))

    assert result.is_success is False
    assert result.message == VisualDiffFailureReason.INVALID_REQUEST.value
    assert file_manager.requested_breps == []


def test_working_request_saves_modified_document_before_diff(tmp_path: Path) -> None:
    doc = MockDocument(str(tmp_path / "doc.FCStd"))
    freecad_port = FakeFreeCadPort(open_documents=[doc])
    freecad_port._modified_doc_names = {doc.Name}
    repo = GitRepository(name="repo", absolute_path=str(tmp_path))
    fake_port = FakeGitPort()
    visual_diff = FakeVisualDiff()
    file_manager = FakeFileManager()
    _add_brep(file_manager, "staging", b"old")
    _add_brep(file_manager, "working", b"new")

    action = _action(fake_port, visual_diff, file_manager, freecad_port)
    action.execute(OpenVisualDiffRequest(repo, "doc.FCStd", "Body/Pad", VisualDiffRequestType.WORKING))

    assert doc.saved is True


def test_staging_request_does_not_save_working_document(tmp_path: Path) -> None:
    doc = MockDocument(str(tmp_path / "doc.FCStd"))
    freecad_port = FakeFreeCadPort(open_documents=[doc])
    repo = GitRepository(name="repo", absolute_path=str(tmp_path))
    fake_port = FakeGitPort()
    visual_diff = FakeVisualDiff()
    file_manager = FakeFileManager()
    _add_brep(file_manager, "HEAD", b"old")
    _add_brep(file_manager, "staging", b"new")

    action = _action(fake_port, visual_diff, file_manager, freecad_port)
    action.execute(OpenVisualDiffRequest(repo, "doc.FCStd", "Body/Pad", VisualDiffRequestType.STAGING))

    assert doc.saved is False
