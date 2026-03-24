"""
Snapping Module for Layout Engine.

Provides coordinate normalization and grid snapping utilities
to reduce floating-point noise and align elements to consistent grids.

This helps produce cleaner, more predictable layout structures.
"""

from typing import Any
import math


def snap_to_grid(value: float, grid_size: float = 0.01) -> float:
    """
    Snap a coordinate value to the nearest grid point.
    
    Reduces floating-point precision issues and aligns values
    to a consistent grid for cleaner layout calculations.
    
    Args:
        value: The coordinate value to snap (expected range 0-1).
        grid_size: The grid spacing. Default 0.01 creates a 100x100 grid.
        
    Returns:
        The value snapped to the nearest grid point.
        
    Example:
        >>> snap_to_grid(0.123456, 0.01)
        0.12
        >>> snap_to_grid(0.127, 0.01)
        0.13
    """
    if grid_size <= 0:
        return value
    
    return round(value / grid_size) * grid_size


def snap_to_grid_floor(value: float, grid_size: float = 0.01) -> float:
    """
    Snap a coordinate value to the grid point below or equal.
    
    Useful for ensuring elements don't exceed their intended bounds.
    
    Args:
        value: The coordinate value to snap.
        grid_size: The grid spacing.
        
    Returns:
        The value snapped down to the nearest grid point.
    """
    if grid_size <= 0:
        return value
    
    return math.floor(value / grid_size) * grid_size


def snap_to_grid_ceil(value: float, grid_size: float = 0.01) -> float:
    """
    Snap a coordinate value to the grid point above or equal.
    
    Useful for ensuring elements meet minimum size requirements.
    
    Args:
        value: The coordinate value to snap.
        grid_size: The grid spacing.
        
    Returns:
        The value snapped up to the nearest grid point.
    """
    if grid_size <= 0:
        return value
    
    return math.ceil(value / grid_size) * grid_size


def normalize_bbox(
    bbox: dict[str, float],
    grid_size: float = 0.01,
    clamp: bool = True
) -> dict[str, float]:
    """
    Normalize a bounding box by snapping coordinates to grid.
    
    Ensures bounding box values are clean, consistent, and
    optionally clamped to valid range [0, 1].
    
    Args:
        bbox: Dictionary with x, y, width, height keys.
        grid_size: Grid spacing for snapping. Set to 0 to disable.
        clamp: If True, clamp values to [0, 1] range.
        
    Returns:
        New dictionary with normalized bounding box values.
        
    Example:
        >>> bbox = {"x": 0.1234, "y": 0.5678, "width": 0.2345, "height": 0.1234}
        >>> normalize_bbox(bbox)
        {'x': 0.12, 'y': 0.57, 'width': 0.23, 'height': 0.12}
    """
    x = float(bbox.get("x", 0))
    y = float(bbox.get("y", 0))
    width = float(bbox.get("width", 0))
    height = float(bbox.get("height", 0))
    
    # Snap to grid
    if grid_size > 0:
        x = snap_to_grid(x, grid_size)
        y = snap_to_grid(y, grid_size)
        width = snap_to_grid(width, grid_size)
        height = snap_to_grid(height, grid_size)
    
    # Clamp to valid range
    if clamp:
        x = max(0.0, min(1.0, x))
        y = max(0.0, min(1.0, y))
        width = max(0.0, min(1.0 - x, width))
        height = max(0.0, min(1.0 - y, height))
    
    return {
        "x": x,
        "y": y,
        "width": width,
        "height": height
    }


def normalize_node(
    node: dict[str, Any],
    grid_size: float = 0.01
) -> dict[str, Any]:
    """
    Normalize a detection node's bounding box in place.
    
    Creates a new node dict with normalized bbox, preserving other fields.
    
    Args:
        node: Detection node with 'bbox' field.
        grid_size: Grid spacing for snapping.
        
    Returns:
        New node dict with normalized bounding box.
    """
    result = dict(node)  # Shallow copy
    
    if "bbox" in node:
        result["bbox"] = normalize_bbox(node["bbox"], grid_size)
    
    return result


def normalize_nodes(
    nodes: list[dict[str, Any]],
    grid_size: float = 0.01
) -> list[dict[str, Any]]:
    """
    Normalize bounding boxes for a list of nodes.
    
    Args:
        nodes: List of detection nodes.
        grid_size: Grid spacing for snapping.
        
    Returns:
        New list with normalized nodes.
    """
    return [normalize_node(node, grid_size) for node in nodes]


def align_edges(
    nodes: list[dict[str, Any]],
    tolerance: float = 0.02
) -> list[dict[str, Any]]:
    """
    Align nearby edges of nodes to create cleaner layouts.
    
    When elements have edges within tolerance of each other,
    snap them to the same value for visual alignment.
    
    Args:
        nodes: List of detection nodes.
        tolerance: Maximum distance for edge snapping.
        
    Returns:
        New list with aligned nodes.
    """
    if len(nodes) < 2:
        return [dict(n) for n in nodes]
    
    # Collect all unique edge positions
    left_edges: list[float] = []
    right_edges: list[float] = []
    top_edges: list[float] = []
    bottom_edges: list[float] = []
    
    for node in nodes:
        bbox = node.get("bbox", {})
        x = float(bbox.get("x", 0))
        y = float(bbox.get("y", 0))
        w = float(bbox.get("width", 0))
        h = float(bbox.get("height", 0))
        
        left_edges.append(x)
        right_edges.append(x + w)
        top_edges.append(y)
        bottom_edges.append(y + h)
    
    def find_snap_target(value: float, edges: list[float]) -> float:
        """Find the closest edge within tolerance to snap to."""
        for edge in edges:
            if abs(value - edge) <= tolerance and edge != value:
                return edge
        return value
    
    # Create aligned copies
    result: list[dict[str, Any]] = []
    
    for i, node in enumerate(nodes):
        new_node = dict(node)
        bbox = node.get("bbox", {})
        x = float(bbox.get("x", 0))
        y = float(bbox.get("y", 0))
        w = float(bbox.get("width", 0))
        h = float(bbox.get("height", 0))
        
        # Try to align left edge
        new_x = find_snap_target(x, left_edges[:i] + left_edges[i+1:])
        
        # Try to align top edge
        new_y = find_snap_target(y, top_edges[:i] + top_edges[i+1:])
        
        new_node["bbox"] = {
            "x": new_x,
            "y": new_y,
            "width": w,
            "height": h
        }
        
        result.append(new_node)
    
    return result


def compute_spacing_unit(
    nodes: list[dict[str, Any]],
    grid_size: float = 0.01
) -> float:
    """
    Analyze nodes to find the most common spacing unit.
    
    Useful for inferring a consistent spacing system from the design.
    
    Args:
        nodes: List of detection nodes.
        grid_size: Minimum spacing resolution.
        
    Returns:
        The most commonly occurring spacing value, or grid_size if none found.
    """
    if len(nodes) < 2:
        return grid_size
    
    gaps: list[float] = []
    
    # Sort by position for gap analysis
    sorted_by_x = sorted(
        nodes,
        key=lambda n: float(n.get("bbox", {}).get("x", 0))
    )
    sorted_by_y = sorted(
        nodes,
        key=lambda n: float(n.get("bbox", {}).get("y", 0))
    )
    
    # Collect horizontal gaps
    for i in range(len(sorted_by_x) - 1):
        bbox1 = sorted_by_x[i].get("bbox", {})
        bbox2 = sorted_by_x[i + 1].get("bbox", {})
        
        right_edge = float(bbox1.get("x", 0)) + float(bbox1.get("width", 0))
        left_edge = float(bbox2.get("x", 0))
        
        gap = left_edge - right_edge
        if gap > grid_size:
            gaps.append(snap_to_grid(gap, grid_size))
    
    # Collect vertical gaps
    for i in range(len(sorted_by_y) - 1):
        bbox1 = sorted_by_y[i].get("bbox", {})
        bbox2 = sorted_by_y[i + 1].get("bbox", {})
        
        bottom_edge = float(bbox1.get("y", 0)) + float(bbox1.get("height", 0))
        top_edge = float(bbox2.get("y", 0))
        
        gap = top_edge - bottom_edge
        if gap > grid_size:
            gaps.append(snap_to_grid(gap, grid_size))
    
    if not gaps:
        return grid_size
    
    # Find most common gap (simple mode)
    gap_counts: dict[float, int] = {}
    for gap in gaps:
        gap_counts[gap] = gap_counts.get(gap, 0) + 1
    
    most_common = max(gap_counts.items(), key=lambda x: x[1])
    return most_common[0]
