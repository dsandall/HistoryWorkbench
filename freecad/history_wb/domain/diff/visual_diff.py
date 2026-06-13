# File responsibility: Visual diff port interfaces for BREP diff document creation.
"""Visual diff port interfaces."""

from __future__ import annotations

from typing import Protocol


class FreeCADVisualDiffPort(Protocol):
    """Protocol for visual BREP diff document creation."""

    def open_brep_visual_diff(
        self,
        old_brep: bytes | None,
        new_brep: bytes | None,
        document_name: str,
    ) -> object:
        """Open visual diff document for old and new BREP bytes."""
        ...
