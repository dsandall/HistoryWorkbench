"""File responsibility: Unit tests for OpenVisualFeatureDiffAction orchestration and failure handling."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from freecad.history_wb.application.actions.diffs.open_visual_diff import (
    OpenVisualDiffAction,
    OpenVisualDiffRequest,
    VisualDiffFailureReason,
    VisualDiffRequestType,
)
from freecad.history_wb.domain.freecad_ports import FreeCadFileManagerPort
from freecad.history_wb.domain.git.git_service import GitService
from freecad.history_wb.domain.git.models import GitRepository
from tests.fakes import FakeFreeCadPort, FakeGitPort, MockDocument


@dataclass
class FakeVisualDiff:
    old_path: str | None = None
    new_path: str | None = None
    document_name: str | None = None

    def open_brep_visual_diff(
        self,
        old_brep_path: str | None,
        new_brep_path: str | None,
        document_name: str,
    ) -> object:
        self.old_path = old_brep_path
        self.new_path = new_brep_path
        self.document_name = document_name
        return object()


class FakePreparedRevision:
    """Fake context manager that yields a configured path."""

    def __init__(self, path: Path | None) -> None:
        self._path = path

    def __enter__(self) -> Path | None:
        return self._path

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        pass


class FakeFileManager(FreeCadFileManagerPort):
    """Fake implementation of FreeCadFileManagerPort for testing."""

    def __init__(self) -> None:
        self._prepared_roots: dict[str, Path | None] = {}
        self._breps_found: dict[tuple[str, str], Path | None] = {}
        self.prepared_revisions: list[str] = []

    def prepare_document_at_revision(self, repo: GitRepository, git_path: str, revision: str) -> FakePreparedRevision:
        self.prepared_revisions.append(revision)
        return FakePreparedRevision(self._prepared_roots.get(revision))

    def find_extracted_file(self, extract_root: Path, file_name: str) -> Path | None:
        return self._breps_found.get((str(extract_root), file_name))

    def set_prepared_root(self, revision: str, root: Path | None) -> None:
        self._prepared_roots[revision] = root

    def set_brep_found(self, extract_root: Path, brep_name: str, path: Path | None) -> None:
        self._breps_found[(str(extract_root), brep_name)] = path


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


def _brep(root: Path, object_name: str = "Pad") -> Path:
    brep = root / "PartData" / f"{object_name}.Shape.brp"
    brep.parent.mkdir(parents=True, exist_ok=True)
    brep.write_text("BREP", encoding="utf-8")
    return brep


def test_document_name_construction(tmp_path: Path) -> None:
    repo = GitRepository(name="repo", absolute_path="/repo")
    fake_port = FakeGitPort()
    visual_diff = FakeVisualDiff()
    file_manager = FakeFileManager()
    old_extract = tmp_path / "old_extract"
    new_extract = tmp_path / "new_extract"
    old_brep = _brep(old_extract)
    new_brep = _brep(new_extract)
    file_manager.set_prepared_root("staging", old_extract)
    file_manager.set_prepared_root("working", new_extract)
    file_manager.set_brep_found(old_extract, "Pad.Shape.brp", old_brep)
    file_manager.set_brep_found(new_extract, "Pad.Shape.brp", new_brep)

    action = _action(fake_port, visual_diff, file_manager)
    result = action.execute(OpenVisualDiffRequest(repo, "BasicFile.FCStd", "Body/Pad", VisualDiffRequestType.WORKING))

    assert result.is_success is True
    assert visual_diff.document_name == "Diff_BasicFile_Pad"


def test_execute_opens_visual_diff_when_shape_present(tmp_path: Path) -> None:
    repo = GitRepository(name="repo", absolute_path="/repo")
    fake_port = FakeGitPort()
    visual_diff = FakeVisualDiff()
    file_manager = FakeFileManager()
    old_extract = tmp_path / "old_extract"
    new_extract = tmp_path / "new_extract"
    old_brep = _brep(old_extract)
    new_brep = _brep(new_extract)
    file_manager.set_prepared_root("staging", old_extract)
    file_manager.set_prepared_root("working", new_extract)
    file_manager.set_brep_found(old_extract, "Pad.Shape.brp", old_brep)
    file_manager.set_brep_found(new_extract, "Pad.Shape.brp", new_brep)

    action = _action(fake_port, visual_diff, file_manager)
    result = action.execute(OpenVisualDiffRequest(repo, "doc.FCStd", "Body/Pad", VisualDiffRequestType.WORKING))

    assert result.is_success is True
    assert file_manager.prepared_revisions == ["staging", "working"]
    assert visual_diff.old_path is not None and visual_diff.old_path.endswith("Pad.Shape.brp")
    assert visual_diff.new_path is not None and visual_diff.new_path.endswith("Pad.Shape.brp")


def test_execute_opens_visual_diff_when_new_brep_missing(tmp_path: Path) -> None:
    repo = GitRepository(name="repo", absolute_path="/repo")
    fake_port = FakeGitPort()
    visual_diff = FakeVisualDiff()
    file_manager = FakeFileManager()
    old_extract = tmp_path / "old_extract"
    new_extract = tmp_path / "new_extract"
    old_brep = _brep(old_extract)
    file_manager.set_prepared_root("staging", old_extract)
    file_manager.set_prepared_root("working", new_extract)
    file_manager.set_brep_found(old_extract, "Pad.Shape.brp", old_brep)
    file_manager.set_brep_found(new_extract, "Pad.Shape.brp", None)

    action = _action(fake_port, visual_diff, file_manager)
    result = action.execute(OpenVisualDiffRequest(repo, "doc.FCStd", "Body/Pad", VisualDiffRequestType.WORKING))

    assert result.is_success is True
    assert visual_diff.old_path is not None and visual_diff.old_path.endswith("Pad.Shape.brp")
    assert visual_diff.new_path is None


def test_execute_opens_visual_diff_when_old_brep_missing(tmp_path: Path) -> None:
    repo = GitRepository(name="repo", absolute_path="/repo")
    fake_port = FakeGitPort()
    visual_diff = FakeVisualDiff()
    file_manager = FakeFileManager()
    old_extract = tmp_path / "old_extract"
    new_extract = tmp_path / "new_extract"
    new_brep = _brep(new_extract)
    file_manager.set_prepared_root("staging", old_extract)
    file_manager.set_prepared_root("working", new_extract)
    file_manager.set_brep_found(old_extract, "Pad.Shape.brp", None)
    file_manager.set_brep_found(new_extract, "Pad.Shape.brp", new_brep)

    action = _action(fake_port, visual_diff, file_manager)
    result = action.execute(OpenVisualDiffRequest(repo, "doc.FCStd", "Body/Pad", VisualDiffRequestType.WORKING))

    assert result.is_success is True
    assert visual_diff.old_path is None
    assert visual_diff.new_path is not None and visual_diff.new_path.endswith("Pad.Shape.brp")


def test_execute_fails_when_brep_missing_from_both_sides(tmp_path: Path) -> None:
    repo = GitRepository(name="repo", absolute_path="/repo")
    fake_port = FakeGitPort()
    visual_diff = FakeVisualDiff()
    file_manager = FakeFileManager()
    old_extract = tmp_path / "old_extract"
    new_extract = tmp_path / "new_extract"
    file_manager.set_prepared_root("staging", old_extract)
    file_manager.set_prepared_root("working", new_extract)
    file_manager.set_brep_found(old_extract, "Pad.Shape.brp", None)
    file_manager.set_brep_found(new_extract, "Pad.Shape.brp", None)

    action = _action(fake_port, visual_diff, file_manager)
    result = action.execute(OpenVisualDiffRequest(repo, "doc.FCStd", "Body/Pad", VisualDiffRequestType.WORKING))

    assert result.is_success is False
    assert result.message == VisualDiffFailureReason.MISSING_BREP.value


def test_execute_fails_when_fcstd_missing_on_both_sides() -> None:
    repo = GitRepository(name="repo", absolute_path="/repo")
    fake_port = FakeGitPort()
    visual_diff = FakeVisualDiff()
    file_manager = FakeFileManager()
    file_manager.set_prepared_root("staging", None)
    file_manager.set_prepared_root("working", None)

    action = _action(fake_port, visual_diff, file_manager)
    result = action.execute(OpenVisualDiffRequest(repo, "doc.FCStd", "Body/Pad", VisualDiffRequestType.WORKING))

    assert result.is_success is False
    assert result.message == VisualDiffFailureReason.MISSING_FCSTD.value


def test_execute_uses_head_and_staging_for_staging_request(tmp_path: Path) -> None:
    repo = GitRepository(name="repo", absolute_path="/repo")
    fake_port = FakeGitPort()
    visual_diff = FakeVisualDiff()
    file_manager = FakeFileManager()
    old_extract = tmp_path / "old_extract"
    new_extract = tmp_path / "new_extract"
    old_brep = _brep(old_extract)
    file_manager.set_prepared_root("HEAD", old_extract)
    file_manager.set_prepared_root("staging", new_extract)
    file_manager.set_brep_found(old_extract, "Pad.Shape.brp", old_brep)

    action = _action(fake_port, visual_diff, file_manager)
    result = action.execute(OpenVisualDiffRequest(repo, "doc.FCStd", "Body/Pad", VisualDiffRequestType.STAGING))

    assert result.is_success is True
    assert file_manager.prepared_revisions == ["HEAD", "staging"]


def test_execute_uses_commit_revisions_for_commit_request(tmp_path: Path) -> None:
    repo = GitRepository(name="repo", absolute_path="/repo")
    fake_port = FakeGitPort()
    visual_diff = FakeVisualDiff()
    file_manager = FakeFileManager()
    old_extract = tmp_path / "old_extract"
    new_extract = tmp_path / "new_extract"
    new_brep = _brep(new_extract)
    file_manager.set_prepared_root("abc~1", old_extract)
    file_manager.set_prepared_root("abc", new_extract)
    file_manager.set_brep_found(new_extract, "Pad.Shape.brp", new_brep)

    action = _action(fake_port, visual_diff, file_manager)
    result = action.execute(
        OpenVisualDiffRequest(repo, "doc.FCStd", "Body/Pad", VisualDiffRequestType.COMMIT, "abc~1", "abc")
    )

    assert result.is_success is True
    assert file_manager.prepared_revisions == ["abc~1", "abc"]


def test_execute_fails_when_commit_request_missing_commits() -> None:
    repo = GitRepository(name="repo", absolute_path="/repo")
    fake_port = FakeGitPort()
    visual_diff = FakeVisualDiff()
    file_manager = FakeFileManager()

    action = _action(fake_port, visual_diff, file_manager)
    result = action.execute(OpenVisualDiffRequest(repo, "doc.FCStd", "Body/Pad", VisualDiffRequestType.COMMIT))

    assert result.is_success is False
    assert result.message == VisualDiffFailureReason.INVALID_REQUEST.value
    assert file_manager.prepared_revisions == []


def test_working_request_saves_modified_document_before_diff(tmp_path: Path) -> None:
    doc = MockDocument(str(tmp_path / "doc.FCStd"))
    freecad_port = FakeFreeCadPort(open_documents=[doc])
    freecad_port._modified_doc_names = {doc.Name}
    repo = GitRepository(name="repo", absolute_path=str(tmp_path))
    fake_port = FakeGitPort()
    visual_diff = FakeVisualDiff()
    file_manager = FakeFileManager()
    old_extract = tmp_path / "old_extract"
    new_extract = tmp_path / "new_extract"
    old_brep = _brep(old_extract)
    new_brep = _brep(new_extract)
    file_manager.set_prepared_root("staging", old_extract)
    file_manager.set_prepared_root("working", new_extract)
    file_manager.set_brep_found(old_extract, "Pad.Shape.brp", old_brep)
    file_manager.set_brep_found(new_extract, "Pad.Shape.brp", new_brep)

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
    old_extract = tmp_path / "old_extract"
    new_extract = tmp_path / "new_extract"
    old_brep = _brep(old_extract)
    file_manager.set_prepared_root("HEAD", old_extract)
    file_manager.set_prepared_root("staging", new_extract)
    file_manager.set_brep_found(old_extract, "Pad.Shape.brp", old_brep)

    action = _action(fake_port, visual_diff, file_manager, freecad_port)
    action.execute(OpenVisualDiffRequest(repo, "doc.FCStd", "Body/Pad", VisualDiffRequestType.STAGING))

    assert doc.saved is False
