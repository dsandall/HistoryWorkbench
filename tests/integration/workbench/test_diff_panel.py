# SPDX-License-Identifier: LGPL-3.0-or-later
"""File responsibility: Integration smoke test for HistoryPanelView instantiation and public methods."""

from __future__ import annotations


class TestHistoryPanelView:
    """Smoke test for HistoryPanelView instantiation and public interface."""

    def test_diff_panel_smoke(self) -> None:
        """Verify HistoryPanelView instantiates and exposes required public methods."""
        from freecad.history_wb.qt import QtWidgets
        from freecad.history_wb.ui.presenters.presentation_models import DiffTreePresentation
        from freecad.history_wb.ui.views.document_diff.summary_state import SummaryCounts

        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication([])

        from freecad.history_wb.ui import HistoryPanelView

        panel = HistoryPanelView()
        assert panel is not None

        # Public protocol methods must be callable
        assert callable(panel.document_diff_panel.show_doc_diffs)
        assert callable(panel.document_diff_panel.set_summary_counts)

        # Methods execute without errors
        panel.document_diff_panel.show_doc_diffs(
            [DiffTreePresentation(nodes=[], git_path="parts/A.FCStd", indicators=[])]
        )
        panel.document_diff_panel.set_summary_counts(SummaryCounts())
