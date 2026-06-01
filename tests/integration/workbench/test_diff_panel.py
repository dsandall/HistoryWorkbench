# SPDX-License-Identifier: LGPL-3.0-or-later
"""File responsibility: Integration smoke test for DiffPanelView instantiation and public methods."""

from __future__ import annotations


class TestDiffPanelView:
    """Smoke test for DiffPanelView instantiation and public interface."""

    def test_diff_panel_smoke(self) -> None:
        """Verify DiffPanelView instantiates and exposes required public methods."""
        from freecad.history_wb.qt import QtWidgets
        from freecad.history_wb.ui.presenters.presentation_models import DiffTreePresentation

        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication([])

        from freecad.history_wb.ui import DiffPanelView

        panel = DiffPanelView()
        assert panel is not None

        # Public protocol methods must be callable
        assert callable(panel.show_doc_diffs)
        assert callable(panel.show_summary)

        # Methods execute without errors
        panel.show_doc_diffs([DiffTreePresentation(nodes=[], git_path="parts/A.FCStd", indicators=[])])
        panel.show_summary(0, 0, 0)
