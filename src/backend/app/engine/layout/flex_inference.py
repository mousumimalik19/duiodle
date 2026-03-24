"""
Flex Inference Module for Layout Engine.

Analyzes spatial relationships between sibling elements to determine
whether they should be arranged as rows (horizontal) or columns (vertical).

This module infers flexbox-compatible layout directions.
"""

from typing import Any, Literal
from enum import Enum


class FlexDirection(str, Enum):
    """Flexbox direction values."""
    ROW = "row"
    COLUMN = "column"
    ROW_REVERSE = "row-reverse"
    COLUMN_REVERSE = "column-reverse"


def get_bbox_center(bbox: dict[str, float]) -> tuple[float, float]:
    """
    Calculate the center point of a bounding box.
    
    Args:
        bbox: Bounding box with x, y, width, height.
        
    Returns:
        Tuple of (center_x, center_y).
    """
    x = float(bbox.get("x", 0))
    y = float(bbox.get("y", 0))
    w = float(bbox.get("width", 0))
    h = float(bbox.get("height", 0))
    
    return (x + w / 2, y + h / 2)


def calculate_horizontal_spread(nodes: list[dict[str, Any]]) -> float:
    """
    Calculate how spread out nodes are horizontally.
    
    Args:
        nodes: List of nodes with bbox fields.
        
    Returns:
        Horizontal spread as ratio of total width covered.
    """
    if len(nodes) < 2:
        return 0.0
    
    x_positions = []
    for node in nodes:
        bbox = node.get("bbox", {})
        x = float(bbox.get("x", 0))
        w = float(bbox.get("width", 0))
        x_positions.append((x, x + w))
    
    min_x = min(pos[0] for pos in x_positions)
    max_x = max(pos[1] for pos in x_positions)
    
    return max_x - min_x


def calculate_vertical_spread(nodes: list[dict[str, Any]]) -> float:
    """
    Calculate how spread out nodes are vertically.
    
    Args:
        nodes: List of nodes with bbox fields.
        
    Returns:
        Vertical spread as ratio of total height covered.
    """
    if len(nodes) < 2:
        return 0.0
    
    y_positions = []
    for node in nodes:
        bbox = node.get("bbox", {})
        y = float(bbox.get("y", 0))
        h = float(bbox.get("height", 0))
        y_positions.append((y, y + h))
    
    min_y = min(pos[0] for pos in y_positions)
    max_y = max(pos[1] for pos in y_positions)
    
    return max_y - min_y


def calculate_horizontal_gaps(nodes: list[dict[str, Any]]) -> list[float]:
    """
    Calculate gaps between horizontally adjacent elements.
    
    Args:
        nodes: List of nodes with bbox fields.
        
    Returns:
        List of horizontal gap sizes between consecutive elements.
    """
    if len(nodes) < 2:
        return []
    
    # Sort by x position
    sorted_nodes = sorted(
        nodes,
        key=lambda n: float(n.get("bbox", {}).get("x", 0))
    )
    
    gaps = []
    for i in range(len(sorted_nodes) - 1):
        bbox1 = sorted_nodes[i].get("bbox", {})
        bbox2 = sorted_nodes[i + 1].get("bbox", {})
        
        right_edge = float(bbox1.get("x", 0)) + float(bbox1.get("width", 0))
        left_edge = float(bbox2.get("x", 0))
        
        gaps.append(left_edge - right_edge)
    
    return gaps


def calculate_vertical_gaps(nodes: list[dict[str, Any]]) -> list[float]:
    """
    Calculate gaps between vertically adjacent elements.
    
    Args:
        nodes: List of nodes with bbox fields.
        
    Returns:
        List of vertical gap sizes between consecutive elements.
    """
    if len(nodes) < 2:
        return []
    
    # Sort by y position
    sorted_nodes = sorted(
        nodes,
        key=lambda n: float(n.get("bbox", {}).get("y", 0))
    )
    
    gaps = []
    for i in range(len(sorted_nodes) - 1):
        bbox1 = sorted_nodes[i].get("bbox", {})
        bbox2 = sorted_nodes[i + 1].get("bbox", {})
        
        bottom_edge = float(bbox1.get("y", 0)) + float(bbox1.get("height", 0))
        top_edge = float(bbox2.get("y", 0))
        
        gaps.append(top_edge - bottom_edge)
    
    return gaps


def elements_horizontally_aligned(
    nodes: list[dict[str, Any]],
    tolerance: float = 0.05
) -> bool:
    """
    Check if elements are roughly horizontally aligned (same row).
    
    Args:
        nodes: List of nodes with bbox fields.
        tolerance: Maximum y-coordinate variance allowed.
        
    Returns:
        True if elements appear to be in the same row.
    """
    if len(nodes) < 2:
        return True
    
    y_centers = [
        get_bbox_center(n.get("bbox", {}))[1]
        for n in nodes
    ]
    
    y_variance = max(y_centers) - min(y_centers)
    return y_variance <= tolerance


def elements_vertically_aligned(
    nodes: list[dict[str, Any]],
    tolerance: float = 0.05
) -> bool:
    """
    Check if elements are roughly vertically aligned (same column).
    
    Args:
        nodes: List of nodes with bbox fields.
        tolerance: Maximum x-coordinate variance allowed.
        
    Returns:
        True if elements appear to be in the same column.
    """
    if len(nodes) < 2:
        return True
    
    x_centers = [
        get_bbox_center(n.get("bbox", {}))[0]
        for n in nodes
    ]
    
    x_variance = max(x_centers) - min(x_centers)
    return x_variance <= tolerance


def infer_flex_direction(
    children: list[dict[str, Any]],
    overlap_threshold: float = 0.3
) -> Literal["row", "column"]:
    """
    Infer the flex direction for a container based on children positions.
    
    Analyzes the spatial distribution of children to determine whether
    they are arranged horizontally (row) or vertically (column).
    
    Args:
        children: List of child nodes with bbox fields.
        overlap_threshold: Threshold for detecting overlapping layouts.
        
    Returns:
        "row" if children are arranged horizontally, "column" otherwise.
        
    Algorithm:
        1. If elements are horizontally aligned (same y), return "row"
        2. If elements are vertically aligned (same x), return "column"
        3. Compare horizontal vs vertical spread
        4. Check gap consistency in each direction
        5. Return direction with better spacing pattern
    """
    if len(children) <= 1:
        return "column"  # Default for single/no children
    
    # Quick check: are all elements on the same row?
    if elements_horizontally_aligned(children, tolerance=0.05):
        h_gaps = calculate_horizontal_gaps(children)
        # Verify they don't overlap significantly
        if all(gap >= -overlap_threshold for gap in h_gaps):
            return "row"
    
    # Quick check: are all elements in the same column?
    if elements_vertically_aligned(children, tolerance=0.05):
        v_gaps = calculate_vertical_gaps(children)
        if all(gap >= -overlap_threshold for gap in v_gaps):
            return "column"
    
    # Compare spreads
    h_spread = calculate_horizontal_spread(children)
    v_spread = calculate_vertical_spread(children)
    
    # Analyze gaps
    h_gaps = calculate_horizontal_gaps(children)
    v_gaps = calculate_vertical_gaps(children)
    
    # Calculate positive gap totals (ignoring overlaps)
    h_positive_gaps = sum(max(0, g) for g in h_gaps)
    v_positive_gaps = sum(max(0, g) for g in v_gaps)
    
    # Count overlaps
    h_overlaps = sum(1 for g in h_gaps if g < 0)
    v_overlaps = sum(1 for g in v_gaps if g < 0)
    
    # Prefer direction with fewer overlaps
    if h_overlaps < v_overlaps:
        return "row"
    elif v_overlaps < h_overlaps:
        return "column"
    
    # If spreads are significantly different, use that
    if h_spread > v_spread * 1.5:
        return "row"
    elif v_spread > h_spread * 1.5:
        return "column"
    
    # Use gap analysis
    if h_positive_gaps > v_positive_gaps:
        return "row"
    
    return "column"


def infer_flex_wrap(
    children: list[dict[str, Any]],
    container_bbox: dict[str, float] | None = None
) -> bool:
    """
    Infer if flex-wrap should be enabled.
    
    Detects if children are arranged in multiple rows/columns,
    suggesting a wrapped layout.
    
    Args:
        children: List of child nodes with bbox fields.
        container_bbox: Optional container bounding box for reference.
        
    Returns:
        True if wrap behavior is detected.
    """
    if len(children) < 3:
        return False
    
    # Group by approximate y-position
    y_groups: dict[float, int] = {}
    tolerance = 0.05
    
    for child in children:
        bbox = child.get("bbox", {})
        y = float(bbox.get("y", 0))
        
        # Find existing group or create new one
        grouped = False
        for group_y in y_groups:
            if abs(y - group_y) <= tolerance:
                y_groups[group_y] += 1
                grouped = True
                break
        
        if not grouped:
            y_groups[y] = 1
    
    # Multiple rows suggests wrap
    return len(y_groups) > 1


def infer_justify_content(
    children: list[dict[str, Any]],
    container_bbox: dict[str, float],
    direction: Literal["row", "column"]
) -> str:
    """
    Infer justify-content value based on element spacing.
    
    Args:
        children: List of child nodes.
        container_bbox: Container bounding box.
        direction: Flex direction ("row" or "column").
        
    Returns:
        CSS justify-content value: "flex-start", "flex-end", "center", 
        "space-between", "space-around", or "space-evenly".
    """
    if len(children) < 1:
        return "flex-start"
    
    if direction == "row":
        container_start = float(container_bbox.get("x", 0))
        container_size = float(container_bbox.get("width", 1))
        
        # Get children bounds
        children_positions = [
            (float(c.get("bbox", {}).get("x", 0)), 
             float(c.get("bbox", {}).get("width", 0)))
            for c in children
        ]
    else:
        container_start = float(container_bbox.get("y", 0))
        container_size = float(container_bbox.get("height", 1))
        
        children_positions = [
            (float(c.get("bbox", {}).get("y", 0)),
             float(c.get("bbox", {}).get("height", 0)))
            for c in children
        ]
    
    if not children_positions:
        return "flex-start"
    
    first_start = children_positions[0][0]
    last_end = children_positions[-1][0] + children_positions[-1][1]
    
    container_end = container_start + container_size
    
    start_gap = first_start - container_start
    end_gap = container_end - last_end
    
    tolerance = 0.02
    
    # Check for centering
    if abs(start_gap - end_gap) <= tolerance:
        if len(children) > 1:
            # Check for even spacing
            gaps = calculate_horizontal_gaps(children) if direction == "row" else calculate_vertical_gaps(children)
            if gaps and max(gaps) - min(gaps) <= tolerance:
                if abs(start_gap - gaps[0] / 2) <= tolerance:
                    return "space-evenly"
                elif abs(start_gap) <= tolerance:
                    return "space-between"
        return "center"
    
    # Check for end alignment
    if start_gap > end_gap + tolerance:
        return "flex-end"
    
    return "flex-start"


def infer_align_items(
    children: list[dict[str, Any]],
    container_bbox: dict[str, float],
    direction: Literal["row", "column"]
) -> str:
    """
    Infer align-items value based on cross-axis positioning.
    
    Args:
        children: List of child nodes.
        container_bbox: Container bounding box.
        direction: Flex direction.
        
    Returns:
        CSS align-items value: "flex-start", "flex-end", "center", or "stretch".
    """
    if len(children) < 1:
        return "flex-start"
    
    # Cross axis is perpendicular to direction
    if direction == "row":
        container_start = float(container_bbox.get("y", 0))
        container_size = float(container_bbox.get("height", 1))
        
        children_positions = [
            (float(c.get("bbox", {}).get("y", 0)),
             float(c.get("bbox", {}).get("height", 0)))
            for c in children
        ]
    else:
        container_start = float(container_bbox.get("x", 0))
        container_size = float(container_bbox.get("width", 1))
        
        children_positions = [
            (float(c.get("bbox", {}).get("x", 0)),
             float(c.get("bbox", {}).get("width", 0)))
            for c in children
        ]
    
    container_end = container_start + container_size
    tolerance = 0.02
    
    # Check if all children stretch to fill container
    all_stretch = all(
        abs(pos[0] - container_start) <= tolerance and
        abs((pos[0] + pos[1]) - container_end) <= tolerance
        for pos in children_positions
    )
    if all_stretch:
        return "stretch"
    
    # Calculate average center position
    centers = [(pos[0] + pos[1] / 2) for pos in children_positions]
    avg_center = sum(centers) / len(centers)
    container_center = container_start + container_size / 2
    
    if abs(avg_center - container_center) <= tolerance:
        return "center"
    
    # Check start/end alignment
    starts = [pos[0] for pos in children_positions]
    if max(starts) - min(starts) <= tolerance:
        if abs(min(starts) - container_start) <= tolerance:
            return "flex-start"
    
    ends = [pos[0] + pos[1] for pos in children_positions]
    if max(ends) - min(ends) <= tolerance:
        if abs(max(ends) - container_end) <= tolerance:
            return "flex-end"
    
    return "flex-start"
