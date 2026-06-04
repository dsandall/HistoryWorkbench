# File responsibility: Pure node-diff to node-presentation mapping.
"""Pure node-diff to node-presentation mapping helpers."""

from ....domain.diff.models import NodeDiff
from ..presentation_models import NodePresentation


def format_node(node_diff: NodeDiff) -> NodePresentation:
    """Transform one domain node diff into UI presentation data."""
    return NodePresentation(
        path=node_diff.path,
        type_id=node_diff.type_id,
        label=node_diff.label,
        state=node_diff.state,
        has_changes=node_diff.has_deep_changes,
        visual_diff_enabled=_is_visual_diff_enabled(node_diff.type_id),
        children=[format_node(child) for child in node_diff.children],
    )


def _is_visual_diff_enabled(type_id: str) -> bool:
    """Return True when node type supports visual diff."""
    return type_id.startswith("Part::") or type_id.startswith("PartDesign::") or type_id == "Sketcher::SketchObject"
