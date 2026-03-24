"""
Nesting Module for Layout Engine.

Detects parent-child relationships between UI elements based on
bounding box containment. Builds a hierarchical tree structure
from flat detection results.
"""

from typing import Any
from copy import deepcopy


def bbox_contains(
    parent_bbox: dict[str, float],
    child_bbox: dict[str, float],
    tolerance: float = 0.01
) -> bool:
    """
    Check if parent bounding box fully contains child bounding box.
    
    A small tolerance is allowed to handle edge cases where child
    edges are very close to parent edges.
    
    Args:
        parent_bbox: Parent bounding box with x, y, width, height.
        child_bbox: Child bounding box with x, y, width, height.
        tolerance: Allowed overflow beyond parent edges.
        
    Returns:
        True if parent contains child (within tolerance).
    """
    parent_x = float(parent_bbox.get("x", 0))
    parent_y = float(parent_bbox.get("y", 0))
    parent_w = float(parent_bbox.get("width", 0))
    parent_h = float(parent_bbox.get("height", 0))
    
    child_x = float(child_bbox.get("x", 0))
    child_y = float(child_bbox.get("y", 0))
    child_w = float(child_bbox.get("width", 0))
    child_h = float(child_bbox.get("height", 0))
    
    # Parent edges
    parent_left = parent_x - tolerance
    parent_right = parent_x + parent_w + tolerance
    parent_top = parent_y - tolerance
    parent_bottom = parent_y + parent_h + tolerance
    
    # Child edges
    child_left = child_x
    child_right = child_x + child_w
    child_top = child_y
    child_bottom = child_y + child_h
    
    return (
        child_left >= parent_left and
        child_right <= parent_right and
        child_top >= parent_top and
        child_bottom <= parent_bottom
    )


def bbox_area(bbox: dict[str, float]) -> float:
    """
    Calculate the area of a bounding box.
    
    Args:
        bbox: Bounding box with width and height.
        
    Returns:
        Area as float.
    """
    return float(bbox.get("width", 0)) * float(bbox.get("height", 0))


def find_smallest_containing_parent(
    node: dict[str, Any],
    potential_parents: list[dict[str, Any]],
    tolerance: float = 0.01
) -> dict[str, Any] | None:
    """
    Find the smallest parent that contains this node.
    
    Among all potential parents that contain the node, returns
    the one with the smallest area (most immediate parent).
    
    Args:
        node: The node to find a parent for.
        potential_parents: List of candidate parent nodes.
        tolerance: Containment tolerance.
        
    Returns:
        The smallest containing parent, or None if no parent found.
    """
    node_bbox = node.get("bbox", {})
    
    containing_parents = [
        p for p in potential_parents
        if p.get("id") != node.get("id") and  # Not self
        bbox_contains(p.get("bbox", {}), node_bbox, tolerance)
    ]
    
    if not containing_parents:
        return None
    
    # Return smallest (most immediate) parent
    return min(containing_parents, key=lambda p: bbox_area(p.get("bbox", {})))


def build_hierarchy(
    nodes: list[dict[str, Any]],
    tolerance: float = 0.01
) -> list[dict[str, Any]]:
    """
    Build a hierarchical tree from flat detection nodes.
    
    Analyzes containment relationships to determine parent-child
    nesting. Returns a list of root nodes, each potentially
    containing nested children.
    
    Args:
        nodes: Flat list of detection nodes with 'id', 'bbox', and other fields.
        tolerance: Containment tolerance for edge cases.
        
    Returns:
        List of root-level nodes with 'children' arrays populated.
        
    Example:
        Input: [
            {"id": "container", "bbox": {"x": 0, "y": 0, "width": 1, "height": 1}},
            {"id": "button", "bbox": {"x": 0.1, "y": 0.1, "width": 0.2, "height": 0.1}}
        ]
        
        Output: [
            {
                "id": "container",
                "bbox": {...},
                "children": [
                    {"id": "button", "bbox": {...}, "children": []}
                ]
            }
        ]
    """
    if not nodes:
        return []
    
    # Create deep copies to avoid mutating input
    node_copies: dict[str, dict[str, Any]] = {}
    for node in nodes:
        node_id = node.get("id", str(id(node)))
        node_copy = deepcopy(node)
        node_copy["id"] = node_id
        node_copy["children"] = []
        node_copies[node_id] = node_copy
    
    # Track which nodes are children (not roots)
    child_ids: set[str] = set()
    
    # Sort by area descending - larger elements are potential parents
    sorted_nodes = sorted(
        node_copies.values(),
        key=lambda n: bbox_area(n.get("bbox", {})),
        reverse=True
    )
    
    # Build parent-child relationships
    for node in sorted_nodes:
        node_id = node["id"]
        potential_parents = [
            n for n in sorted_nodes
            if n["id"] != node_id and n["id"] not in child_ids
        ]
        
        parent = find_smallest_containing_parent(
            node, potential_parents, tolerance
        )
        
        if parent:
            parent["children"].append(node)
            child_ids.add(node_id)
    
    # Return only root nodes (those without parents)
    roots = [
        node for node_id, node in node_copies.items()
        if node_id not in child_ids
    ]
    
    # Sort roots by position for consistent output
    roots.sort(key=lambda n: (
        float(n.get("bbox", {}).get("y", 0)),
        float(n.get("bbox", {}).get("x", 0))
    ))
    
    return roots


def flatten_hierarchy(
    tree: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Flatten a hierarchical tree back to a flat list.
    
    Useful for debugging or when flat representation is needed.
    Children field is removed from output nodes.
    
    Args:
        tree: Hierarchical tree structure.
        
    Returns:
        Flat list of all nodes in tree.
    """
    result: list[dict[str, Any]] = []
    
    def traverse(nodes: list[dict[str, Any]]) -> None:
        for node in nodes:
            flat_node = {k: v for k, v in node.items() if k != "children"}
            result.append(flat_node)
            
            if node.get("children"):
                traverse(node["children"])
    
    traverse(tree)
    return result


def get_nesting_depth(tree: list[dict[str, Any]]) -> int:
    """
    Calculate the maximum nesting depth of a tree.
    
    Args:
        tree: Hierarchical tree structure.
        
    Returns:
        Maximum depth (1 for flat list, higher for nested structures).
    """
    if not tree:
        return 0
    
    def depth(nodes: list[dict[str, Any]]) -> int:
        if not nodes:
            return 0
        
        max_child_depth = 0
        for node in nodes:
            children = node.get("children", [])
            if children:
                child_depth = depth(children)
                max_child_depth = max(max_child_depth, child_depth)
        
        return 1 + max_child_depth
    
    return depth(tree)


def find_node_by_id(
    tree: list[dict[str, Any]],
    node_id: str
) -> dict[str, Any] | None:
    """
    Find a node by ID in the hierarchy.
    
    Args:
        tree: Hierarchical tree structure.
        node_id: ID of the node to find.
        
    Returns:
        The node if found, None otherwise.
    """
    def search(nodes: list[dict[str, Any]]) -> dict[str, Any] | None:
        for node in nodes:
            if node.get("id") == node_id:
                return node
            
            children = node.get("children", [])
            if children:
                found = search(children)
                if found:
                    return found
        
        return None
    
    return search(tree)


def get_parent_chain(
    tree: list[dict[str, Any]],
    node_id: str
) -> list[dict[str, Any]]:
    """
    Get the chain of ancestors for a node.
    
    Args:
        tree: Hierarchical tree structure.
        node_id: ID of the node to find ancestors for.
        
    Returns:
        List of ancestors from root to immediate parent.
    """
    def search(
        nodes: list[dict[str, Any]],
        chain: list[dict[str, Any]]
    ) -> list[dict[str, Any]] | None:
        for node in nodes:
            if node.get("id") == node_id:
                return chain
            
            children = node.get("children", [])
            if children:
                result = search(children, chain + [node])
                if result is not None:
                    return result
        
        return None
    
    result = search(tree, [])
    return result if result else []
