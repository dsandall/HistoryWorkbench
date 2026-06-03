# SPDX-License-Identifier: LGPL-3.0-or-later
"""File responsibility: FreeCAD command entry points for the Diff Workbench.

This module defines the FreeCAD commands that bridge user interactions
(toolbar/menu clicks) with handlers, presenters, and application actions.
Commands instantiate handlers directly from the container and DialogView,
without requiring the diff panel to be open.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, TypedDict

from ..qt import QtCore, QtWidgets
from ..resources import ICONPATH
from ..utils import Log, translate


if TYPE_CHECKING:
    QWidget = QtWidgets.QWidget

    from ..application.di.container import ApplicationContainer
    from ..domain.git.models import GitRepository
    from ..ui.presenters.git_repository.author_configuration_handler import (
        AuthorConfigurationHandler,
    )
    from ..ui.presenters.git_repository.commit_iteration_handler import (
        CommitIterationHandler,
    )
    from ..ui.views.diff_panel import DialogView


def _main_window_parent(container) -> QWidget | None:
    """Get the FreeCAD main window as a parent widget for dialogs.

    Args:
        container: The application container with _freecad_port attribute

    Returns:
        QWidget parent or None if not available
    """
    main_window = container._freecad_port.get_main_window()
    return main_window  # type: ignore[return-value]


def _create_dialog_view(container: ApplicationContainer) -> DialogView:
    """Create a DialogView anchored to the FreeCAD main window."""
    from ..ui.views.diff_panel import DialogView

    parent = _main_window_parent(container)
    if parent is None:
        raise RuntimeError("FreeCAD main window not available")
    return DialogView(parent)


def _get_application_repo_or_warn(
    container: ApplicationContainer,
    dialog_view: DialogView,
) -> GitRepository | None:
    """Return the current git repository from application state, or show a warning.

    Returns:
        GitRepository if set, None otherwise (warning already shown).
    """
    from ..ui.registry import ui_registry

    repo = ui_registry.application_state.git_repository
    if repo is None:
        dialog_view.show_warning_message(
            translate("History", "No Project"),
            translate("History", "No project detected. Open a FreeCAD document in a project first."),
        )
    return repo


def _refresh_git_repository_presenter_if_open() -> None:
    """Refresh the git repository presenter if the panel is currently open."""
    from ..ui.registry import ui_registry

    presenter = ui_registry.git_repository_presenter
    if presenter is not None:
        presenter.refresh_repository_and_commits()


def _build_author_configuration_handler(
    container: ApplicationContainer,
    dialog_view: DialogView,
) -> AuthorConfigurationHandler:
    """Build an AuthorConfigurationHandler from container actions and dialog callbacks."""
    from ..ui.presenters.git_repository.author_configuration_handler import AuthorConfigurationHandler

    return AuthorConfigurationHandler(
        get_git_identity_action=container.get_git_identity_action,
        save_git_identity_action=container.save_git_identity_action,
        can_write_global_git_identity_action=container.can_write_global_git_identity_action,
        show_configure_author_dialog=dialog_view.show_configure_author_dialog,
        show_warning_message=dialog_view.show_warning_message,
        show_error_message=dialog_view.show_error_message,
    )


def _build_commit_iteration_handler(
    container: ApplicationContainer,
    dialog_view: DialogView,
) -> CommitIterationHandler:
    """Build a CommitIterationHandler from container actions, dialog callbacks, and an author handler."""
    from ..ui.presenters.git_repository.commit_iteration_handler import CommitIterationHandler

    author_handler = _build_author_configuration_handler(container, dialog_view)
    return CommitIterationHandler(
        get_staged_file_paths_action=container.get_staged_file_paths_action,
        commit_staging_action=container.commit_staging_action,
        get_git_identity_action=container.get_git_identity_action,
        author_configuration_handler=author_handler,
        show_save_iteration_dialog=dialog_view.show_save_iteration_dialog,
        show_warning_message=dialog_view.show_warning_message,
        show_info_message=dialog_view.show_info_message,
        show_error_message=dialog_view.show_error_message,
    )


class CommandResources(TypedDict):
    """Shape of FreeCAD command metadata returned by GetResources."""

    MenuText: object
    ToolTip: object
    Pixmap: str


class _ConfigureAuthorCommand:
    """Command to configure author identity."""

    def GetResources(self) -> CommandResources:
        """Return FreeCAD command metadata for UI integration."""
        return {
            "MenuText": QtCore.QT_TRANSLATE_NOOP("HistoryConfigureAuthorCommand", "Configure Author"),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP("HistoryConfigureAuthorCommand", "Configure author name and email"),
            "Pixmap": os.path.join(ICONPATH, "ConfigureGit.svg"),
        }

    def IsActive(self) -> bool:
        """Return whether the command should be enabled."""
        return True

    def Activated(self) -> None:
        """FreeCAD calls this when user clicks toolbar button."""
        from .._container import get_container

        container = get_container()
        try:
            dialog_view = _create_dialog_view(container)
        except RuntimeError:
            return

        repo = _get_application_repo_or_warn(container, dialog_view)
        if repo is None:
            return

        handler = _build_author_configuration_handler(container, dialog_view)
        handler.execute(repo)


class _CommitCommand:
    """Command to save iteration."""

    def GetResources(self) -> CommandResources:
        """Return FreeCAD command metadata for UI integration."""
        return {
            "MenuText": QtCore.QT_TRANSLATE_NOOP("HistoryCommit", "Save Iteration"),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP("HistoryCommit", "Save reviewed changes as an iteration"),
            "Pixmap": os.path.join(ICONPATH, "Commit.svg"),
        }

    def IsActive(self) -> bool:
        """Return whether the command should be enabled."""
        return True  # Always enabled; validation happens in Activated()

    def Activated(self) -> None:
        """FreeCAD calls this when user clicks toolbar button."""
        from .._container import get_container

        container = get_container()
        try:
            dialog_view = _create_dialog_view(container)
        except RuntimeError:
            return

        repo = _get_application_repo_or_warn(container, dialog_view)
        if repo is None:
            return

        handler = _build_commit_iteration_handler(container, dialog_view)
        success = handler.execute(repo)
        if success:
            Log.info("Commit successful")
            _refresh_git_repository_presenter_if_open()


class _RefreshRepositoryCommand:
    """Command to refresh project detection and reload iterations."""

    def GetResources(self) -> CommandResources:
        """Return FreeCAD command metadata for UI integration."""
        return {
            "MenuText": QtCore.QT_TRANSLATE_NOOP("HistoryRefreshRepository", "Refresh Project"),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "HistoryRefreshRepository",
                "Refresh the detected project and reload iterations.\n"
                "Open at least one FreeCAD document "
                "located within a project before running this command.\n"
                "How it works: open FreeCAD "
                "documents are checked one by one until one is found to be located within a project.",
            ),
            "Pixmap": os.path.join(ICONPATH, "RefreshRepository.svg"),
        }

    def IsActive(self) -> bool:
        """Return whether the command should be enabled."""
        return True

    def Activated(self) -> None:
        """FreeCAD calls this when user clicks toolbar button."""
        from .._container import get_container
        from ..ui.registry import ui_registry

        presenter = ui_registry.git_repository_presenter
        if presenter is not None:
            presenter.refresh_repository_and_commits()
            return

        # Panel closed; run repository detection directly and update application state
        container = get_container()
        result = container.find_active_git_repository_action.execute()

        if result.is_success:
            ui_registry.application_state.git_repository = result.data
        else:
            # Clear stale repo state when refresh fails
            ui_registry.application_state.git_repository = None


class _InitializeGitRepositoryCommand:
    """Command to initialize a git repository from open document directories."""

    def GetResources(self) -> CommandResources:
        """Return FreeCAD command metadata for UI integration."""
        return {
            "MenuText": QtCore.QT_TRANSLATE_NOOP("HistoryInitializeGitRepository", "Initialize Project"),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "HistoryInitializeGitRepository",
                "Initialize a new project in the selected directory",
            ),
            "Pixmap": os.path.join(ICONPATH, "CreateGitRepository.svg"),
        }

    def IsActive(self) -> bool:
        """Return whether the command should be enabled."""
        return True

    def Activated(self) -> None:
        """FreeCAD calls this when user clicks toolbar button."""
        from .._container import get_container
        from ..ui.presenters.git_repository.initialize_repository_handler import InitializeRepositoryHandler
        from ..ui.registry import ui_registry

        container = get_container()
        try:
            dialog_view = _create_dialog_view(container)
        except RuntimeError:
            return

        handler = InitializeRepositoryHandler(
            get_candidates_action=container.get_git_repository_init_candidates_action,
            initialize_action=container.initialize_git_repository_action,
            show_init_dialog=dialog_view.show_init_repository_dialog,
            show_info_message=dialog_view.show_info_message,
            show_error_message=dialog_view.show_error_message,
            application_state=ui_registry.application_state,
        )
        initialized = handler.execute()
        if initialized:
            _refresh_git_repository_presenter_if_open()


class _OpenAllDocumentsInRepositoryCommand:
    """Command to open all .FCStd documents under detected repository."""

    def GetResources(self) -> CommandResources:
        """Return FreeCAD command metadata for UI integration."""
        return {
            "MenuText": QtCore.QT_TRANSLATE_NOOP(
                "HistoryOpenAllDocumentsInRepository",
                "Open All Documents in Project",
            ),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "HistoryOpenAllDocumentsInRepository",
                "Open every .FCStd file found in the project. Useful for generating en masse.",
            ),
            "Pixmap": os.path.join(ICONPATH, "OpenAllDocuments.svg"),
        }

    def IsActive(self) -> bool:
        """Return whether the command should be enabled."""
        return True

    def Activated(self) -> None:
        """FreeCAD calls this when user clicks toolbar button."""
        from .._container import get_container

        container = get_container()
        try:
            dialog_view = _create_dialog_view(container)
        except RuntimeError:
            return

        repo = _get_application_repo_or_warn(container, dialog_view)
        if repo is None:
            return

        container.open_all_documents_in_repository_action.execute(repo)


class _UpdateGitIgnoreCommand:
    """Command to edit repository .gitignore content."""

    def GetResources(self) -> CommandResources:
        """Return FreeCAD command metadata for UI integration."""
        return {
            "MenuText": QtCore.QT_TRANSLATE_NOOP("HistoryUpdateGitIgnore", "Edit Ignored Files"),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "HistoryUpdateGitIgnore",
                "Edit project ignored files list (.gitignore)",
            ),
            "Pixmap": os.path.join(ICONPATH, "GitIgnore.svg"),
        }

    def IsActive(self) -> bool:
        """Return whether the command should be enabled."""
        return True

    def Activated(self) -> None:
        """FreeCAD calls this when user clicks toolbar button."""
        from .._container import get_container
        from ..ui.presenters.git_repository.gitignore_handler import GitIgnoreHandler

        container = get_container()
        try:
            dialog_view = _create_dialog_view(container)
        except RuntimeError:
            return

        repo = _get_application_repo_or_warn(container, dialog_view)
        if repo is None:
            return

        handler = GitIgnoreHandler(
            get_content_action=container.get_gitignore_content_action,
            update_action=container.update_gitignore_action,
            show_editor_dialog=dialog_view.show_gitignore_editor_dialog,
            show_info_message=dialog_view.show_info_message,
            show_error_message=dialog_view.show_error_message,
        )
        handler.execute(repo)


class _RecomputeAllOpenDocumentsCommand:
    """Command to recompute all open documents in FreeCAD."""

    def GetResources(self) -> CommandResources:
        """Return FreeCAD command metadata for UI integration."""
        return {
            "MenuText": QtCore.QT_TRANSLATE_NOOP("HistoryRecomputeAllOpenDocuments", "Recompute All"),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP("HistoryRecomputeAllOpenDocuments", "Recompute every open document"),
            "Pixmap": os.path.join(ICONPATH, "RecomputeAll.svg"),
        }

    def IsActive(self) -> bool:
        """Return whether the command should be enabled."""
        return True

    def Activated(self) -> None:
        """FreeCAD calls this when user clicks toolbar button."""
        from .._container import get_container

        container = get_container()
        container.recompute_all_open_documents_action.execute()


class _RecomputeActiveDocumentCommand:
    """Command to recompute the active document in FreeCAD."""

    def GetResources(self) -> CommandResources:
        """Return FreeCAD command metadata for UI integration."""
        return {
            "MenuText": QtCore.QT_TRANSLATE_NOOP("HistoryRecomputeActiveDocument", "Recompute Active Document"),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP("HistoryRecomputeActiveDocument", "Recompute the active document"),
            "Pixmap": os.path.join(ICONPATH, "RecomputeActiveDocument.svg"),
        }

    def IsActive(self) -> bool:
        """Return whether the command should be enabled."""
        return True

    def Activated(self) -> None:
        """FreeCAD calls this when user clicks toolbar button."""
        from .._container import get_container

        container = get_container()

        # Use FreeCAD port to recompute the active document
        container._freecad_port.try_recompute_active_document()


class _OpenDiffWindowCommand:
    """Command to open or focus the history panel."""

    def GetResources(self) -> CommandResources:
        """Return FreeCAD command metadata for UI integration."""
        return {
            "MenuText": QtCore.QT_TRANSLATE_NOOP("HistoryOpenDiffWindow", "Open History Panel"),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP("HistoryOpenDiffWindow", "Open history panel view"),
            "Pixmap": os.path.join(ICONPATH, "Logo.svg"),
        }

    def IsActive(self) -> bool:
        """Return whether the command should be enabled."""
        return True

    def Activated(self) -> None:
        """FreeCAD calls this when user clicks toolbar button."""
        import FreeCADGui as Gui  # pylint: disable=import-error

        # Get the History workbench instance and show/create the diff panel
        workbench = Gui.getWorkbench("HistoryWorkbench")
        if workbench is not None:
            workbench.create_or_show_diff_panel()


class _CloseDiffWindowsCommand:
    """Command to close all Diff_* windows without saving."""

    def GetResources(self) -> CommandResources:
        """Return FreeCAD command metadata for UI integration."""
        return {
            "MenuText": QtCore.QT_TRANSLATE_NOOP("HistoryCloseDiffWindows", "Close Comparison Windows"),
            "ToolTip": QtCore.QT_TRANSLATE_NOOP(
                "HistoryCloseDiffWindows",
                "Close every document starting with 'Diff_' without saving",
            ),
            "Pixmap": os.path.join(ICONPATH, "DiffCloseDiffWindows.svg"),
        }

    def IsActive(self) -> bool:
        """Return whether the command should be enabled."""
        return True

    def Activated(self) -> None:
        """FreeCAD calls this when user clicks toolbar button."""
        import FreeCAD as App  # pylint: disable=import-error

        # Get list of document names to close (iterate over copy to avoid modification during iteration)
        docs_to_close = [doc_name for doc_name in App.listDocuments() if doc_name.startswith("Diff_")]

        # Close each document without saving
        for doc_name in docs_to_close:
            App.closeDocument(doc_name)


def register_commands() -> None:
    """Register the Diff Workbench commands with FreeCAD."""
    import FreeCADGui as Gui  # pylint: disable=import-error

    Gui.addCommand("HistoryConfigureAuthorCommand", _ConfigureAuthorCommand())
    Gui.addCommand("HistoryCommit", _CommitCommand())
    Gui.addCommand("HistoryRefreshRepository", _RefreshRepositoryCommand())
    Gui.addCommand("HistoryInitializeGitRepository", _InitializeGitRepositoryCommand())
    Gui.addCommand("HistoryUpdateGitIgnore", _UpdateGitIgnoreCommand())
    Gui.addCommand("HistoryOpenAllDocumentsInRepository", _OpenAllDocumentsInRepositoryCommand())
    Gui.addCommand("HistoryRecomputeAllOpenDocuments", _RecomputeAllOpenDocumentsCommand())
    Gui.addCommand("HistoryRecomputeActiveDocument", _RecomputeActiveDocumentCommand())
    Gui.addCommand("HistoryOpenDiffWindow", _OpenDiffWindowCommand())
    Gui.addCommand("HistoryCloseDiffWindows", _CloseDiffWindowsCommand())
