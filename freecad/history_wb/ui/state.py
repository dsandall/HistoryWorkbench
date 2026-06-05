# SPDX-License-Identifier: LGPL-3.0-or-later
# File responsibility: Application-scoped state holder (frontend state, like Pinia/Redux).
# This module contains the ApplicationState dataclass which serves as an in-memory state
# holder for the UI layer. It stores the currently detected GitRepository and survives
# diff-panel close cycles, remaining accessible to commands even when the panel is closed.
# Domain layer must NOT depend on this class.
"""Application-scoped state holder (frontend state, like Pinia/Redux)."""

from dataclasses import dataclass

from freecad.history_wb.domain.git.models import GitRepository


@dataclass
class ApplicationState:
    """In-memory state holder for application-scoped UI state.

    This class is for UI/presentation layer state ONLY.
    It is analogous to frontend state management solutions like Pinia (Vue)
    or Redux (React) - it holds application-wide UI state that is accessed
    by presenters and commands but never by domain or application layer components.

    This class stores the currently detected GitRepository.
    Created once during first workbench activation and reused across all entry points.
    Survives diff-panel close cycles and is accessible to commands even when
    the panel is closed.

    Architecture note: Domain layer must NOT depend on this class.
    Future enhancements may add observable properties using Qt signals.
    """

    git_repository: GitRepository | None = None


__all__ = ["ApplicationState"]
