"""
Theme Provider Module

Applies theme tokens to layout trees, enriching each node with
style metadata. This module bridges the gap between abstract
design tokens and concrete node styling.

The provider traverses the layout tree recursively and injects
style properties without mutating the original input.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from copy import deepcopy

from .tokens import (
    ThemeTokens,
    get_theme_tokens,
    ShadowStyle,
    BorderRadiusStyle,
)


@dataclass
class StyleContext:
    """
    Context passed during style resolution.
    
    Attributes:
        tokens: Active theme tokens
        parent_type: Parent node type (for contextual styling)
        depth: Nesting depth in tree
        is_first_child: Whether node is first child of parent
        is_last_child: Whether node is last child of parent
        siblings_count: Number of siblings
    """
    tokens: ThemeTokens
    parent_type: Optional[str] = None
    depth: int = 0
    is_first_child: bool = False
    is_last_child: bool = False
    siblings_count: int = 0


@dataclass
class StyleResult:
    """
    Style properties to apply to a node.
    
    Attributes:
        background: Background color
        text: Text color
        border: Border color
        border_width: Border width in pixels
        radius: Border radius value
        shadow: Box shadow value
        padding: Padding value
        font_family: Font family
        font_size: Font size
        font_weight: Font weight
        line_height: Line height
        opacity: Opacity value (0-1)
        custom: Additional custom properties
    """
    background: Optional[str] = None
    text: Optional[str] = None
    border: Optional[str] = None
    border_width: Optional[str] = None
    radius: Optional[str] = None
    shadow: Optional[str] = None
    padding: Optional[str] = None
    font_family: Optional[str] = None
    font_size: Optional[str] = None
    font_weight: Optional[str] = None
    line_height: Optional[str] = None
    opacity: Optional[float] = None
    custom: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = {}
        
        if self.background is not None:
            result["background"] = self.background
        if self.text is not None:
            result["text"] = self.text
        if self.border is not None:
            result["border"] = self.border
        if self.border_width is not None:
            result["border_width"] = self.border_width
        if self.radius is not None:
            result["radius"] = self.radius
        if self.shadow is not None:
            result["shadow"] = self.shadow
        if self.padding is not None:
            result["padding"] = self.padding
        if self.font_family is not None:
            result["font_family"] = self.font_family
        if self.font_size is not None:
            result["font_size"] = self.font_size
        if self.font_weight is not None:
            result["font_weight"] = self.font_weight
        if self.line_height is not None:
            result["line_height"] = self.line_height
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.custom:
            result.update(self.custom)
            
        return result


# Type alias for style resolver functions
StyleResolver = Callable[[Dict[str, Any], StyleContext], StyleResult]


def _get_spacing_value(tokens: ThemeTokens, multiplier: float = 1.0) -> str:
    """Get spacing value from tokens."""
    base = tokens.spacing.unit * 4 * multiplier
    return f"{int(base)}px"


def _resolve_container_style(node: Dict[str, Any], ctx: StyleContext) -> StyleResult:
    """Resolve styles for container nodes."""
    tokens = ctx.tokens
    
    # Root containers get background, nested ones are transparent
    is_root = ctx.depth == 0
    
    return StyleResult(
        background=tokens.colors.background if is_root else tokens.colors.surface,
        text=tokens.colors.text_primary,
        radius=tokens.get_border_radius_value() if ctx.depth > 0 else None,
        padding=_get_spacing_value(tokens, 1.5 if is_root else 1.0),
        shadow=tokens.get_shadow_value() if ctx.depth == 1 else None,
    )


def _resolve_card_style(node: Dict[str, Any], ctx: StyleContext) -> StyleResult:
    """Resolve styles for card nodes."""
    tokens = ctx.tokens
    
    return StyleResult(
        background=tokens.colors.surface,
        text=tokens.colors.text_primary,
        border=tokens.colors.border,
        border_width="1px",
        radius=tokens.get_border_radius_value(),
        shadow=tokens.get_shadow_value(),
        padding=_get_spacing_value(tokens, 1.5),
    )


def _resolve_button_style(node: Dict[str, Any], ctx: StyleContext) -> StyleResult:
    """Resolve styles for button nodes."""
    tokens = ctx.tokens
    
    # Check for button variant
    variant = node.get("variant", "primary")
    
    if variant == "primary":
        bg = tokens.colors.primary
        text = tokens.colors.text_on_primary
    elif variant == "secondary":
        bg = tokens.colors.secondary
        text = tokens.colors.text_on_primary
    elif variant == "outline":
        bg = "transparent"
        text = tokens.colors.primary
    elif variant == "ghost":
        bg = "transparent"
        text = tokens.colors.text_primary
    else:
        bg = tokens.colors.primary
        text = tokens.colors.text_on_primary
    
    return StyleResult(
        background=bg,
        text=text,
        border=tokens.colors.primary if variant == "outline" else None,
        border_width="2px" if variant == "outline" else None,
        radius=tokens.get_border_radius_value(),
        padding=f"{tokens.spacing.unit * 2}px {tokens.spacing.unit * 4}px",
        font_weight="600",
        shadow=tokens.get_shadow_value() if variant == "primary" else None,
        custom={
            "transition": f"all {tokens.transition_duration}ms ease",
        },
    )


def _resolve_input_style(node: Dict[str, Any], ctx: StyleContext) -> StyleResult:
    """Resolve styles for input nodes."""
    tokens = ctx.tokens
    
    return StyleResult(
        background=tokens.colors.background,
        text=tokens.colors.text_primary,
        border=tokens.colors.border,
        border_width="1px",
        radius=tokens.get_border_radius_value(),
        padding=f"{tokens.spacing.unit * 2}px {tokens.spacing.unit * 3}px",
        font_family=tokens.typography.font_family,
        custom={
            "placeholder_color": tokens.colors.text_secondary,
        },
    )


def _resolve_text_style(node: Dict[str, Any], ctx: StyleContext) -> StyleResult:
    """Resolve styles for text nodes."""
    tokens = ctx.tokens
    
    # Check for text variant
    variant = node.get("variant", "body")
    
    size_map = {
        "h1": "2.5rem",
        "h2": "2rem",
        "h3": "1.75rem",
        "h4": "1.5rem",
        "h5": "1.25rem",
        "h6": "1rem",
        "body": "1rem",
        "small": "0.875rem",
        "caption": "0.75rem",
    }
    
    weight_map = {
        "h1": "700",
        "h2": "700",
        "h3": "600",
        "h4": "600",
        "h5": "600",
        "h6": "600",
        "body": "400",
        "small": "400",
        "caption": "400",
    }
    
    is_heading = variant.startswith("h")
    
    return StyleResult(
        text=tokens.colors.text_primary if is_heading else tokens.colors.text_secondary,
        font_family=tokens.typography.heading_font if is_heading else tokens.typography.font_family,
        font_size=size_map.get(variant, "1rem"),
        font_weight=weight_map.get(variant, "400"),
        line_height=str(tokens.typography.line_height),
    )


def _resolve_image_style(node: Dict[str, Any], ctx: StyleContext) -> StyleResult:
    """Resolve styles for image nodes."""
    tokens = ctx.tokens
    
    return StyleResult(
        radius=tokens.get_border_radius_value(),
        custom={
            "object_fit": node.get("fit", "cover"),
        },
    )


def _resolve_divider_style(node: Dict[str, Any], ctx: StyleContext) -> StyleResult:
    """Resolve styles for divider nodes."""
    tokens = ctx.tokens
    
    return StyleResult(
        background=tokens.colors.border,
        opacity=0.5,
    )


def _resolve_spacer_style(node: Dict[str, Any], ctx: StyleContext) -> StyleResult:
    """Resolve styles for spacer nodes."""
    tokens = ctx.tokens
    size = node.get("size", 1.0)
    spacing = int(tokens.spacing.unit * 4 * size)
    
    return StyleResult(
        custom={
            "size": f"{spacing}px",
        },
    )


def _resolve_icon_style(node: Dict[str, Any], ctx: StyleContext) -> StyleResult:
    """Resolve styles for icon nodes."""
    tokens = ctx.tokens
    
    return StyleResult(
        text=tokens.colors.text_secondary,
        custom={
            "size": "24px",
        },
    )


def _resolve_badge_style(node: Dict[str, Any], ctx: StyleContext) -> StyleResult:
    """Resolve styles for badge nodes."""
    tokens = ctx.tokens
    
    variant = node.get("variant", "default")
    
    variant_colors = {
        "default": (tokens.colors.surface, tokens.colors.text_primary),
        "primary": (tokens.colors.primary, tokens.colors.text_on_primary),
        "success": (tokens.colors.success, "#FFFFFF"),
        "warning": (tokens.colors.warning, "#FFFFFF"),
        "error": (tokens.colors.error, "#FFFFFF"),
    }
    
    bg, text = variant_colors.get(variant, variant_colors["default"])
    
    return StyleResult(
        background=bg,
        text=text,
        radius="9999px",
        padding=f"{tokens.spacing.unit}px {tokens.spacing.unit * 2}px",
        font_size="0.75rem",
        font_weight="500",
    )


def _resolve_default_style(node: Dict[str, Any], ctx: StyleContext) -> StyleResult:
    """Resolve default styles for unknown node types."""
    tokens = ctx.tokens
    
    return StyleResult(
        text=tokens.colors.text_primary,
        font_family=tokens.typography.font_family,
    )


# Style resolver registry
_STYLE_RESOLVERS: Dict[str, StyleResolver] = {
    "container": _resolve_container_style,
    "card": _resolve_card_style,
    "button": _resolve_button_style,
    "input": _resolve_input_style,
    "text": _resolve_text_style,
    "heading": _resolve_text_style,
    "paragraph": _resolve_text_style,
    "image": _resolve_image_style,
    "divider": _resolve_divider_style,
    "spacer": _resolve_spacer_style,
    "icon": _resolve_icon_style,
    "badge": _resolve_badge_style,
}


class ThemeProvider:
    """
    Applies theme tokens to layout trees.
    
    The ThemeProvider traverses a layout tree and enriches each node
    with style metadata based on the selected theme. It does not
    mutate the original tree but returns a new enriched copy.
    
    Attributes:
        default_theme: Default theme name to use if none specified
        custom_resolvers: Additional style resolvers for custom node types
        
    Example:
        >>> provider = ThemeProvider()
        >>> styled_tree = provider.apply_theme(layout_tree, "professional")
    """
    
    def __init__(
        self,
        default_theme: str = "minimal",
        custom_resolvers: Optional[Dict[str, StyleResolver]] = None,
    ) -> None:
        """
        Initialize ThemeProvider.
        
        Args:
            default_theme: Default theme name
            custom_resolvers: Additional style resolvers
        """
        self.default_theme = default_theme
        self._resolvers = {**_STYLE_RESOLVERS}
        
        if custom_resolvers:
            self._resolvers.update(custom_resolvers)
    
    def apply_theme(
        self,
        tree: Dict[str, Any],
        theme_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Apply theme to a layout tree.
        
        Recursively traverses the tree and injects style metadata
        into each node based on the theme tokens.
        
        Args:
            tree: Layout tree to style
            theme_name: Theme to apply (uses default if not specified)
            
        Returns:
            New tree with style metadata injected
            
        Example:
            >>> tree = {"type": "container", "children": [...]}
            >>> styled = provider.apply_theme(tree, "aesthetic")
        """
        theme = theme_name or self.default_theme
        tokens = get_theme_tokens(theme)
        
        # Deep copy to avoid mutation
        result = deepcopy(tree)
        
        # Create initial context
        context = StyleContext(
            tokens=tokens,
            depth=0,
        )
        
        # Apply theme recursively
        self._apply_to_node(result, context)
        
        # Inject global theme metadata
        result["_theme"] = {
            "name": tokens.name,
            "display_name": tokens.display_name,
            "is_dark": tokens.is_dark,
            "tokens": tokens.to_dict(),
        }
        
        return result
    
    def _apply_to_node(
        self,
        node: Dict[str, Any],
        context: StyleContext,
    ) -> None:
        """
        Apply theme to a single node and its children.
        
        Args:
            node: Node to style (mutated in place)
            context: Style context
        """
        node_type = node.get("type", "unknown")
        
        # Get style resolver
        resolver = self._resolvers.get(node_type, _resolve_default_style)
        
        # Resolve styles
        style_result = resolver(node, context)
        
        # Inject style metadata
        node["style"] = style_result.to_dict()
        
        # Process children
        children = node.get("children", [])
        if children:
            child_count = len(children)
            
            for i, child in enumerate(children):
                child_context = StyleContext(
                    tokens=context.tokens,
                    parent_type=node_type,
                    depth=context.depth + 1,
                    is_first_child=(i == 0),
                    is_last_child=(i == child_count - 1),
                    siblings_count=child_count,
                )
                self._apply_to_node(child, child_context)
    
    def register_resolver(
        self,
        node_type: str,
        resolver: StyleResolver,
    ) -> None:
        """
        Register a custom style resolver.
        
        Args:
            node_type: Node type to handle
            resolver: Style resolver function
        """
        self._resolvers[node_type] = resolver
    
    def get_theme_preview(
        self,
        theme_name: str,
    ) -> Dict[str, Any]:
        """
        Get a preview of theme tokens.
        
        Args:
            theme_name: Theme to preview
            
        Returns:
            Dictionary of theme properties for preview
        """
        tokens = get_theme_tokens(theme_name)
        
        return {
            "name": tokens.name,
            "display_name": tokens.display_name,
            "is_dark": tokens.is_dark,
            "preview": {
                "primary": tokens.colors.primary,
                "secondary": tokens.colors.secondary,
                "background": tokens.colors.background,
                "surface": tokens.colors.surface,
                "text": tokens.colors.text_primary,
                "radius": tokens.get_border_radius_value(),
                "shadow": tokens.shadow_style.value,
                "font": tokens.typography.font_family,
            },
        }


def apply_theme(
    tree: Dict[str, Any],
    theme_name: str = "minimal",
) -> Dict[str, Any]:
    """
    Convenience function to apply theme to a layout tree.
    
    Args:
        tree: Layout tree to style
        theme_name: Theme to apply
        
    Returns:
        Styled layout tree
        
    Example:
        >>> styled_tree = apply_theme(layout_tree, "professional")
    """
    provider = ThemeProvider()
    return provider.apply_theme(tree, theme_name)


def get_component_styles(
    node_type: str,
    theme_name: str = "minimal",
    **node_props: Any,
) -> Dict[str, Any]:
    """
    Get styles for a specific component type.
    
    Utility function to get styles without a full tree.
    
    Args:
        node_type: Type of component
        theme_name: Theme to use
        **node_props: Additional node properties
        
    Returns:
        Style dictionary for the component
    """
    tokens = get_theme_tokens(theme_name)
    context = StyleContext(tokens=tokens, depth=1)
    
    node = {"type": node_type, **node_props}
    
    resolver = _STYLE_RESOLVERS.get(node_type, _resolve_default_style)
    result = resolver(node, context)
    
    return result.to_dict()
