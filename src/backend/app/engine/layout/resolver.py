"""
Layout Resolver Module - Main Orchestrator.

Coordinates the layout engine pipeline to transform raw visual detections
into a structured, hierarchical UI tree with layout metadata.

Pipeline: Normalize → Sort → Nest → Flex Inference → Spacer Injection
"""

from typing import Any
from copy import deepcopy
from dataclasses import dataclass, field

from .reading_order import sort_by_top_left, sort_by_area_descending
from .snapping import normalize_nodes, align_edges, compute_spacing_unit
from .nesting import build_hierarchy, flatten_hierarchy
from .flex_inference import (
    infer_flex_direction,
    infer_flex_wrap,
    infer_justify_content,
    infer_align_items
)
from .spacer_injection import (
    inject_spacers,
    inject_edge_spacers,
    detect_grid_gaps,
    merge_adjacent_spacers,
    DEFAULT_GAP_THRESHOLD
)


@dataclass
class LayoutConfig:
    """
    Configuration for the layout resolution process.
    
    Attributes:
        grid_size: Grid size for coordinate snapping.
        gap_threshold: Minimum gap size for spacer injection.
        enable_spacers: Whether to inject spacer nodes.
        enable_edge_spacers: Whether to add spacers at container edges.
        align_edges: Whether to align nearby edges.
        containment_tolerance: Tolerance for parent-child detection.
        y_tolerance: Tolerance for same-row detection.
    """
    grid_size: float = 0.01
    gap_threshold: float = DEFAULT_GAP_THRESHOLD
    enable_spacers: bool = True
    enable_edge_spacers: bool = False
    align_edges: bool = True
    containment_tolerance: float = 0.01
    y_tolerance: float = 0.02


@dataclass
class LayoutResult:
    """
    Result from layout resolution.
    
    Attributes:
        tree: Hierarchical component tree.
        flat_nodes: Original flat nodes (normalized).
        spacing_unit: Detected spacing unit.
        stats: Processing statistics.
    """
    tree: list[dict[str, Any]]
    flat_nodes: list[dict[str, Any]]
    spacing_unit: float
    stats: dict[str, Any] = field(default_factory=dict)


class LayoutResolver:
    """
    Main orchestrator for the layout engine.
    
    Transforms flat detection nodes into a hierarchical UI tree
    with layout metadata, flex properties, and spacer nodes.
    
    Usage:
        resolver = LayoutResolver()
        result = resolver.resolve(detection_nodes)
        print(result.tree)
    """
    
    def __init__(self, config: LayoutConfig | None = None):
        """
        Initialize the layout resolver.
        
        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or LayoutConfig()
    
    def resolve(
        self,
        nodes: list[dict[str, Any]],
        root_bbox: dict[str, float] | None = None
    ) -> LayoutResult:
        """
        Resolve layout from flat detection nodes.
        
        Pipeline steps:
        1. Normalize bounding boxes (snap to grid)
        2. Align nearby edges
        3. Sort by reading order
        4. Build nesting hierarchy
        5. Infer flex direction for containers
        6. Inject spacers
        7. Compute layout properties
        
        Args:
            nodes: Flat list of detection nodes.
            root_bbox: Optional root container bounding box.
                      Defaults to full canvas (0,0,1,1).
                      
        Returns:
            LayoutResult with hierarchical tree and metadata.
        """
        if not nodes:
            return LayoutResult(
                tree=[],
                flat_nodes=[],
                spacing_unit=self.config.grid_size,
                stats={"total_nodes": 0}
            )
        
        # Default root bbox is full canvas
        if root_bbox is None:
            root_bbox = {"x": 0, "y": 0, "width": 1, "height": 1}
        
        # Step 1: Normalize bounding boxes
        normalized = normalize_nodes(nodes, self.config.grid_size)
        
        # Step 2: Align edges if enabled
        if self.config.align_edges:
            normalized = align_edges(normalized, tolerance=self.config.grid_size * 2)
        
        # Compute spacing unit for later use
        spacing_unit = compute_spacing_unit(normalized, self.config.grid_size)
        
        # Step 3: Sort by reading order
        sorted_nodes = sort_by_top_left(
            normalized,
            y_tolerance=self.config.y_tolerance
        )
        
        # Step 4: Build nesting hierarchy
        tree = build_hierarchy(
            sorted_nodes,
            tolerance=self.config.containment_tolerance
        )
        
        # Step 5 & 6: Process tree recursively
        processed_tree = self._process_tree(tree, root_bbox)
        
        # Collect statistics
        stats = {
            "total_nodes": len(nodes),
            "root_count": len(processed_tree),
            "nesting_depth": self._calculate_depth(processed_tree),
            "spacing_unit": spacing_unit
        }
        
        return LayoutResult(
            tree=processed_tree,
            flat_nodes=sorted_nodes,
            spacing_unit=spacing_unit,
            stats=stats
        )
    
    def _process_tree(
        self,
        nodes: list[dict[str, Any]],
        parent_bbox: dict[str, float]
    ) -> list[dict[str, Any]]:
        """
        Recursively process tree nodes with layout inference.
        
        Args:
            nodes: List of nodes at current level.
            parent_bbox: Parent container bounding box.
            
        Returns:
            Processed nodes with layout metadata.
        """
        result: list[dict[str, Any]] = []
        
        for node in nodes:
            processed = self._process_node(node, parent_bbox)
            result.append(processed)
        
        # Inject spacers between siblings if enabled
        if self.config.enable_spacers and len(result) > 1:
            # Infer direction for this level
            direction = infer_flex_direction(result)
            
            result = inject_spacers(
                result,
                direction=direction,
                gap_threshold=self.config.gap_threshold
            )
            
            result = merge_adjacent_spacers(result)
            
            if self.config.enable_edge_spacers:
                result = inject_edge_spacers(
                    result,
                    parent_bbox,
                    direction=direction,
                    gap_threshold=self.config.gap_threshold
                )
        
        return result
    
    def _process_node(
        self,
        node: dict[str, Any],
        parent_bbox: dict[str, float]
    ) -> dict[str, Any]:
        """
        Process a single node and its children.
        
        Adds layout metadata including flex direction, justify, align.
        
        Args:
            node: Node to process.
            parent_bbox: Parent bounding box for reference.
            
        Returns:
            Processed node with layout metadata.
        """
        processed = deepcopy(node)
        children = processed.get("children", [])
        node_bbox = processed.get("bbox", {"x": 0, "y": 0, "width": 1, "height": 1})
        
        if children:
            # This is a container - infer layout properties
            direction = infer_flex_direction(children)
            wrap = infer_flex_wrap(children, node_bbox)
            justify = infer_justify_content(children, node_bbox, direction)
            align = infer_align_items(children, node_bbox, direction)
            
            # Add layout metadata
            processed["layout"] = {
                "display": "flex",
                "direction": direction,
                "wrap": wrap,
                "justify": justify,
                "align": align
            }
            
            # Check for grid-like gaps
            grid_gaps = detect_grid_gaps(children)
            if grid_gaps["row_gap"] or grid_gaps["column_gap"]:
                processed["layout"]["gap"] = {
                    "row": grid_gaps["row_gap"],
                    "column": grid_gaps["column_gap"]
                }
            
            # Process children recursively
            processed["children"] = self._process_tree(children, node_bbox)
        else:
            # Leaf node - ensure children is empty list
            processed["children"] = []
            processed["layout"] = {
                "display": "block"
            }
        
        # Mark as editable
        processed["editable"] = True
        
        return processed
    
    def _calculate_depth(self, tree: list[dict[str, Any]]) -> int:
        """
        Calculate maximum nesting depth of the tree.
        
        Args:
            tree: Hierarchical tree structure.
            
        Returns:
            Maximum depth (0 for empty, 1 for flat, etc.).
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
    
    def update_config(self, **kwargs: Any) -> None:
        """
        Update configuration parameters.
        
        Args:
            **kwargs: Configuration parameters to update.
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
    
    def resolve_single_container(
        self,
        container: dict[str, Any],
        children: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Resolve layout for a single container with children.
        
        Useful for incremental updates when a container's
        children have changed.
        
        Args:
            container: Container node.
            children: Child nodes.
            
        Returns:
            Processed container with layout metadata.
        """
        container_bbox = container.get("bbox", {"x": 0, "y": 0, "width": 1, "height": 1})
        
        # Normalize children
        normalized_children = normalize_nodes(children, self.config.grid_size)
        
        # Sort by reading order
        sorted_children = sort_by_top_left(
            normalized_children,
            y_tolerance=self.config.y_tolerance
        )
        
        # Create temporary container
        temp_container = deepcopy(container)
        temp_container["children"] = sorted_children
        
        # Process
        processed = self._process_node(temp_container, container_bbox)
        
        return processed


def resolve_layout(
    nodes: list[dict[str, Any]],
    config: LayoutConfig | None = None
) -> LayoutResult:
    """
    Convenience function for one-shot layout resolution.
    
    Args:
        nodes: Flat list of detection nodes.
        config: Optional configuration.
        
    Returns:
        LayoutResult with hierarchical tree.
        
    Example:
        >>> nodes = [
        ...     {"id": "1", "type": "rectangle", "bbox": {...}},
        ...     {"id": "2", "type": "rectangle", "bbox": {...}}
        ... ]
        >>> result = resolve_layout(nodes)
        >>> print(result.tree)
    """
    resolver = LayoutResolver(config)
    return resolver.resolve(nodes)


def to_output_format(result: LayoutResult) -> dict[str, Any]:
    """
    Convert LayoutResult to API output format.
    
    Args:
        result: Layout resolution result.
        
    Returns:
        Dictionary suitable for JSON serialization.
    """
    return {
        "type": "root",
        "layout": {
            "display": "flex",
            "direction": "column"
        },
        "children": result.tree,
        "metadata": {
            "spacing_unit": result.spacing_unit,
            "stats": result.stats
        }
    }
