"""File responsibility: Property diff tree container that wires headers, delegate, and item builders."""

from __future__ import annotations

from ....domain.config import FLOAT_PRECISION as DEFAULT_FLOAT_PRECISION
from ....domain.settings import SettingsRepository
from ....qt import QtWidgets
from ....utils import translate
from ...presenters.presentation_models import PropertyPresentation
from .delegate import PropertyValueDelegate
from .tree_items import apply_stored_expansion_state, build_grouped_property_items


__all__ = ["PropertyDiffTreeWidget"]


class PropertyDiffTreeWidget(QtWidgets.QTreeWidget):
    """Widget that renders grouped property diffs in three columns."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        settings_repo: SettingsRepository | None = None,
    ) -> None:
        super().__init__(parent)
        self._settings_repo = settings_repo
        self._default_precision = DEFAULT_FLOAT_PRECISION
        self._property_value_delegate = PropertyValueDelegate(self)
        self._setup_tree()

    def _setup_tree(self) -> None:
        """Configure headers, resize behavior, delegate, and edit triggers."""
        self.setColumnCount(3)
        self.setHeaderLabels(
            [
                translate("History", "Property"),
                translate("History", "Old Value"),
                translate("History", "New Value"),
            ]
        )
        self.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.header().setStretchLastSection(True)
        self.setItemDelegate(self._property_value_delegate)
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked)

    def clear_property_diff(self) -> None:
        """Clear all property diff entries from the tree widget."""
        self.clear()

    def show_property_diff(self, properties: list[PropertyPresentation]) -> None:
        """Render property diffs grouped by their group name."""
        self.clear_property_diff()
        if not properties:
            return

        items = build_grouped_property_items(properties, self.palette(), self._get_precision())
        self.addTopLevelItems(items)
        apply_stored_expansion_state(items)

    def _get_precision(self) -> int:
        """Read configured float precision or fall back to default precision."""
        if self._settings_repo is not None:
            try:
                return self._settings_repo.get_settings().float_precision
            except (AttributeError, RuntimeError):
                pass
        return self._default_precision
