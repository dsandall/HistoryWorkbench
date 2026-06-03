"""File responsibility: Shared fixtures for property diff view tests."""

from __future__ import annotations

import pytest

from freecad.history_wb.ui.views.property_diff.tree import PropertyDiffTreeWidget


@pytest.fixture
def widget() -> PropertyDiffTreeWidget:
    """Create a fresh property diff widget per test."""
    return PropertyDiffTreeWidget()
