"""
Theme Tokens Module

Defines design token structures and predefined theme configurations.
Theme tokens encapsulate all visual styling parameters that can be
applied consistently across UI components.

Supported themes:
- minimal: Clean, simple design with subtle shadows
- professional: Corporate, trustworthy appearance
- aesthetic: Soft, modern with rounded corners
- playful: Vibrant colors, bouncy feel
- portfolio: Dark, elegant for showcasing work
- tropical: Warm, vacation-inspired palette
- gradient: Bold gradient-based design
- animated: Designed for motion-heavy interfaces
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from enum import Enum


class ThemeName(str, Enum):
    """Supported theme identifiers."""
    MINIMAL = "minimal"
    PROFESSIONAL = "professional"
    AESTHETIC = "aesthetic"
    PLAYFUL = "playful"
    PORTFOLIO = "portfolio"
    TROPICAL = "tropical"
    GRADIENT = "gradient"
    ANIMATED = "animated"


class ShadowStyle(str, Enum):
    """Shadow intensity levels."""
    NONE = "none"
    SUBTLE = "subtle"
    SOFT = "soft"
    MEDIUM = "medium"
    STRONG = "strong"
    GLOW = "glow"


class BorderRadiusStyle(str, Enum):
    """Border radius presets."""
    NONE = "none"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    FULL = "full"


@dataclass(frozen=True)
class ColorPalette:
    """
    Complete color palette for a theme.
    
    Attributes:
        primary: Main brand/action color
        secondary: Supporting accent color
        background: Page/container background
        surface: Card/elevated surface background
        text_primary: Main text color
        text_secondary: Muted/secondary text
        text_on_primary: Text color when on primary background
        border: Default border color
        success: Success state color
        warning: Warning state color
        error: Error state color
        info: Info state color
    """
    primary: str
    secondary: str
    background: str
    surface: str
    text_primary: str
    text_secondary: str
    text_on_primary: str
    border: str
    success: str = "#10B981"
    warning: str = "#F59E0B"
    error: str = "#EF4444"
    info: str = "#3B82F6"


@dataclass(frozen=True)
class Typography:
    """
    Typography configuration for a theme.
    
    Attributes:
        font_family: Primary font stack
        font_family_heading: Heading font stack (if different)
        font_family_mono: Monospace font stack
        base_size: Base font size in pixels
        line_height: Default line height multiplier
        letter_spacing: Default letter spacing
    """
    font_family: str
    font_family_heading: Optional[str] = None
    font_family_mono: str = "'Fira Code', 'Consolas', monospace"
    base_size: int = 16
    line_height: float = 1.5
    letter_spacing: str = "normal"
    
    @property
    def heading_font(self) -> str:
        """Get heading font, falling back to primary font."""
        return self.font_family_heading or self.font_family


@dataclass(frozen=True)
class Spacing:
    """
    Spacing scale configuration.
    
    Attributes:
        unit: Base spacing unit in pixels
        scale: Multipliers for spacing scale (xs, sm, md, lg, xl, etc.)
    """
    unit: int = 4
    scale: tuple = (0.5, 1, 2, 3, 4, 6, 8, 12, 16, 24, 32)
    
    def get_space(self, index: int) -> int:
        """
        Get spacing value at scale index.
        
        Args:
            index: Scale index (0-based)
            
        Returns:
            Spacing value in pixels
        """
        if 0 <= index < len(self.scale):
            return int(self.unit * self.scale[index])
        return self.unit * 4  # Default to md


@dataclass(frozen=True)
class ThemeTokens:
    """
    Complete theme token configuration.
    
    This dataclass encapsulates all design tokens needed to style
    a UI consistently. It is immutable to ensure theme integrity.
    
    Attributes:
        name: Theme identifier
        display_name: Human-readable theme name
        colors: Color palette
        typography: Typography settings
        spacing: Spacing scale
        border_radius: Border radius style preset
        shadow_style: Shadow intensity preset
        transition_duration: Default animation duration in ms
        is_dark: Whether this is a dark theme
        custom_properties: Additional theme-specific properties
    """
    name: str
    display_name: str
    colors: ColorPalette
    typography: Typography
    spacing: Spacing = field(default_factory=Spacing)
    border_radius: BorderRadiusStyle = BorderRadiusStyle.MEDIUM
    shadow_style: ShadowStyle = ShadowStyle.SOFT
    transition_duration: int = 200
    is_dark: bool = False
    custom_properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tokens to dictionary for serialization."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "colors": asdict(self.colors),
            "typography": {
                "font_family": self.typography.font_family,
                "font_family_heading": self.typography.heading_font,
                "font_family_mono": self.typography.font_family_mono,
                "base_size": self.typography.base_size,
                "line_height": self.typography.line_height,
                "letter_spacing": self.typography.letter_spacing,
            },
            "spacing": {
                "unit": self.spacing.unit,
                "scale": list(self.spacing.scale),
            },
            "border_radius": self.border_radius.value,
            "shadow_style": self.shadow_style.value,
            "transition_duration": self.transition_duration,
            "is_dark": self.is_dark,
            "custom_properties": self.custom_properties,
        }
    
    def get_border_radius_value(self) -> str:
        """Get CSS border-radius value."""
        radius_map = {
            BorderRadiusStyle.NONE: "0px",
            BorderRadiusStyle.SMALL: "4px",
            BorderRadiusStyle.MEDIUM: "8px",
            BorderRadiusStyle.LARGE: "16px",
            BorderRadiusStyle.FULL: "9999px",
        }
        return radius_map.get(self.border_radius, "8px")
    
    def get_shadow_value(self) -> str:
        """Get CSS box-shadow value."""
        shadow_map = {
            ShadowStyle.NONE: "none",
            ShadowStyle.SUBTLE: "0 1px 2px rgba(0,0,0,0.05)",
            ShadowStyle.SOFT: "0 4px 6px -1px rgba(0,0,0,0.1)",
            ShadowStyle.MEDIUM: "0 10px 15px -3px rgba(0,0,0,0.1)",
            ShadowStyle.STRONG: "0 20px 25px -5px rgba(0,0,0,0.15)",
            ShadowStyle.GLOW: f"0 0 20px {self.colors.primary}40",
        }
        return shadow_map.get(self.shadow_style, "none")


# =============================================================================
# PREDEFINED THEMES
# =============================================================================

THEME_MINIMAL = ThemeTokens(
    name="minimal",
    display_name="Minimal",
    colors=ColorPalette(
        primary="#171717",
        secondary="#525252",
        background="#FFFFFF",
        surface="#FAFAFA",
        text_primary="#171717",
        text_secondary="#737373",
        text_on_primary="#FFFFFF",
        border="#E5E5E5",
    ),
    typography=Typography(
        font_family="'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        line_height=1.6,
    ),
    border_radius=BorderRadiusStyle.SMALL,
    shadow_style=ShadowStyle.SUBTLE,
    transition_duration=150,
)

THEME_PROFESSIONAL = ThemeTokens(
    name="professional",
    display_name="Professional",
    colors=ColorPalette(
        primary="#1E40AF",
        secondary="#3B82F6",
        background="#F8FAFC",
        surface="#FFFFFF",
        text_primary="#1E293B",
        text_secondary="#64748B",
        text_on_primary="#FFFFFF",
        border="#CBD5E1",
    ),
    typography=Typography(
        font_family="'Source Sans Pro', 'Segoe UI', sans-serif",
        font_family_heading="'Merriweather', Georgia, serif",
        line_height=1.6,
    ),
    border_radius=BorderRadiusStyle.SMALL,
    shadow_style=ShadowStyle.SOFT,
    transition_duration=200,
)

THEME_AESTHETIC = ThemeTokens(
    name="aesthetic",
    display_name="Aesthetic",
    colors=ColorPalette(
        primary="#8B5CF6",
        secondary="#EC4899",
        background="#FDF4FF",
        surface="#FFFFFF",
        text_primary="#4C1D95",
        text_secondary="#7C3AED",
        text_on_primary="#FFFFFF",
        border="#E9D5FF",
    ),
    typography=Typography(
        font_family="'Poppins', 'Helvetica Neue', sans-serif",
        line_height=1.7,
        letter_spacing="0.01em",
    ),
    border_radius=BorderRadiusStyle.LARGE,
    shadow_style=ShadowStyle.SOFT,
    transition_duration=300,
    custom_properties={
        "gradient_start": "#8B5CF6",
        "gradient_end": "#EC4899",
    },
)

THEME_PLAYFUL = ThemeTokens(
    name="playful",
    display_name="Playful",
    colors=ColorPalette(
        primary="#F97316",
        secondary="#FACC15",
        background="#FFFBEB",
        surface="#FFFFFF",
        text_primary="#292524",
        text_secondary="#78716C",
        text_on_primary="#FFFFFF",
        border="#FED7AA",
    ),
    typography=Typography(
        font_family="'Nunito', 'Comic Sans MS', cursive, sans-serif",
        font_family_heading="'Baloo 2', cursive",
        base_size=17,
        line_height=1.6,
    ),
    spacing=Spacing(unit=5),
    border_radius=BorderRadiusStyle.LARGE,
    shadow_style=ShadowStyle.MEDIUM,
    transition_duration=250,
    custom_properties={
        "bounce_enabled": True,
        "emoji_support": True,
    },
)

THEME_PORTFOLIO = ThemeTokens(
    name="portfolio",
    display_name="Portfolio",
    colors=ColorPalette(
        primary="#F5F5F5",
        secondary="#A3A3A3",
        background="#0A0A0A",
        surface="#171717",
        text_primary="#F5F5F5",
        text_secondary="#A3A3A3",
        text_on_primary="#0A0A0A",
        border="#262626",
    ),
    typography=Typography(
        font_family="'Space Grotesk', 'SF Pro Display', sans-serif",
        font_family_heading="'Playfair Display', Georgia, serif",
        line_height=1.6,
        letter_spacing="0.02em",
    ),
    border_radius=BorderRadiusStyle.NONE,
    shadow_style=ShadowStyle.NONE,
    transition_duration=400,
    is_dark=True,
    custom_properties={
        "accent_highlight": "#FACC15",
    },
)

THEME_TROPICAL = ThemeTokens(
    name="tropical",
    display_name="Tropical",
    colors=ColorPalette(
        primary="#0D9488",
        secondary="#F97316",
        background="#F0FDFA",
        surface="#FFFFFF",
        text_primary="#134E4A",
        text_secondary="#5EEAD4",
        text_on_primary="#FFFFFF",
        border="#99F6E4",
    ),
    typography=Typography(
        font_family="'Quicksand', 'Verdana', sans-serif",
        base_size=16,
        line_height=1.7,
    ),
    border_radius=BorderRadiusStyle.LARGE,
    shadow_style=ShadowStyle.SOFT,
    transition_duration=300,
    custom_properties={
        "accent_warm": "#F97316",
        "accent_cool": "#06B6D4",
    },
)

THEME_GRADIENT = ThemeTokens(
    name="gradient",
    display_name="Gradient",
    colors=ColorPalette(
        primary="#6366F1",
        secondary="#EC4899",
        background="#0F172A",
        surface="#1E293B",
        text_primary="#F8FAFC",
        text_secondary="#94A3B8",
        text_on_primary="#FFFFFF",
        border="#334155",
    ),
    typography=Typography(
        font_family="'DM Sans', 'Helvetica Neue', sans-serif",
        font_family_heading="'Clash Display', sans-serif",
        line_height=1.6,
    ),
    border_radius=BorderRadiusStyle.MEDIUM,
    shadow_style=ShadowStyle.GLOW,
    transition_duration=350,
    is_dark=True,
    custom_properties={
        "gradient_primary": "linear-gradient(135deg, #6366F1, #EC4899)",
        "gradient_secondary": "linear-gradient(135deg, #06B6D4, #10B981)",
        "glass_effect": True,
    },
)

THEME_ANIMATED = ThemeTokens(
    name="animated",
    display_name="Animated",
    colors=ColorPalette(
        primary="#7C3AED",
        secondary="#2DD4BF",
        background="#18181B",
        surface="#27272A",
        text_primary="#FAFAFA",
        text_secondary="#A1A1AA",
        text_on_primary="#FFFFFF",
        border="#3F3F46",
    ),
    typography=Typography(
        font_family="'Outfit', 'SF Pro', sans-serif",
        line_height=1.5,
    ),
    border_radius=BorderRadiusStyle.MEDIUM,
    shadow_style=ShadowStyle.GLOW,
    transition_duration=500,
    is_dark=True,
    custom_properties={
        "motion_enabled": True,
        "stagger_delay": 50,
        "spring_stiffness": 300,
        "spring_damping": 30,
        "hover_scale": 1.02,
    },
)


# =============================================================================
# THEME REGISTRY
# =============================================================================

_THEME_REGISTRY: Dict[str, ThemeTokens] = {
    ThemeName.MINIMAL.value: THEME_MINIMAL,
    ThemeName.PROFESSIONAL.value: THEME_PROFESSIONAL,
    ThemeName.AESTHETIC.value: THEME_AESTHETIC,
    ThemeName.PLAYFUL.value: THEME_PLAYFUL,
    ThemeName.PORTFOLIO.value: THEME_PORTFOLIO,
    ThemeName.TROPICAL.value: THEME_TROPICAL,
    ThemeName.GRADIENT.value: THEME_GRADIENT,
    ThemeName.ANIMATED.value: THEME_ANIMATED,
}


def get_theme_tokens(theme_name: str) -> ThemeTokens:
    """
    Retrieve theme tokens by name.
    
    Args:
        theme_name: Theme identifier (e.g., "minimal", "professional")
        
    Returns:
        ThemeTokens for the requested theme, or minimal as fallback
        
    Example:
        >>> tokens = get_theme_tokens("professional")
        >>> print(tokens.colors.primary)
        '#1E40AF'
    """
    normalized_name = theme_name.lower().strip()
    return _THEME_REGISTRY.get(normalized_name, THEME_MINIMAL)


def get_available_themes() -> List[str]:
    """
    Get list of all available theme names.
    
    Returns:
        List of theme identifiers
    """
    return list(_THEME_REGISTRY.keys())


def get_all_themes() -> Dict[str, ThemeTokens]:
    """
    Get all available themes.
    
    Returns:
        Dictionary mapping theme names to ThemeTokens
    """
    return _THEME_REGISTRY.copy()


def register_theme(tokens: ThemeTokens) -> None:
    """
    Register a custom theme.
    
    Args:
        tokens: ThemeTokens instance to register
        
    Raises:
        ValueError: If theme name is empty
    """
    if not tokens.name:
        raise ValueError("Theme name cannot be empty")
    _THEME_REGISTRY[tokens.name.lower()] = tokens


def create_theme_variant(
    base_theme: str,
    name: str,
    display_name: str,
    **overrides: Any
) -> ThemeTokens:
    """
    Create a theme variant from an existing theme.
    
    Args:
        base_theme: Name of theme to base variant on
        name: New theme identifier
        display_name: Human-readable name
        **overrides: Properties to override
        
    Returns:
        New ThemeTokens instance
        
    Example:
        >>> dark_minimal = create_theme_variant(
        ...     "minimal",
        ...     "dark_minimal",
        ...     "Dark Minimal",
        ...     is_dark=True,
        ...     colors=ColorPalette(...)
        ... )
    """
    base = get_theme_tokens(base_theme)
    
    # Build new token dict
    token_dict = {
        "name": name,
        "display_name": display_name,
        "colors": overrides.get("colors", base.colors),
        "typography": overrides.get("typography", base.typography),
        "spacing": overrides.get("spacing", base.spacing),
        "border_radius": overrides.get("border_radius", base.border_radius),
        "shadow_style": overrides.get("shadow_style", base.shadow_style),
        "transition_duration": overrides.get("transition_duration", base.transition_duration),
        "is_dark": overrides.get("is_dark", base.is_dark),
        "custom_properties": {
            **base.custom_properties,
            **overrides.get("custom_properties", {}),
        },
    }
    
    return ThemeTokens(**token_dict)
