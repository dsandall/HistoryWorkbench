"""File responsibility: Display formatting helpers for history view timestamps."""

from datetime import datetime, timedelta

from ....utils import translate


def format_snapshot_timestamp(iso_string: str) -> str:
    """Format snapshot timestamp string for list display."""
    dt = datetime.fromisoformat(iso_string)
    return dt.strftime("%b %d, %Y %I:%M%p").replace(" 0", " ")


def format_commit_timestamp(timestamp: datetime) -> str:
    """Format commit timestamp for compact history-row display."""
    local_timestamp = timestamp.astimezone() if timestamp.tzinfo is not None else timestamp
    now = datetime.now(local_timestamp.tzinfo) if local_timestamp.tzinfo is not None else datetime.now()

    def _time(dt: datetime) -> str:
        """Format time component without leading zero."""
        return dt.strftime("%I:%M %p").lstrip("0")

    if local_timestamp.date() == now.date():
        return _time(local_timestamp)

    if local_timestamp.date() == (now - timedelta(days=1)).date():
        yesterday_label = translate("History", "Yesterday")
        return f"{yesterday_label} {_time(local_timestamp)}"

    if local_timestamp.year == now.year:
        return local_timestamp.strftime("%b %d ").replace(" 0", " ") + _time(local_timestamp)

    return local_timestamp.strftime("%b %d, %Y ").replace(" 0", " ") + _time(local_timestamp)
