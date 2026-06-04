# File responsibility: Internal path-tree helpers for property-diff presentation mapping.
"""Internal path-tree helpers for property-diff presentation mapping."""

from dataclasses import dataclass, field
from typing import Any

from ....domain.diff.models import DiffState, PropertyPathDiff
from ....domain.tree.data_path import PropertyPathType
from ....utils import format_float
from ..presentation_models import PropertyPresentation


@dataclass
class _PathTreeNode:
    """Internal tree node for hierarchical property-path presentation building."""

    name: str
    state: DiffState = DiffState.UNCHANGED
    old_value: Any = None
    new_value: Any = None
    children: dict[str, "_PathTreeNode"] = field(default_factory=dict)


def _split_rel_path(path: str) -> list[str]:
    """Convert flattened path strings into hierarchical segments."""
    if path == "." or not path:
        return []
    tokens: list[str] = []
    segment_buf: list[str] = []
    i = 0
    while i < len(path):
        ch = path[i]
        if ch == ".":
            if segment_buf:
                tokens.append("".join(segment_buf))
                segment_buf = []
            i += 1
            continue
        if ch == "[":
            if segment_buf:
                tokens.append("".join(segment_buf))
                segment_buf = []
            j = path.find("]", i)
            if j == -1:
                # Malformed bracket must stay literal so tree still renders.
                segment_buf.append(ch)
                i += 1
                continue
            tokens.append(path[i : j + 1])
            i = j + 1
            continue
        segment_buf.append(ch)
        i += 1
    if segment_buf:
        tokens.append("".join(segment_buf))
    return tokens


def _format_path_value(path_value: Any, precision: int) -> Any:
    """Format one property-path value for UI display."""
    if path_value is None:
        return None
    if getattr(path_value, "type_", None) == PropertyPathType.FLOAT:
        return format_float(float(path_value.value), precision)
    if getattr(path_value, "type_", None) == PropertyPathType.QUANTITY:
        num = format_float(float(path_value.value), precision)
        unit = path_value.unit if path_value.unit else ""
        return num + " " + unit
    if hasattr(path_value, "value"):
        return path_value.value
    return path_value


def _insert_path_diff(root: _PathTreeNode, path_diff: PropertyPathDiff) -> None:
    """Insert one path diff into a hierarchical tree node."""
    node = root
    for segment in _split_rel_path(path_diff.path):
        node = node.children.setdefault(segment, _PathTreeNode(name=segment))

    node.old_value = path_diff.old_value
    node.new_value = path_diff.new_value
    node.state = path_diff.value_state

    # Expression rows exist only when at least one side carries expression text.
    if path_diff.old_value is not None or path_diff.new_value is not None:
        old_expr = path_diff.old_value.expression if path_diff.old_value is not None else None
        new_expr = path_diff.new_value.expression if path_diff.new_value is not None else None
        if old_expr is not None or new_expr is not None:
            node.children["__expr__"] = _PathTreeNode(
                name="Expression",
                state=path_diff.expression_state,
                old_value=old_expr,
                new_value=new_expr,
            )


def _set_subtree_state(node: _PathTreeNode, state: DiffState) -> None:
    """Apply one diff state to a whole subtree."""
    node.state = state
    for child in node.children.values():
        _set_subtree_state(child, state)


def _collect_leaf_values(node: _PathTreeNode, include_expr: bool = False) -> tuple[list[Any], list[Any]]:
    """Collect leaf old/new values from descendants."""
    old_values: list[Any] = []
    new_values: list[Any] = []
    for name, child in node.children.items():
        if not include_expr and name.startswith("__"):
            continue

        # Nodes with direct value payloads contribute to container summaries.
        if child.old_value is not None:
            old_values.append(child.old_value)
        if child.new_value is not None:
            new_values.append(child.new_value)

        child_old, child_new = _collect_leaf_values(child, include_expr)
        old_values.extend(child_old)
        new_values.extend(child_new)
    return old_values, new_values


def _derive_container_summary(values: list[Any], precision: int) -> str | None:
    """Create FreeCAD-style bracket summary from child leaf values."""
    formatted_values = [_format_path_value(value, precision) for value in values if value is not None]
    rendered_values = [str(value) for value in formatted_values if value is not None]
    if not rendered_values:
        return None
    return "[" + " ".join(rendered_values) + "]"


def _path_tree_to_presentations(node: _PathTreeNode, precision: int) -> list[PropertyPresentation]:
    """Convert internal tree nodes into nested property presentations."""
    out: list[PropertyPresentation] = []
    for key in sorted(node.children.keys(), key=_child_sort_key):
        child = node.children[key]
        grandchildren = _path_tree_to_presentations(child, precision)

        old_value = child.old_value
        new_value = child.new_value
        if old_value is None and new_value is None and grandchildren:
            # Container rows show summarized child values until expanded.
            old_value = _derive_container_summary([grandchild.old_value for grandchild in grandchildren], precision)
            new_value = _derive_container_summary([grandchild.new_value for grandchild in grandchildren], precision)

        out.append(
            PropertyPresentation(
                name=child.name,
                state=child.state,
                old_value=_format_path_value(old_value, precision),
                new_value=_format_path_value(new_value, precision),
                children=grandchildren,
            )
        )
    return out


def _child_sort_key(name: str) -> tuple[int, int | str]:
    """Return deterministic sort key for tree child names."""
    if name.startswith("[") and name.endswith("]"):
        try:
            return (1, int(name[1:-1]))
        except ValueError:
            return (0, name)
    return (0, name)
