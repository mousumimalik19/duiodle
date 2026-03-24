"""
Layout Engine Module.

Transforms raw visual detections into structured, hierarchical UI trees
with layout metadata, flex properties, and spacing information.

Pipeline:
    Vision Detections → Layout Engine → Hierarchical UI Tree
    
Components:
    - reading_order: Sorts elements in natural reading order
    - snapping: Normalizes coordinates to consistent grid
    - nesting: Builds parent-child hierarchy from containment
    - flex_inference: Infers flexbox direction and properties
    - spacer_injection: Adds spacer nodes for explicit gaps
    - resolver: Main orchestrator coordinating all components

Usage:
    from app.engine.layout import LayoutResolver, LayoutConfig
    
    resolver = LayoutResolver()
    result = resolver.resolve(detection_nodes)
    
    # Access the hierarchical tree
    tree = result.tree
    
    # Access statistics
    print(result.stats)
"""

from .reading_order import (
    sort_by_top_left,
    sort_by_center,
    sort_by_area_descending,
    group_by_rows,
    group_by_columns,
    get_bbox_coordinates
)

from .snapping import (
    snap_to_grid,
    snap_to_grid_floor,
    snap_to_grid_ceil,
    normalize_bbox,
    normalize_node,
    normalize_nodes,
    align_edges,
    compute_spacing_unit
)

from .nesting import (
    build_hierarchy,
    flatten_hierarchy,
    find_node_by_id,
    get_parent_chain,
    get_nesting_depth,
    bbox_contains,
    bbox_area
)

from .flex_inference import (
    FlexDirection,
    infer_flex_direction,
    infer_flex_wrap,
    infer_justify_content,
    infer_align_items,
    elements_horizontally_aligned,
    elements_vertically_aligned,
    calculate_horizontal_gaps,
    calculate_vertical_gaps
)

from .spacer_injection import (
    inject_spacers,
    inject_edge_spacers,
    remove_spacers,
    merge_adjacent_spacers,
    detect_grid_gaps,
    create_spacer_node,
    DEFAULT_GAP_THRESHOLD
)

from .resolver import (
    LayoutResolver,
    LayoutConfig,
    LayoutResult,
    resolve_layout,
    to_output_format
)


__all__ = [
    # Reading order
    "sort_by_top_left",
    "sort_by_center",
    "sort_by_area_descending",
    "group_by_rows",
    "group_by_columns",
    "get_bbox_coordinates",
    
    # Snapping
    "snap_to_grid",
    "snap_to_grid_floor",
    "snap_to_grid_ceil",
    "normalize_bbox",
    "normalize_node",
    "normalize_nodes",
    "align_edges",
    "compute_spacing_unit",
    
    # Nesting
    "build_hierarchy",
    "flatten_hierarchy",
    "find_node_by_id",
    "get_parent_chain",
    "get_nesting_depth",
    "bbox_contains",
    "bbox_area",
    
    # Flex inference
    "FlexDirection",
    "infer_flex_direction",
    "infer_flex_wrap",
    "infer_justify_content",
    "infer_align_items",
    "elements_horizontally_aligned",
    "elements_vertically_aligned",
    "calculate_horizontal_gaps",
    "calculate_vertical_gaps",
    
    # Spacer injection
    "inject_spacers",
    "inject_edge_spacers",
    "remove_spacers",
    "merge_adjacent_spacers",
    "detect_grid_gaps",
    "create_spacer_node",
    "DEFAULT_GAP_THRESHOLD",
    
    # Resolver
    "LayoutResolver",
    "LayoutConfig",
    "LayoutResult",
    "resolve_layout",
    "to_output_format",
]
