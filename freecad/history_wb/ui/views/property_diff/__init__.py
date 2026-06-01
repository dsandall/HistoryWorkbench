"""Module responsibility: Property diff tree facade, delegate, formatters, and item builders."""

from .delegate import PropertyValueDelegate
from .formatters import build_property_tooltip, camelcase_to_spaces, format_property_value, get_property_display_values
from .tree import PropertyDiffTreeWidget
from .tree_items import apply_stored_expansion_state, build_grouped_property_items


__all__ = [
    "PropertyDiffTreeWidget",
    "PropertyValueDelegate",
    "apply_stored_expansion_state",
    "build_grouped_property_items",
    "build_property_tooltip",
    "camelcase_to_spaces",
    "format_property_value",
    "get_property_display_values",
]
