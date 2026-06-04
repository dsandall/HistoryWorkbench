"""Module responsibility: User interface."""

# Lazy imports for UI widgets - load through project Qt wrapper boundary
try:
    from .views.diff_panel import HistoryPanelView
except ImportError:
    # Qt binding not available (running outside FreeCAD)
    HistoryPanelView = None  # type: ignore

__all__ = ["HistoryPanelView"]
