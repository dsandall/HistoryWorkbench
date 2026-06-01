"""File responsibility: History view selection models."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class HistorySelection:
    """Represent selected entry in history list."""

    item_kind: Literal["WORKING_TREE", "STAGING", "COMMIT"]
    commit_hash: str | None
