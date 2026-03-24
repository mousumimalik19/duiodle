"""
Spacer Injection Module for Layout Engine.

Detects significant gaps between UI elements and injects spacer nodes
to represent empty space in the layout tree.

This allows users to manipulate spacing as explicit elements rather
than implicit CSS properties.
"""

from typing import Any, Literal
import uuid


# Default gap threshold as percentage of container dimension
DEFAULT_GAP_THRESHOLD = 0.03


def generate_spacer_id() -> str:
    """
    Generate a unique ID for a spacer node.
    
    Returns:
        Unique spacer ID string.
    """
    return f"spacer_{uuid.uuid4().hex[:8]}"


def create_spacer_node(
    size: float,
    direction: Literal["horizontal", "vertical"],
    position_index: int | None = None
) -> dict[str, Any]:
    """
    Create a spacer node representing empty space.
    
    Args:
        size: Size of the space (normalized 0-1).
        direction: Whether spacer is horizontal or vertical.
        position_index: Optional position in children list.
        
    Returns:
        Spacer node dictionary.
    """
    return {
        "id": generate_spacer_id(),
        "type": "spacer",
        "ui_hint": "spacer",
        "spacer_size": round(size, 4),
        "spacer_direction": direction,
        "position_index": position_index,
        "editable": True,
        "children": []
    }


def calculate_gap(
    node1: dict[str, Any],
    node2: dict[str, Any],
    direction: Literal["row", "column"]
) -> float:
    """
    Calculate the gap between two adjacent nodes.
    
    Args:
        node1: First node (should come before node2).
        node2: Second node.
        direction: Layout direction ("row" or "column").
        
    Returns:
        Gap size as float. Negative indicates overlap.
    """
    bbox1 = node1.get("bbox", {})
    bbox2 = node2.get("bbox", {})
    
    if direction == "row":
        # Horizontal gap
        node1_end = float(bbox1.get("x", 0)) + float(bbox1.get("width", 0))
        node2_start = float(bbox2.get("x", 0))
        return node2_start - node1_end
    else:
        # Vertical gap
        node1_end = float(bbox1.get("y", 0)) + float(bbox1.get("height", 0))
        node2_start = float(bbox2.get("y", 0))
        return node2_start - node1_end


def sort_by_position(
    children: list[dict[str, Any]],
    direction: Literal["row", "column"]
) -> list[dict[str, Any]]:
    """
    Sort children by position in layout direction.
    
    Args:
        children: List of child nodes.
        direction: Layout direction.
        
    Returns:
        Sorted list of children.
    """
    if direction == "row":
        return sorted(
            children,
            key=lambda n: float(n.get("bbox", {}).get("x", 0))
        )
    else:
        return sorted(
            children,
            key=lambda n: float(n.get("bbox", {}).get("y", 0))
        )


def inject_spacers(
    children: list[dict[str, Any]],
    direction: Literal["row", "column"] = "column",
    gap_threshold: float = DEFAULT_GAP_THRESHOLD,
    normalize_sizes: bool = True
) -> list[dict[str, Any]]:
    """
    Inject spacer nodes between children with significant gaps.
    
    Analyzes gaps between consecutive elements and inserts spacer
    nodes where gaps exceed the threshold.
    
    Args:
        children: List of child nodes to analyze.
        direction: Layout direction ("row" or "column").
        gap_threshold: Minimum gap size to create a spacer.
        normalize_sizes: If True, round spacer sizes to grid.
        
    Returns:
        New list with spacer nodes injected between elements.
        
    Example:
        >>> children = [
        ...     {"id": "a", "bbox": {"x": 0, "y": 0, "width": 0.2, "height": 0.1}},
        ...     {"id": "b", "bbox": {"x": 0, "y": 0.3, "width": 0.2, "height": 0.1}}
        ... ]
        >>> result = inject_spacers(children, "column")
        >>> len(result)  # a, spacer, b
        3
    """
    if len(children) <= 1:
        return list(children)  # Return copy
    
    # Sort by position
    sorted_children = sort_by_position(children, direction)
    
    spacer_direction: Literal["horizontal", "vertical"] = (
        "horizontal" if direction == "row" else "vertical"
    )
    
    result: list[dict[str, Any]] = []
    
    for i, child in enumerate(sorted_children):
        result.append(child)
        
        # Check gap to next child
        if i < len(sorted_children) - 1:
            next_child = sorted_children[i + 1]
            gap = calculate_gap(child, next_child, direction)
            
            if gap >= gap_threshold:
                # Normalize size if requested
                size = gap
                if normalize_sizes:
                    size = round(size, 3)
                
                spacer = create_spacer_node(
                    size=size,
                    direction=spacer_direction,
                    position_index=len(result)
                )
                result.append(spacer)
    
    return result


def inject_edge_spacers(
    children: list[dict[str, Any]],
    container_bbox: dict[str, float],
    direction: Literal["row", "column"] = "column",
    gap_threshold: float = DEFAULT_GAP_THRESHOLD
) -> list[dict[str, Any]]:
    """
    Inject spacers at container edges if there's padding.
    
    Adds spacers at the start and end of children if there's
    significant space between children and container edges.
    
    Args:
        children: List of child nodes.
        container_bbox: Container bounding box.
        direction: Layout direction.
        gap_threshold: Minimum gap for spacer creation.
        
    Returns:
        List with edge spacers added if needed.
    """
    if not children:
        return []
    
    sorted_children = sort_by_position(children, direction)
    spacer_direction: Literal["horizontal", "vertical"] = (
        "horizontal" if direction == "row" else "vertical"
    )
    
    result: list[dict[str, Any]] = []
    
    # Calculate edge gaps
    if direction == "row":
        container_start = float(container_bbox.get("x", 0))
        container_end = container_start + float(container_bbox.get("width", 1))
        
        first_child_start = float(sorted_children[0].get("bbox", {}).get("x", 0))
        last_child_bbox = sorted_children[-1].get("bbox", {})
        last_child_end = (
            float(last_child_bbox.get("x", 0)) + 
            float(last_child_bbox.get("width", 0))
        )
    else:
        container_start = float(container_bbox.get("y", 0))
        container_end = container_start + float(container_bbox.get("height", 1))
        
        first_child_start = float(sorted_children[0].get("bbox", {}).get("y", 0))
        last_child_bbox = sorted_children[-1].get("bbox", {})
        last_child_end = (
            float(last_child_bbox.get("y", 0)) + 
            float(last_child_bbox.get("height", 0))
        )
    
    # Start edge spacer
    start_gap = first_child_start - container_start
    if start_gap >= gap_threshold:
        result.append(create_spacer_node(
            size=round(start_gap, 3),
            direction=spacer_direction,
            position_index=0
        ))
    
    # Add children
    result.extend(sorted_children)
    
    # End edge spacer
    end_gap = container_end - last_child_end
    if end_gap >= gap_threshold:
        result.append(create_spacer_node(
            size=round(end_gap, 3),
            direction=spacer_direction,
            position_index=len(result)
        ))
    
    return result


def detect_grid_gaps(
    children: list[dict[str, Any]],
    tolerance: float = 0.02
) -> dict[str, float | None]:
    """
    Detect consistent row and column gaps (CSS grid-style).
    
    Analyzes spacing patterns to find consistent gaps that could
    be represented as grid-row-gap and grid-column-gap.
    
    Args:
        children: List of child nodes.
        tolerance: Variance tolerance for "consistent" gaps.
        
    Returns:
        Dictionary with 'row_gap' and 'column_gap' values,
        or None if gaps are inconsistent.
    """
    if len(children) < 2:
        return {"row_gap": None, "column_gap": None}
    
    h_gaps: list[float] = []
    v_gaps: list[float] = []
    
    # Sort for horizontal analysis
    sorted_by_x = sorted(
        children,
        key=lambda n: float(n.get("bbox", {}).get("x", 0))
    )
    
    # Sort for vertical analysis
    sorted_by_y = sorted(
        children,
        key=lambda n: float(n.get("bbox", {}).get("y", 0))
    )
    
    # Collect horizontal gaps
    for i in range(len(sorted_by_x) - 1):
        gap = calculate_gap(sorted_by_x[i], sorted_by_x[i + 1], "row")
        if gap > 0:
            h_gaps.append(gap)
    
    # Collect vertical gaps
    for i in range(len(sorted_by_y) - 1):
        gap = calculate_gap(sorted_by_y[i], sorted_by_y[i + 1], "column")
        if gap > 0:
            v_gaps.append(gap)
    
    result: dict[str, float | None] = {
        "row_gap": None,
        "column_gap": None
    }
    
    # Check for consistent horizontal gaps
    if h_gaps:
        h_variance = max(h_gaps) - min(h_gaps)
        if h_variance <= tolerance:
            result["column_gap"] = round(sum(h_gaps) / len(h_gaps), 3)
    
    # Check for consistent vertical gaps
    if v_gaps:
        v_variance = max(v_gaps) - min(v_gaps)
        if v_variance <= tolerance:
            result["row_gap"] = round(sum(v_gaps) / len(v_gaps), 3)
    
    return result


def remove_spacers(
    children: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Remove all spacer nodes from children list.
    
    Useful for re-processing or when spacers are no longer needed.
    
    Args:
        children: List of child nodes, possibly including spacers.
        
    Returns:
        List with spacer nodes removed.
    """
    return [
        child for child in children
        if child.get("type") != "spacer"
    ]


def merge_adjacent_spacers(
    children: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Merge consecutive spacer nodes into single spacers.
    
    Cleans up layouts where multiple spacers ended up adjacent.
    
    Args:
        children: List of child nodes.
        
    Returns:
        List with adjacent spacers merged.
    """
    if not children:
        return []
    
    result: list[dict[str, Any]] = []
    pending_spacer: dict[str, Any] | None = None
    
    for child in children:
        if child.get("type") == "spacer":
            if pending_spacer is None:
                pending_spacer = dict(child)
            else:
                # Merge with pending spacer
                pending_spacer["spacer_size"] = (
                    float(pending_spacer.get("spacer_size", 0)) +
                    float(child.get("spacer_size", 0))
                )
        else:
            # Non-spacer node
            if pending_spacer is not None:
                result.append(pending_spacer)
                pending_spacer = None
            result.append(child)
    
    # Don't forget trailing spacer
    if pending_spacer is not None:
        result.append(pending_spacer)
    
    return result
