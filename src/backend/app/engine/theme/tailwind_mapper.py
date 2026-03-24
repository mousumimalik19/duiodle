"""
Tailwind CSS Mapper Module

Maps theme tokens and node types to Tailwind CSS utility classes.
This module provides the bridge between semantic design tokens and
concrete Tailwind class strings for code generation.

The mapper does NOT generate React code - it only produces
Tailwind class strings that can be used by code generators.
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from .tokens import (
    ThemeTokens,
    get_theme_tokens,
    ShadowStyle,
    BorderRadiusStyle,
)


class TailwindColorMap(Enum):
    """
    Mapping of hex colors to Tailwind color classes.
    
    This provides common color mappings. For custom colors,
    arbitrary value syntax [#xxx] is used.
    """
    # Neutrals
    WHITE = ("#FFFFFF", "white")
    BLACK = ("#000000", "black")
    
    # Grays
    SLATE_50 = ("#F8FAFC", "slate-50")
    SLATE_100 = ("#F1F5F9", "slate-100")
    SLATE_200 = ("#E2E8F0", "slate-200")
    SLATE_500 = ("#64748B", "slate-500")
    SLATE_700 = ("#334155", "slate-700")
    SLATE_900 = ("#0F172A", "slate-900")
    
    NEUTRAL_50 = ("#FAFAFA", "neutral-50")
    NEUTRAL_100 = ("#F5F5F5", "neutral-100")
    NEUTRAL_200 = ("#E5E5E5", "neutral-200")
    NEUTRAL_500 = ("#737373", "neutral-500")
    NEUTRAL_700 = ("#404040", "neutral-700")
    NEUTRAL_900 = ("#171717", "neutral-900")
    
    # Blues
    BLUE_500 = ("#3B82F6", "blue-500")
    BLUE_600 = ("#2563EB", "blue-600")
    BLUE_700 = ("#1D4ED8", "blue-700")
    BLUE_800 = ("#1E40AF", "blue-800")
    
    # Purples
    VIOLET_500 = ("#8B5CF6", "violet-500")
    VIOLET_600 = ("#7C3AED", "violet-600")
    PURPLE_500 = ("#A855F7", "purple-500")
    
    # Pinks
    PINK_500 = ("#EC4899", "pink-500")
    FUCHSIA_500 = ("#D946EF", "fuchsia-500")
    
    # Greens
    EMERALD_500 = ("#10B981", "emerald-500")
    TEAL_500 = ("#14B8A6", "teal-500")
    TEAL_600 = ("#0D9488", "teal-600")
    
    # Oranges/Yellows
    ORANGE_500 = ("#F97316", "orange-500")
    AMBER_400 = ("#FBBF24", "amber-400")
    YELLOW_400 = ("#FACC15", "yellow-400")
    
    # Reds
    RED_500 = ("#EF4444", "red-500")


@dataclass
class TailwindClassBuilder:
    """
    Builder for constructing Tailwind class strings.
    
    Provides a fluent interface for building class strings
    with deduplication and ordering.
    """
    _classes: Set[str] = field(default_factory=set)
    
    def add(self, *classes: str) -> "TailwindClassBuilder":
        """Add one or more classes."""
        for cls in classes:
            if cls:
                self._classes.add(cls.strip())
        return self
    
    def add_if(self, condition: bool, *classes: str) -> "TailwindClassBuilder":
        """Add classes conditionally."""
        if condition:
            self.add(*classes)
        return self
    
    def build(self) -> str:
        """Build final class string."""
        # Sort for consistent output
        return " ".join(sorted(self._classes))
    
    def __str__(self) -> str:
        return self.build()


def _hex_to_tailwind_color(hex_color: str, prefix: str = "bg") -> str:
    """
    Convert hex color to Tailwind class.
    
    Args:
        hex_color: Hex color string (e.g., "#FFFFFF")
        prefix: Class prefix (bg, text, border, etc.)
        
    Returns:
        Tailwind color class
    """
    hex_upper = hex_color.upper()
    
    # Check predefined colors
    for color_enum in TailwindColorMap:
        if color_enum.value[0] == hex_upper:
            return f"{prefix}-{color_enum.value[1]}"
    
    # Use arbitrary value for custom colors
    return f"{prefix}-[{hex_color}]"


def _map_shadow_to_tailwind(shadow_style: ShadowStyle) -> str:
    """Map shadow style to Tailwind class."""
    shadow_map = {
        ShadowStyle.NONE: "",
        ShadowStyle.SUBTLE: "shadow-sm",
        ShadowStyle.SOFT: "shadow",
        ShadowStyle.MEDIUM: "shadow-md",
        ShadowStyle.STRONG: "shadow-lg",
        ShadowStyle.GLOW: "shadow-lg",
    }
    return shadow_map.get(shadow_style, "")


def _map_radius_to_tailwind(radius_style: BorderRadiusStyle) -> str:
    """Map border radius style to Tailwind class."""
    radius_map = {
        BorderRadiusStyle.NONE: "rounded-none",
        BorderRadiusStyle.SMALL: "rounded",
        BorderRadiusStyle.MEDIUM: "rounded-lg",
        BorderRadiusStyle.LARGE: "rounded-2xl",
        BorderRadiusStyle.FULL: "rounded-full",
    }
    return radius_map.get(radius_style, "rounded-lg")


def _map_spacing_to_tailwind(spacing_px: int, prefix: str = "p") -> str:
    """
    Map pixel spacing to Tailwind spacing class.
    
    Args:
        spacing_px: Spacing in pixels
        prefix: Class prefix (p, m, gap, etc.)
        
    Returns:
        Tailwind spacing class
    """
    # Tailwind spacing scale (in 0.25rem = 4px increments)
    spacing_scale = {
        0: "0",
        4: "1",
        8: "2",
        12: "3",
        16: "4",
        20: "5",
        24: "6",
        32: "8",
        40: "10",
        48: "12",
        64: "16",
        80: "20",
        96: "24",
    }
    
    # Find closest match
    closest = min(spacing_scale.keys(), key=lambda x: abs(x - spacing_px))
    return f"{prefix}-{spacing_scale[closest]}"


class TailwindMapper:
    """
    Maps theme tokens and node types to Tailwind CSS classes.
    
    This class provides methods to convert semantic design tokens
    and component types into concrete Tailwind utility classes.
    
    Attributes:
        tokens: Active theme tokens
        include_transitions: Whether to include transition classes
        
    Example:
        >>> mapper = TailwindMapper("professional")
        >>> classes = mapper.map_node_to_classes({"type": "button"})
        >>> print(classes)
        'px-4 py-2 rounded bg-blue-800 text-white ...'
    """
    
    def __init__(
        self,
        theme_name: str = "minimal",
        include_transitions: bool = True,
    ) -> None:
        """
        Initialize TailwindMapper.
        
        Args:
            theme_name: Theme to use for mapping
            include_transitions: Whether to include transition classes
        """
        self.tokens = get_theme_tokens(theme_name)
        self.include_transitions = include_transitions
    
    def map_node_to_classes(self, node: Dict[str, Any]) -> str:
        """
        Map a node to Tailwind classes.
        
        Args:
            node: Node dictionary with type and properties
            
        Returns:
            Space-separated Tailwind class string
            
        Example:
            >>> classes = mapper.map_node_to_classes({
            ...     "type": "container",
            ...     "layout": "column"
            ... })
        """
        node_type = node.get("type", "unknown")
        
        # Get type-specific mapper
        mapper_method = getattr(
            self,
            f"_map_{node_type}",
            self._map_default,
        )
        
        return mapper_method(node)
    
    def _map_container(self, node: Dict[str, Any]) -> str:
        """Map container node to Tailwind classes."""
        builder = TailwindClassBuilder()
        layout = node.get("layout", "column")
        
        # Flex layout
        builder.add("flex")
        builder.add("flex-col" if layout == "column" else "flex-row")
        
        # Flex properties
        justify = node.get("justify", "start")
        align = node.get("align", "stretch")
        
        justify_map = {
            "start": "justify-start",
            "center": "justify-center",
            "end": "justify-end",
            "between": "justify-between",
            "around": "justify-around",
            "evenly": "justify-evenly",
        }
        
        align_map = {
            "start": "items-start",
            "center": "items-center",
            "end": "items-end",
            "stretch": "items-stretch",
            "baseline": "items-baseline",
        }
        
        builder.add(justify_map.get(justify, "justify-start"))
        builder.add(align_map.get(align, "items-stretch"))
        
        # Gap
        gap = node.get("gap")
        if gap:
            builder.add(_map_spacing_to_tailwind(int(gap * 4), "gap"))
        else:
            builder.add("gap-4")
        
        # Background
        style = node.get("style", {})
        if style.get("background"):
            builder.add(_hex_to_tailwind_color(style["background"], "bg"))
        
        # Padding
        builder.add("p-4")
        
        # Border radius
        builder.add(_map_radius_to_tailwind(self.tokens.border_radius))
        
        return builder.build()
    
    def _map_card(self, node: Dict[str, Any]) -> str:
        """Map card node to Tailwind classes."""
        builder = TailwindClassBuilder()
        
        # Background and surface
        builder.add(_hex_to_tailwind_color(self.tokens.colors.surface, "bg"))
        
        # Border
        builder.add("border")
        builder.add(_hex_to_tailwind_color(self.tokens.colors.border, "border"))
        
        # Radius and shadow
        builder.add(_map_radius_to_tailwind(self.tokens.border_radius))
        builder.add(_map_shadow_to_tailwind(self.tokens.shadow_style))
        
        # Padding
        builder.add("p-6")
        
        # Overflow
        builder.add("overflow-hidden")
        
        return builder.build()
    
    def _map_button(self, node: Dict[str, Any]) -> str:
        """Map button node to Tailwind classes."""
        builder = TailwindClassBuilder()
        variant = node.get("variant", "primary")
        size = node.get("size", "md")
        
        # Base button styles
        builder.add("inline-flex", "items-center", "justify-center")
        builder.add("font-semibold")
        
        # Size variants
        size_classes = {
            "sm": ["px-3", "py-1.5", "text-sm"],
            "md": ["px-4", "py-2", "text-base"],
            "lg": ["px-6", "py-3", "text-lg"],
        }
        builder.add(*size_classes.get(size, size_classes["md"]))
        
        # Variant styles
        if variant == "primary":
            builder.add(_hex_to_tailwind_color(self.tokens.colors.primary, "bg"))
            builder.add(_hex_to_tailwind_color(self.tokens.colors.text_on_primary, "text"))
            builder.add("hover:opacity-90")
        elif variant == "secondary":
            builder.add(_hex_to_tailwind_color(self.tokens.colors.secondary, "bg"))
            builder.add(_hex_to_tailwind_color(self.tokens.colors.text_on_primary, "text"))
            builder.add("hover:opacity-90")
        elif variant == "outline":
            builder.add("bg-transparent")
            builder.add("border-2")
            builder.add(_hex_to_tailwind_color(self.tokens.colors.primary, "border"))
            builder.add(_hex_to_tailwind_color(self.tokens.colors.primary, "text"))
            builder.add("hover:bg-opacity-10")
        elif variant == "ghost":
            builder.add("bg-transparent")
            builder.add(_hex_to_tailwind_color(self.tokens.colors.text_primary, "text"))
            builder.add("hover:bg-gray-100")
        
        # Border radius
        builder.add(_map_radius_to_tailwind(self.tokens.border_radius))
        
        # Transitions
        if self.include_transitions:
            builder.add("transition-all", "duration-200")
        
        # Focus states
        builder.add("focus:outline-none", "focus:ring-2", "focus:ring-offset-2")
        builder.add(_hex_to_tailwind_color(self.tokens.colors.primary, "focus:ring"))
        
        return builder.build()
    
    def _map_input(self, node: Dict[str, Any]) -> str:
        """Map input node to Tailwind classes."""
        builder = TailwindClassBuilder()
        
        # Base input styles
        builder.add("w-full", "px-4", "py-2")
        
        # Background and text
        builder.add(_hex_to_tailwind_color(self.tokens.colors.background, "bg"))
        builder.add(_hex_to_tailwind_color(self.tokens.colors.text_primary, "text"))
        
        # Border
        builder.add("border")
        builder.add(_hex_to_tailwind_color(self.tokens.colors.border, "border"))
        
        # Radius
        builder.add(_map_radius_to_tailwind(self.tokens.border_radius))
        
        # Placeholder
        builder.add("placeholder:text-gray-400")
        
        # Focus states
        builder.add("focus:outline-none", "focus:ring-2")
        builder.add(_hex_to_tailwind_color(self.tokens.colors.primary, "focus:ring"))
        builder.add("focus:border-transparent")
        
        # Transitions
        if self.include_transitions:
            builder.add("transition-colors", "duration-200")
        
        return builder.build()
    
    def _map_text(self, node: Dict[str, Any]) -> str:
        """Map text node to Tailwind classes."""
        builder = TailwindClassBuilder()
        variant = node.get("variant", "body")
        
        # Typography variants
        variant_classes = {
            "h1": ["text-4xl", "font-bold", "tracking-tight"],
            "h2": ["text-3xl", "font-bold", "tracking-tight"],
            "h3": ["text-2xl", "font-semibold"],
            "h4": ["text-xl", "font-semibold"],
            "h5": ["text-lg", "font-semibold"],
            "h6": ["text-base", "font-semibold"],
            "body": ["text-base"],
            "small": ["text-sm"],
            "caption": ["text-xs", "text-gray-500"],
        }
        
        builder.add(*variant_classes.get(variant, ["text-base"]))
        
        # Text color
        is_heading = variant.startswith("h")
        if is_heading:
            builder.add(_hex_to_tailwind_color(self.tokens.colors.text_primary, "text"))
        else:
            builder.add(_hex_to_tailwind_color(self.tokens.colors.text_secondary, "text"))
        
        # Line height
        builder.add("leading-relaxed" if not is_heading else "leading-tight")
        
        return builder.build()
    
    def _map_heading(self, node: Dict[str, Any]) -> str:
        """Map heading node to Tailwind classes (alias for text)."""
        return self._map_text({**node, "variant": node.get("level", "h2")})
    
    def _map_paragraph(self, node: Dict[str, Any]) -> str:
        """Map paragraph node to Tailwind classes."""
        return self._map_text({**node, "variant": "body"})
    
    def _map_image(self, node: Dict[str, Any]) -> str:
        """Map image node to Tailwind classes."""
        builder = TailwindClassBuilder()
        fit = node.get("fit", "cover")
        
        # Object fit
        fit_map = {
            "cover": "object-cover",
            "contain": "object-contain",
            "fill": "object-fill",
            "none": "object-none",
        }
        builder.add(fit_map.get(fit, "object-cover"))
        
        # Dimensions
        builder.add("w-full", "h-auto")
        
        # Border radius
        builder.add(_map_radius_to_tailwind(self.tokens.border_radius))
        
        return builder.build()
    
    def _map_divider(self, node: Dict[str, Any]) -> str:
        """Map divider node to Tailwind classes."""
        builder = TailwindClassBuilder()
        direction = node.get("direction", "horizontal")
        
        if direction == "horizontal":
            builder.add("w-full", "h-px")
        else:
            builder.add("w-px", "h-full")
        
        builder.add(_hex_to_tailwind_color(self.tokens.colors.border, "bg"))
        builder.add("opacity-50")
        
        return builder.build()
    
    def _map_spacer(self, node: Dict[str, Any]) -> str:
        """Map spacer node to Tailwind classes."""
        builder = TailwindClassBuilder()
        size = node.get("size", 1.0)
        direction = node.get("direction", "vertical")
        
        # Convert size to Tailwind spacing
        spacing_px = int(size * 16)
        
        if direction == "vertical":
            builder.add(_map_spacing_to_tailwind(spacing_px, "h"))
            builder.add("w-full")
        else:
            builder.add(_map_spacing_to_tailwind(spacing_px, "w"))
            builder.add("h-full")
        
        return builder.build()
    
    def _map_icon(self, node: Dict[str, Any]) -> str:
        """Map icon node to Tailwind classes."""
        builder = TailwindClassBuilder()
        size = node.get("size", "md")
        
        size_classes = {
            "sm": ["w-4", "h-4"],
            "md": ["w-6", "h-6"],
            "lg": ["w-8", "h-8"],
            "xl": ["w-12", "h-12"],
        }
        
        builder.add(*size_classes.get(size, size_classes["md"]))
        builder.add(_hex_to_tailwind_color(self.tokens.colors.text_secondary, "text"))
        
        return builder.build()
    
    def _map_badge(self, node: Dict[str, Any]) -> str:
        """Map badge node to Tailwind classes."""
        builder = TailwindClassBuilder()
        variant = node.get("variant", "default")
        
        # Base badge styles
        builder.add("inline-flex", "items-center", "px-2.5", "py-0.5")
        builder.add("text-xs", "font-medium", "rounded-full")
        
        # Variant colors
        variant_classes = {
            "default": [
                _hex_to_tailwind_color(self.tokens.colors.surface, "bg"),
                _hex_to_tailwind_color(self.tokens.colors.text_primary, "text"),
            ],
            "primary": [
                _hex_to_tailwind_color(self.tokens.colors.primary, "bg"),
                _hex_to_tailwind_color(self.tokens.colors.text_on_primary, "text"),
            ],
            "success": ["bg-green-100", "text-green-800"],
            "warning": ["bg-yellow-100", "text-yellow-800"],
            "error": ["bg-red-100", "text-red-800"],
        }
        
        builder.add(*variant_classes.get(variant, variant_classes["default"]))
        
        return builder.build()
    
    def _map_avatar(self, node: Dict[str, Any]) -> str:
        """Map avatar node to Tailwind classes."""
        builder = TailwindClassBuilder()
        size = node.get("size", "md")
        
        size_classes = {
            "sm": ["w-8", "h-8"],
            "md": ["w-12", "h-12"],
            "lg": ["w-16", "h-16"],
            "xl": ["w-24", "h-24"],
        }
        
        builder.add(*size_classes.get(size, size_classes["md"]))
        builder.add("rounded-full", "object-cover")
        builder.add(_hex_to_tailwind_color(self.tokens.colors.surface, "bg"))
        
        return builder.build()
    
    def _map_default(self, node: Dict[str, Any]) -> str:
        """Map unknown node types to basic Tailwind classes."""
        builder = TailwindClassBuilder()
        
        # Add basic text styling
        builder.add(_hex_to_tailwind_color(self.tokens.colors.text_primary, "text"))
        
        return builder.build()
    
    def map_tree_to_classes(
        self,
        tree: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Map an entire tree to Tailwind classes.
        
        Recursively traverses the tree and adds Tailwind classes
        to each node.
        
        Args:
            tree: Layout tree to map
            
        Returns:
            Tree with 'tailwind_classes' added to each node
        """
        from copy import deepcopy
        
        result = deepcopy(tree)
        self._map_tree_recursive(result)
        return result
    
    def _map_tree_recursive(self, node: Dict[str, Any]) -> None:
        """Recursively map tree nodes to Tailwind classes."""
        node["tailwind_classes"] = self.map_node_to_classes(node)
        
        children = node.get("children", [])
        for child in children:
            self._map_tree_recursive(child)
    
    def get_base_styles(self) -> str:
        """
        Get base/root Tailwind classes for the entire document.
        
        Returns:
            Tailwind classes for the root element
        """
        builder = TailwindClassBuilder()
        
        # Background
        builder.add(_hex_to_tailwind_color(self.tokens.colors.background, "bg"))
        
        # Text defaults
        builder.add(_hex_to_tailwind_color(self.tokens.colors.text_primary, "text"))
        
        # Font
        builder.add("font-sans")
        
        # Antialiasing
        builder.add("antialiased")
        
        # Min height
        builder.add("min-h-screen")
        
        return builder.build()
    
    def get_dark_mode_classes(self, node: Dict[str, Any]) -> str:
        """
        Get dark mode variant classes for a node.
        
        Args:
            node: Node to generate dark mode classes for
            
        Returns:
            Dark mode Tailwind classes
        """
        if not self.tokens.is_dark:
            return ""
        
        # For dark themes, we might want to add dark: prefixed classes
        # This is a placeholder for future dark mode support
        return ""


def map_node_to_classes(
    node: Dict[str, Any],
    theme_name: str = "minimal",
) -> str:
    """
    Convenience function to map a node to Tailwind classes.
    
    Args:
        node: Node dictionary
        theme_name: Theme to use
        
    Returns:
        Tailwind class string
    """
    mapper = TailwindMapper(theme_name)
    return mapper.map_node_to_classes(node)


def map_tree_to_classes(
    tree: Dict[str, Any],
    theme_name: str = "minimal",
) -> Dict[str, Any]:
    """
    Convenience function to map an entire tree to Tailwind classes.
    
    Args:
        tree: Layout tree
        theme_name: Theme to use
        
    Returns:
        Tree with Tailwind classes added
    """
    mapper = TailwindMapper(theme_name)
    return mapper.map_tree_to_classes(tree)
