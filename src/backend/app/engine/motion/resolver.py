"""
Motion Resolver - Animation Metadata Injection Engine.

This module resolves and injects motion metadata into themed layout trees.
It traverses the UI tree and attaches appropriate animation properties
to each eligible node based on component type and configuration.

The motion resolver:
- Does NOT render animations
- Does NOT generate frontend code
- Does NOT modify layout structure
- ONLY attaches motion metadata to nodes

Motion metadata is designed to be framework-agnostic and can be
translated to Framer Motion, CSS animations, GSAP, or other systems.
"""

from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Callable

from .physics import (
    MotionPreset,
    get_motion_preset,
    get_preset_for_component,
    get_available_presets,
    PRESET_NONE,
)


class MotionStrategy(str, Enum):
    """Strategy for applying motion to components."""
    
    NONE = "none"
    UNIFORM = "uniform"
    TYPE_BASED = "type_based"
    DEPTH_BASED = "depth_based"
    STAGGERED = "staggered"
    CUSTOM = "custom"


class StaggerDirection(str, Enum):
    """Direction for staggered animations."""
    
    FORWARD = "forward"
    REVERSE = "reverse"
    CENTER_OUT = "center_out"
    EDGES_IN = "edges_in"


@dataclass
class MotionConfig:
    """
    Configuration for motion resolution.
    
    Attributes:
        enable_motion: Master switch for motion injection.
        default_preset: Fallback preset name if no specific match.
        strategy: How to select presets for components.
        enable_hover: Whether to include hover states.
        enable_tap: Whether to include tap/click states.
        enable_exit: Whether to include exit animations.
        enable_viewport: Whether to enable viewport-triggered animations.
        stagger_delay: Default stagger delay between children.
        max_depth: Maximum tree depth for motion injection (-1 = unlimited).
        excluded_types: Component types to exclude from motion.
        type_preset_map: Custom mapping of component types to presets.
        depth_delay_increment: Additional delay per depth level.
    """
    
    enable_motion: bool = True
    default_preset: str = "fade_in"
    strategy: MotionStrategy = MotionStrategy.TYPE_BASED
    enable_hover: bool = True
    enable_tap: bool = True
    enable_exit: bool = True
    enable_viewport: bool = False
    stagger_delay: float = 0.08
    max_depth: int = -1
    excluded_types: set[str] = field(default_factory=lambda: {"spacer", "divider_spacer"})
    type_preset_map: dict[str, str] = field(default_factory=dict)
    depth_delay_increment: float = 0.05


@dataclass
class MotionContext:
    """
    Context passed during tree traversal.
    
    Attributes:
        depth: Current depth in the tree.
        sibling_index: Index among siblings.
        sibling_count: Total number of siblings.
        parent_type: Type of the parent node.
        parent_layout: Layout direction of parent.
        accumulated_delay: Accumulated delay from staggering.
    """
    
    depth: int = 0
    sibling_index: int = 0
    sibling_count: int = 1
    parent_type: Optional[str] = None
    parent_layout: Optional[str] = None
    accumulated_delay: float = 0.0
    
    def child_context(
        self,
        sibling_index: int = 0,
        sibling_count: int = 1,
        parent_type: Optional[str] = None,
        parent_layout: Optional[str] = None,
    ) -> "MotionContext":
        """Create a child context with incremented depth."""
        return MotionContext(
            depth=self.depth + 1,
            sibling_index=sibling_index,
            sibling_count=sibling_count,
            parent_type=parent_type,
            parent_layout=parent_layout,
            accumulated_delay=self.accumulated_delay,
        )


class MotionResolver:
    """
    Motion metadata injection engine.
    
    This class traverses a themed layout tree and injects appropriate
    animation metadata into each eligible node. It supports multiple
    strategies for selecting animations and can be configured to
    handle various use cases.
    
    Example:
        >>> resolver = MotionResolver(enable_motion=True)
        >>> animated_tree = resolver.apply_motion(tree, preset_name="slide_up")
    """
    
    def __init__(
        self,
        enable_motion: bool = False,
        config: Optional[MotionConfig] = None,
    ) -> None:
        """
        Initialize the motion resolver.
        
        Args:
            enable_motion: Whether to enable motion injection.
            config: Optional configuration object. If not provided,
                    a default config is created with the enable_motion flag.
        """
        if config is not None:
            self._config = config
            self._config.enable_motion = enable_motion
        else:
            self._config = MotionConfig(enable_motion=enable_motion)
        
        self._custom_resolvers: dict[str, Callable[[dict, MotionContext], MotionPreset]] = {}
    
    @property
    def config(self) -> MotionConfig:
        """Get the current configuration."""
        return self._config
    
    @property
    def is_enabled(self) -> bool:
        """Check if motion is enabled."""
        return self._config.enable_motion
    
    def register_resolver(
        self,
        component_type: str,
        resolver: Callable[[dict, MotionContext], MotionPreset],
    ) -> None:
        """
        Register a custom resolver for a component type.
        
        Args:
            component_type: The component type to handle.
            resolver: A callable that takes (node, context) and returns a MotionPreset.
        """
        self._custom_resolvers[component_type] = resolver
    
    def apply_motion(
        self,
        tree: dict[str, Any],
        preset_name: str = "fade_in",
    ) -> dict[str, Any]:
        """
        Apply motion metadata to a layout tree.
        
        This method traverses the tree and injects motion metadata
        into each eligible node. The original tree is NOT mutated.
        
        Args:
            tree: The themed layout tree to process.
            preset_name: Default preset name to use (for UNIFORM strategy).
            
        Returns:
            A new tree with motion metadata injected.
            
        Example:
            >>> tree = {"type": "container", "children": [...]}
            >>> result = resolver.apply_motion(tree, "spring_pop")
        """
        if not self._config.enable_motion:
            return deepcopy(tree)
        
        # Update default preset if provided
        if preset_name != self._config.default_preset:
            self._config.default_preset = preset_name
        
        # Deep copy to avoid mutation
        result = deepcopy(tree)
        
        # Start traversal from root
        context = MotionContext()
        self._traverse_and_inject(result, context)
        
        return result
    
    def _traverse_and_inject(
        self,
        node: dict[str, Any],
        context: MotionContext,
    ) -> None:
        """
        Recursively traverse and inject motion metadata.
        
        Args:
            node: Current node to process.
            context: Current traversal context.
        """
        # Check depth limit
        if self._config.max_depth >= 0 and context.depth > self._config.max_depth:
            return
        
        node_type = node.get("type", "unknown")
        
        # Check if this node type should receive motion
        if self._should_inject_motion(node, context):
            motion_preset = self._resolve_preset(node, context)
            motion_data = self._build_motion_data(motion_preset, node, context)
            node["motion"] = motion_data
        
        # Process children recursively
        children = node.get("children", [])
        if children:
            parent_layout = node.get("layout", node.get("flex_direction", "column"))
            child_count = len(children)
            
            for idx, child in enumerate(children):
                if isinstance(child, dict):
                    child_context = context.child_context(
                        sibling_index=idx,
                        sibling_count=child_count,
                        parent_type=node_type,
                        parent_layout=parent_layout,
                    )
                    
                    # Add stagger delay if using staggered strategy
                    if self._config.strategy == MotionStrategy.STAGGERED:
                        child_context.accumulated_delay = (
                            context.accumulated_delay + 
                            idx * self._config.stagger_delay
                        )
                    
                    self._traverse_and_inject(child, child_context)
    
    def _should_inject_motion(
        self,
        node: dict[str, Any],
        context: MotionContext,
    ) -> bool:
        """
        Determine if a node should receive motion metadata.
        
        Args:
            node: The node to check.
            context: Current traversal context.
            
        Returns:
            True if motion should be injected, False otherwise.
        """
        node_type = node.get("type", "unknown")
        
        # Check exclusion list
        if node_type in self._config.excluded_types:
            return False
        
        # Skip if already has motion
        if "motion" in node and node["motion"]:
            return False
        
        # Skip nodes explicitly marked as no-motion
        if node.get("skip_motion", False):
            return False
        
        # Component types that should receive motion
        motion_eligible_types = {
            "container",
            "card",
            "button",
            "image",
            "text",
            "heading",
            "paragraph",
            "icon",
            "badge",
            "input",
            "input_field",
            "link",
            "nav",
            "header",
            "footer",
            "section",
            "hero",
            "list",
            "list_item",
            "avatar",
            "modal",
            "dropdown",
            "tooltip",
            "alert",
            "progress",
            "tabs",
            "accordion",
        }
        
        return node_type in motion_eligible_types
    
    def _resolve_preset(
        self,
        node: dict[str, Any],
        context: MotionContext,
    ) -> MotionPreset:
        """
        Resolve the appropriate motion preset for a node.
        
        Args:
            node: The node to resolve a preset for.
            context: Current traversal context.
            
        Returns:
            The resolved MotionPreset.
        """
        node_type = node.get("type", "unknown")
        
        # Check for custom resolver first
        if node_type in self._custom_resolvers:
            return self._custom_resolvers[node_type](node, context)
        
        # Check type preset map in config
        if node_type in self._config.type_preset_map:
            preset_name = self._config.type_preset_map[node_type]
            return get_motion_preset(preset_name)
        
        # Apply strategy
        strategy = self._config.strategy
        
        if strategy == MotionStrategy.NONE:
            return PRESET_NONE
        
        elif strategy == MotionStrategy.UNIFORM:
            return get_motion_preset(self._config.default_preset)
        
        elif strategy == MotionStrategy.TYPE_BASED:
            return get_preset_for_component(node_type)
        
        elif strategy == MotionStrategy.DEPTH_BASED:
            return self._resolve_depth_based(node, context)
        
        elif strategy == MotionStrategy.STAGGERED:
            return self._resolve_staggered(node, context)
        
        else:
            return get_motion_preset(self._config.default_preset)
    
    def _resolve_depth_based(
        self,
        node: dict[str, Any],
        context: MotionContext,
    ) -> MotionPreset:
        """
        Resolve preset based on tree depth.
        
        Deeper nodes get simpler, faster animations.
        
        Args:
            node: The node to resolve for.
            context: Current traversal context.
            
        Returns:
            Appropriate MotionPreset for the depth.
        """
        depth = context.depth
        
        if depth == 0:
            return get_motion_preset("fade_in_slow")
        elif depth == 1:
            return get_motion_preset("slide_up")
        elif depth == 2:
            return get_motion_preset("fade_in")
        else:
            return get_motion_preset("fade_in")
    
    def _resolve_staggered(
        self,
        node: dict[str, Any],
        context: MotionContext,
    ) -> MotionPreset:
        """
        Resolve preset for staggered animation.
        
        Args:
            node: The node to resolve for.
            context: Current traversal context.
            
        Returns:
            MotionPreset with appropriate delay.
        """
        base_preset = get_preset_for_component(node.get("type", "unknown"))
        
        if context.accumulated_delay > 0:
            return base_preset.with_delay(context.accumulated_delay)
        
        return base_preset
    
    def _build_motion_data(
        self,
        preset: MotionPreset,
        node: dict[str, Any],
        context: MotionContext,
    ) -> dict[str, Any]:
        """
        Build the final motion data dictionary.
        
        Applies configuration filters and context-specific adjustments.
        
        Args:
            preset: The resolved motion preset.
            node: The node being processed.
            context: Current traversal context.
            
        Returns:
            Motion metadata dictionary ready for injection.
        """
        motion_data = preset.to_dict()
        
        # Apply configuration filters
        if not self._config.enable_hover and "whileHover" in motion_data:
            del motion_data["whileHover"]
        
        if not self._config.enable_tap and "whileTap" in motion_data:
            del motion_data["whileTap"]
        
        if not self._config.enable_exit and "exit" in motion_data:
            del motion_data["exit"]
        
        if not self._config.enable_viewport and "viewport" in motion_data:
            del motion_data["viewport"]
        
        # Add depth-based delay if configured
        if self._config.depth_delay_increment > 0 and context.depth > 0:
            current_delay = motion_data.get("transition", {}).get("delay", 0)
            additional_delay = context.depth * self._config.depth_delay_increment
            motion_data.setdefault("transition", {})["delay"] = current_delay + additional_delay
        
        # Add metadata for debugging/inspection
        motion_data["_preset"] = preset.name
        motion_data["_depth"] = context.depth
        
        return motion_data


def apply_motion_to_tree(
    tree: dict[str, Any],
    preset_name: str = "fade_in",
    enable_motion: bool = True,
    strategy: MotionStrategy = MotionStrategy.TYPE_BASED,
) -> dict[str, Any]:
    """
    Convenience function to apply motion to a tree.
    
    This is a simplified interface for common use cases.
    
    Args:
        tree: The layout tree to process.
        preset_name: Default preset name for uniform strategy.
        enable_motion: Whether to enable motion injection.
        strategy: Motion selection strategy.
        
    Returns:
        Tree with motion metadata injected.
        
    Example:
        >>> result = apply_motion_to_tree(tree, "spring_pop", True)
    """
    config = MotionConfig(
        enable_motion=enable_motion,
        default_preset=preset_name,
        strategy=strategy,
    )
    resolver = MotionResolver(enable_motion=enable_motion, config=config)
    return resolver.apply_motion(tree, preset_name)


def strip_motion_from_tree(tree: dict[str, Any]) -> dict[str, Any]:
    """
    Remove all motion metadata from a tree.
    
    Useful for generating static exports or debugging.
    
    Args:
        tree: The tree to strip motion from.
        
    Returns:
        A new tree with all motion metadata removed.
    """
    result = deepcopy(tree)
    _strip_motion_recursive(result)
    return result


def _strip_motion_recursive(node: dict[str, Any]) -> None:
    """Recursively remove motion from nodes."""
    if "motion" in node:
        del node["motion"]
    
    for child in node.get("children", []):
        if isinstance(child, dict):
            _strip_motion_recursive(child)


def get_motion_summary(tree: dict[str, Any]) -> dict[str, Any]:
    """
    Generate a summary of motion usage in a tree.
    
    Useful for analytics and debugging.
    
    Args:
        tree: The tree to analyze.
        
    Returns:
        Summary dictionary with counts and details.
    """
    summary = {
        "total_nodes": 0,
        "nodes_with_motion": 0,
        "nodes_without_motion": 0,
        "presets_used": {},
        "types_with_motion": {},
    }
    
    _analyze_motion_recursive(tree, summary)
    
    return summary


def _analyze_motion_recursive(
    node: dict[str, Any],
    summary: dict[str, Any],
) -> None:
    """Recursively analyze motion usage."""
    summary["total_nodes"] += 1
    node_type = node.get("type", "unknown")
    
    if "motion" in node:
        summary["nodes_with_motion"] += 1
        
        preset_name = node["motion"].get("_preset", "unknown")
        summary["presets_used"][preset_name] = (
            summary["presets_used"].get(preset_name, 0) + 1
        )
        
        summary["types_with_motion"][node_type] = (
            summary["types_with_motion"].get(node_type, 0) + 1
        )
    else:
        summary["nodes_without_motion"] += 1
    
    for child in node.get("children", []):
        if isinstance(child, dict):
            _analyze_motion_recursive(child, summary)
