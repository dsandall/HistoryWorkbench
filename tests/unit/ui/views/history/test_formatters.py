"""File responsibility: Unit tests for history timestamp formatting helpers."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest

from freecad.history_wb.ui.views.history import formatters


class _FixedDateTime(datetime):
    """Provide deterministic now() for formatter tests."""

    @classmethod
    def now(cls, tz=None):  # type: ignore[override]
        """Return frozen current time for tests."""
        base = datetime(2024, 3, 20, 15, 0, 0)
        return base if tz is None else base.astimezone(tz)


def test_format_snapshot_timestamp_formats_iso_string() -> None:
    """Snapshot timestamp uses expected readable display format."""
    assert formatters.format_snapshot_timestamp("2024-01-15T10:30:00") == "Jan 15, 2024 10:30AM"


@pytest.mark.parametrize(
    ("timestamp", "expected"),
    [
        ("2024-03-20T14:45:00", "2:45 PM"),
        ("2024-03-19T14:45:00", "Yesterday 2:45 PM"),
        ("2024-02-01T10:00:00", "Feb 1 10:00 AM"),
        ("2023-12-25T08:15:00", "Dec 25, 2023 8:15 AM"),
    ],
)
def test_format_commit_timestamp_matches_display_rules(timestamp: str, expected: str) -> None:
    """Commit timestamp formatter follows today/yesterday/year rules."""
    with patch.object(formatters, "datetime", _FixedDateTime):
        assert formatters.format_commit_timestamp(datetime.fromisoformat(timestamp)) == expected
