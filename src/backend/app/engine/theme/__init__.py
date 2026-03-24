"""
Theme Engine Module

Provides design token management, theme application, and
Tailwind CSS class mapping for the Duiodle UI generation pipeline.

This module is responsible for:
- Defining and managing design tokens (colors, typography, spacing)
- Applying themes to layout trees
- Mapping semantic styles to Tailwind CSS utilities

Components:
- tokens: Theme token definitions and registry
- provider: Theme application to layout trees
- tailwind_mapper: Tailwind CSS class generation

Example:
    >>> from app.engine.theme import ThemeProvider, TailwindMapper
    >>> 
    >>> # Apply theme to layout tree
    >>> provider = ThemeProvider()
    >>> styled_tree = provider.apply_theme(layout_tree, "professional")
    >>> 
    >>> # Get Tailwind classes for a node
    >>> mapper = TailwindMapper("professional")
    >>> classes = mapper.map_node_to_classes({"type": "button"})
"""

from .tokens import (
    # Enums
    ThemeName,
    ShadowStyle,
    BorderRadiusStyle,
    # Dataclasses
    ColorPalette,
    Typography,
    Spacing,
    ThemeTokens,
    # Predefined themes
    THEME_MINIMAL,
    THEME_PROFESSIONAL,
    THEME_AESTHETIC,
    THEME_PLAYFUL,
    THEME_PORTFOLIO,
    THEME_TROPICAL,
    THEME_GRADIENT,
    THEME_ANIMATED,
    # Functions
    get_theme_tokens,
    get_available_themes,
    get_all_themes,
    register_theme,
    create_theme_variant,
)

from .provider import (
    # Classes
    StyleContext,
    StyleResult,
    ThemeProvider,
    # Functions
    apply_theme,
    get_component_styles,
)

from .tailwind_mapper import (
    # Classes
    TailwindClassBuilder,
    TailwindMapper,
    # Functions
    map_node_to_classes,
    map_tree_to_classes,
)


__all__ = [
    # Enums
    "ThemeName",
    "ShadowStyle",
    "BorderRadiusStyle",
    # Token dataclasses
    "ColorPalette",
    "Typography",
    "Spacing",
    "ThemeTokens",
    # Predefined themes
    "THEME_MINIMAL",
    "THEME_PROFESSIONAL",
    "THEME_AESTHETIC",
    "THEME_PLAYFUL",
    "THEME_PORTFOLIO",
    "THEME_TROPICAL",
    "THEME_GRADIENT",
    "THEME_ANIMATED",
    # Token functions
    "get_theme_tokens",
    "get_available_themes",
    "get_all_themes",
    "register_theme",
    "create_theme_variant",
    # Provider classes
    "StyleContext",
    "StyleResult",
    "ThemeProvider",
    # Provider functions
    "apply_theme",
    "get_component_styles",
    # Mapper classes
    "TailwindClassBuilder",
    "TailwindMapper",
    # Mapper functions
    "map_node_to_classes",
    "map_tree_to_classes",
]
