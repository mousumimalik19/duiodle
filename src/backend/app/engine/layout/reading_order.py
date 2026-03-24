"""
Reading Order Module for Layout Engine.

Provides utilities for sorting UI elements in natural reading order,
simulating how a user would scan a page (top-to-bottom, left-to-right).

This module is language-agnostic and assumes left-to-right reading direction.
Future versions may support RTL layouts.
"""

from typing import Any, Callable, List, TypeVar

# Generic type for nodes
T = TypeVar('T')


def get_bbox_coordinates(node: dict[str, Any]) -> tuple[float, float, float, float]:
    """
    Extract bounding box coordinates from a node.
    
    Args:
        node: A detection node with 'bbox' field containing x, y, width, height.
        
    Returns:
        Tuple of (x, y, width, height) coordinates.
        
    Raises:
        KeyError: If bbox or required coordinates are missing.
    """
    bbox = node.get("bbox", {})
    return (
        float(bbox.get("x", 0)),
        float(bbox.get("y", 0)),
        float(bbox.get("width", 0)),
        float(bbox.get("height", 0))
    )


def sort_by_top_left(
    nodes: List[T],
    y_tolerance: float = 0.02,
    bbox_extractor: Callable[[T], dict[str, Any]] | None = None
) -> List[T]:
    """
    Sort nodes in natural reading order (top-to-bottom, left-to-right).
    
    Elements within the same horizontal band (within y_tolerance) are
    sorted left-to-right. Elements in different bands are sorted by
    their vertical position first.
    
    Args:
        nodes: List of detection nodes to sort.
        y_tolerance: Vertical tolerance for considering elements on the same line.
                    Elements with y-coordinates within this tolerance are grouped.
        bbox_extractor: Optional function to extract node dict from custom objects.
                       If None, assumes nodes are dicts with 'bbox' field.
                       
    Returns:
        New list of nodes sorted in reading order.
        
    Example:
        >>> nodes = [
        ...     {"id": "1", "bbox": {"x": 0.5, "y": 0.1, "width": 0.1, "height": 0.1}},
        ...     {"id": "2", "bbox": {"x": 0.1, "y": 0.1, "width": 0.1, "height": 0.1}},
        ...     {"id": "3", "bbox": {"x": 0.1, "y": 0.5, "width": 0.1, "height": 0.1}},
        ... ]
        >>> sorted_nodes = sort_by_top_left(nodes)
        >>> [n["id"] for n in sorted_nodes]
        ['2', '1', '3']
    """
    if not nodes:
        return []
    
    def get_sort_key(node: T) -> tuple[int, float]:
        """Generate sort key: (row_group, x_position)."""
        if bbox_extractor:
            node_dict = bbox_extractor(node)
        else:
            node_dict = node  # type: ignore
            
        x, y, _, _ = get_bbox_coordinates(node_dict)  # type: ignore
        
        # Group by vertical position (row bands)
        row_group = int(y / y_tolerance) if y_tolerance > 0 else int(y * 1000)
        
        return (row_group, x)
    
    return sorted(nodes, key=get_sort_key)


def sort_by_center(
    nodes: List[T],
    y_tolerance: float = 0.02,
    bbox_extractor: Callable[[T], dict[str, Any]] | None = None
) -> List[T]:
    """
    Sort nodes by their center point in reading order.
    
    Similar to sort_by_top_left but uses center coordinates,
    which can be more accurate for elements of varying sizes.
    
    Args:
        nodes: List of detection nodes to sort.
        y_tolerance: Vertical tolerance for same-line grouping.
        bbox_extractor: Optional function to extract node dict from custom objects.
        
    Returns:
        New list of nodes sorted by center position in reading order.
    """
    if not nodes:
        return []
    
    def get_center_sort_key(node: T) -> tuple[int, float]:
        """Generate sort key using center coordinates."""
        if bbox_extractor:
            node_dict = bbox_extractor(node)
        else:
            node_dict = node  # type: ignore
            
        x, y, width, height = get_bbox_coordinates(node_dict)  # type: ignore
        
        center_x = x + width / 2
        center_y = y + height / 2
        
        row_group = int(center_y / y_tolerance) if y_tolerance > 0 else int(center_y * 1000)
        
        return (row_group, center_x)
    
    return sorted(nodes, key=get_center_sort_key)


def sort_by_area_descending(nodes: List[T]) -> List[T]:
    """
    Sort nodes by bounding box area in descending order.
    
    Useful for processing containers before their children,
    as larger elements are likely to be parent containers.
    
    Args:
        nodes: List of detection nodes to sort.
        
    Returns:
        New list of nodes sorted by area (largest first).
    """
    if not nodes:
        return []
    
    def get_area(node: T) -> float:
        """Calculate bounding box area."""
        _, _, width, height = get_bbox_coordinates(node)  # type: ignore
        return width * height
    
    return sorted(nodes, key=get_area, reverse=True)


def group_by_rows(
    nodes: List[T],
    y_tolerance: float = 0.03
) -> List[List[T]]:
    """
    Group nodes into rows based on vertical position.
    
    Elements within y_tolerance of each other vertically are
    considered to be in the same row.
    
    Args:
        nodes: List of detection nodes to group.
        y_tolerance: Vertical tolerance for same-row grouping.
        
    Returns:
        List of rows, where each row is a list of nodes sorted left-to-right.
    """
    if not nodes:
        return []
    
    # Sort by y-coordinate first
    sorted_nodes = sorted(
        nodes,
        key=lambda n: get_bbox_coordinates(n)[1]  # type: ignore
    )
    
    rows: List[List[T]] = []
    current_row: List[T] = []
    current_row_y: float | None = None
    
    for node in sorted_nodes:
        _, y, _, _ = get_bbox_coordinates(node)  # type: ignore
        
        if current_row_y is None:
            # First node
            current_row_y = y
            current_row.append(node)
        elif abs(y - current_row_y) <= y_tolerance:
            # Same row
            current_row.append(node)
        else:
            # New row - save current and start new
            rows.append(sorted(
                current_row,
                key=lambda n: get_bbox_coordinates(n)[0]  # type: ignore
            ))
            current_row = [node]
            current_row_y = y
    
    # Don't forget the last row
    if current_row:
        rows.append(sorted(
            current_row,
            key=lambda n: get_bbox_coordinates(n)[0]  # type: ignore
        ))
    
    return rows


def group_by_columns(
    nodes: List[T],
    x_tolerance: float = 0.03
) -> List[List[T]]:
    """
    Group nodes into columns based on horizontal position.
    
    Elements within x_tolerance of each other horizontally are
    considered to be in the same column.
    
    Args:
        nodes: List of detection nodes to group.
        x_tolerance: Horizontal tolerance for same-column grouping.
        
    Returns:
        List of columns, where each column is a list of nodes sorted top-to-bottom.
    """
    if not nodes:
        return []
    
    # Sort by x-coordinate first
    sorted_nodes = sorted(
        nodes,
        key=lambda n: get_bbox_coordinates(n)[0]  # type: ignore
    )
    
    columns: List[List[T]] = []
    current_column: List[T] = []
    current_column_x: float | None = None
    
    for node in sorted_nodes:
        x, _, _, _ = get_bbox_coordinates(node)  # type: ignore
        
        if current_column_x is None:
            current_column_x = x
            current_column.append(node)
        elif abs(x - current_column_x) <= x_tolerance:
            current_column.append(node)
        else:
            columns.append(sorted(
                current_column,
                key=lambda n: get_bbox_coordinates(n)[1]  # type: ignore
            ))
            current_column = [node]
            current_column_x = x
    
    if current_column:
        columns.append(sorted(
            current_column,
            key=lambda n: get_bbox_coordinates(n)[1]  # type: ignore
        ))
    
    return columns
