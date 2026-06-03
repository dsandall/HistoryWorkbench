# SPDX-License-Identifier: LGPL-3.0-or-later
# Module responsibility: Provide fake implementations for testing including FakeLogger,
# FakeSnapshotRepository, FakeSettingsRepository, FakeDiffEngine, fake UI views,
# FakeGitPort, MockDocument, and InMemorySnapshotRepository.
"""Fake implementations for testing."""

from .fake_freecad_port import FakeFreeCadPort, MockDocument
from .fake_git_port import FakeGitPort
from .fake_logger import FakeLogger
from .fake_repositories import (
    FakeDiffEngine,
    FakeSettingsRepository,
    FakeSnapshotRepository,
    InMemorySnapshotRepository,
)
from .fake_views import FakeDialogView, FakeDocumentDiffView, FakeHistoryView, FakePropertyDiffView


__all__ = [
    "FakeLogger",
    "FakeSnapshotRepository",
    "FakeSettingsRepository",
    "FakeDiffEngine",
    "FakeDialogView",
    "FakeDocumentDiffView",
    "FakeHistoryView",
    "FakeFreeCadPort",
    "FakeGitPort",
    "FakePropertyDiffView",
    "InMemorySnapshotRepository",
    "MockDocument",
]
