# SPDX-License-Identifier: LGPL-3.0-or-later
# File responsibility: Global registry for UI components.
# Provides thread-safe access to application state and nullable panel-scoped
# presenters from entry points without tight coupling to the composition root.
"""Global registry for UI components."""

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .presenters.diff_presenter import DiffPresenter
    from .presenters.git_repository_presenter import GitRepositoryPresenter
    from .state import ApplicationState


class UIRegistry:
    """Registry for UI components.

    Provides centralized access to application-scoped state and panel-scoped
    presenters from entry points without tight coupling to the composition root.
    Application state (ApplicationState) survives panel close cycles.
    Presenters are nullable and cleared when the diff panel is closed.

    Note: This is designed for FreeCAD's single-threaded Python interpreter;
    thread safety is not guaranteed for multi-threaded scenarios.
    """

    def __init__(self) -> None:
        self._diff_presenter: DiffPresenter | None = None
        self._git_repository_presenter: GitRepositoryPresenter | None = None
        self._application_state: ApplicationState | None = None

    @property
    def diff_presenter(self) -> "DiffPresenter | None":
        """Get diff presenter (may be None)."""
        return self._diff_presenter

    @property
    def git_repository_presenter(self) -> "GitRepositoryPresenter | None":
        """Get git repository presenter (may be None when panel is closed)."""
        return self._git_repository_presenter

    @property
    def application_state(self) -> "ApplicationState":
        """Get application state.

        Raises:
            RuntimeError: If not initialized
        """
        if self._application_state is None:
            raise RuntimeError("Application state not initialized. Workbench must be activated first.")
        return self._application_state

    def register_application_state(self, state: "ApplicationState") -> None:
        """Register application state."""
        self._application_state = state

    def register_git_repository_presenter(self, presenter: "GitRepositoryPresenter") -> None:
        """Register git repository presenter."""
        self._git_repository_presenter = presenter

    def register_diff_presenter(self, presenter: "DiffPresenter") -> None:
        """Register diff presenter."""
        self._diff_presenter = presenter

    def clear_presenters(self) -> None:
        """Clear panel-scoped presenters, preserving application state.

        Called when the diff panel is closed. Presenters are tied to the panel
        lifecycle; application state survives and remains accessible to commands.
        """
        self._diff_presenter = None
        self._git_repository_presenter = None

    def clear(self) -> None:
        """Clear entire registry (for testing)."""
        self._diff_presenter = None
        self._git_repository_presenter = None
        self._application_state = None


# Global instance
ui_registry = UIRegistry()


__all__ = ["UIRegistry", "ui_registry"]
