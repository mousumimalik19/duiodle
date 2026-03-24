"""
Duiodle Schema Definitions

This module defines the editable UI tree schema for non-technical users.
All schemas are designed to be human-readable and editable without
requiring knowledge of HTML, CSS, or any programming language.

The component tree structure allows visual editing tools to manipulate
layout, theme, and motion properties through simple JSON modifications.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# =============================================================================
# ENUMERATIONS
# =============================================================================


class ComponentType(str, Enum):
    """Supported UI component types detected from sketches."""
    
    # Layout containers
    CONTAINER = "container"
    ROW = "row"
    COLUMN = "column"
    GRID = "grid"
    STACK = "stack"
    SPACER = "spacer"
    
    # Interactive elements
    BUTTON = "button"
    INPUT = "input"
    TEXTAREA = "textarea"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    TOGGLE = "toggle"
    SLIDER = "slider"
    DROPDOWN = "dropdown"
    
    # Content elements
    TEXT = "text"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LABEL = "label"
    LINK = "link"
    
    # Media elements
    IMAGE = "image"
    ICON = "icon"
    AVATAR = "avatar"
    VIDEO = "video"
    
    # Structural elements
    CARD = "card"
    MODAL = "modal"
    NAVBAR = "navbar"
    SIDEBAR = "sidebar"
    FOOTER = "footer"
    DIVIDER = "divider"
    
    # Data display
    TABLE = "table"
    LIST = "list"
    BADGE = "badge"
    PROGRESS = "progress"


class ThemeStyle(str, Enum):
    """Available theme styles for UI generation."""
    
    MINIMAL = "minimal"
    PROFESSIONAL = "professional"
    AESTHETIC = "aesthetic"
    PLAYFUL = "playful"
    ANIMATED = "animated"
    DARK = "dark"
    LIGHT = "light"


class FlexDirection(str, Enum):
    """Flexbox direction options."""
    
    ROW = "row"
    COLUMN = "column"
    ROW_REVERSE = "row-reverse"
    COLUMN_REVERSE = "column-reverse"


class FlexJustify(str, Enum):
    """Flexbox justify-content options."""
    
    START = "start"
    END = "end"
    CENTER = "center"
    BETWEEN = "space-between"
    AROUND = "space-around"
    EVENLY = "space-evenly"


class FlexAlign(str, Enum):
    """Flexbox align-items options."""
    
    START = "start"
    END = "end"
    CENTER = "center"
    STRETCH = "stretch"
    BASELINE = "baseline"


class TextAlign(str, Enum):
    """Text alignment options."""
    
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


class FontWeight(str, Enum):
    """Font weight options."""
    
    THIN = "thin"
    LIGHT = "light"
    NORMAL = "normal"
    MEDIUM = "medium"
    SEMIBOLD = "semibold"
    BOLD = "bold"
    EXTRABOLD = "extrabold"


class MotionType(str, Enum):
    """Animation/motion effect types."""
    
    FADE_IN = "fade-in"
    FADE_OUT = "fade-out"
    SLIDE_UP = "slide-up"
    SLIDE_DOWN = "slide-down"
    SLIDE_LEFT = "slide-left"
    SLIDE_RIGHT = "slide-right"
    SCALE_IN = "scale-in"
    SCALE_OUT = "scale-out"
    BOUNCE = "bounce"
    PULSE = "pulse"
    SHAKE = "shake"
    ROTATE = "rotate"
    FLIP = "flip"
    SPRING = "spring"


class MotionTrigger(str, Enum):
    """When to trigger motion effects."""
    
    ON_LOAD = "on-load"
    ON_HOVER = "on-hover"
    ON_CLICK = "on-click"
    ON_SCROLL = "on-scroll"
    ON_FOCUS = "on-focus"
    STAGGERED = "staggered"


class ExportFormat(str, Enum):
    """Available export formats."""
    
    JSON = "json"
    REACT_TAILWIND = "react-tailwind"
    REACT_CSS = "react-css"
    HTML_CSS = "html-css"
    FIGMA = "figma"


# =============================================================================
# BOUNDING BOX & POSITION
# =============================================================================


class BoundingBox(BaseModel):
    """
    Represents the detected bounding box of a component from vision analysis.
    Coordinates are relative to the original sketch dimensions.
    """
    
    x: float = Field(..., description="X coordinate (left edge)")
    y: float = Field(..., description="Y coordinate (top edge)")
    width: float = Field(..., ge=0, description="Width in pixels")
    height: float = Field(..., ge=0, description="Height in pixels")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Detection confidence score (0-1)"
    )


class Spacing(BaseModel):
    """Spacing values for padding and margin."""
    
    top: int = Field(default=0, ge=0, description="Top spacing in pixels")
    right: int = Field(default=0, ge=0, description="Right spacing in pixels")
    bottom: int = Field(default=0, ge=0, description="Bottom spacing in pixels")
    left: int = Field(default=0, ge=0, description="Left spacing in pixels")
    
    @classmethod
    def uniform(cls, value: int) -> "Spacing":
        """Create uniform spacing on all sides."""
        return cls(top=value, right=value, bottom=value, left=value)
    
    @classmethod
    def symmetric(cls, vertical: int, horizontal: int) -> "Spacing":
        """Create symmetric vertical and horizontal spacing."""
        return cls(top=vertical, right=horizontal, bottom=vertical, left=horizontal)


class BorderRadius(BaseModel):
    """Border radius values for rounded corners."""
    
    top_left: int = Field(default=0, ge=0)
    top_right: int = Field(default=0, ge=0)
    bottom_right: int = Field(default=0, ge=0)
    bottom_left: int = Field(default=0, ge=0)
    
    @classmethod
    def uniform(cls, value: int) -> "BorderRadius":
        """Create uniform border radius on all corners."""
        return cls(
            top_left=value,
            top_right=value,
            bottom_right=value,
            bottom_left=value
        )


# =============================================================================
# LAYOUT METADATA
# =============================================================================


class LayoutMetadata(BaseModel):
    """
    Layout properties for a component.
    These are editable by non-technical users through visual controls.
    """
    
    # Flexbox properties
    direction: FlexDirection = Field(
        default=FlexDirection.COLUMN,
        description="Layout direction for child elements"
    )
    justify: FlexJustify = Field(
        default=FlexJustify.START,
        description="How to distribute space along main axis"
    )
    align: FlexAlign = Field(
        default=FlexAlign.STRETCH,
        description="How to align items along cross axis"
    )
    gap: int = Field(
        default=0,
        ge=0,
        description="Space between child elements in pixels"
    )
    wrap: bool = Field(
        default=False,
        description="Whether children should wrap to next line"
    )
    
    # Size constraints
    width: Optional[str] = Field(
        default=None,
        description="Width value (e.g., '100%', '200px', 'auto')"
    )
    height: Optional[str] = Field(
        default=None,
        description="Height value (e.g., '100%', '200px', 'auto')"
    )
    min_width: Optional[str] = Field(default=None)
    max_width: Optional[str] = Field(default=None)
    min_height: Optional[str] = Field(default=None)
    max_height: Optional[str] = Field(default=None)
    
    # Spacing
    padding: Spacing = Field(default_factory=Spacing)
    margin: Spacing = Field(default_factory=Spacing)
    
    # Positioning
    position: str = Field(
        default="relative",
        description="CSS position value"
    )
    z_index: int = Field(default=0, description="Stack order")
    
    # Visibility
    visible: bool = Field(default=True, description="Whether component is visible")
    opacity: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Opacity level (0-1)"
    )


# =============================================================================
# THEME METADATA
# =============================================================================


class ColorValue(BaseModel):
    """
    Color value that can be specified as hex, rgb, or theme token.
    Non-technical users can use color picker or preset colors.
    """
    
    value: str = Field(
        ...,
        description="Color value (hex: '#FF5733', token: 'primary', name: 'red')"
    )
    opacity: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Color opacity (0-1)"
    )


class ThemeTokens(BaseModel):
    """
    Design tokens that define the visual language.
    These are applied globally and can be overridden per-component.
    """
    
    # Color palette
    primary: str = Field(default="#3B82F6", description="Primary brand color")
    secondary: str = Field(default="#6366F1", description="Secondary color")
    accent: str = Field(default="#F59E0B", description="Accent/highlight color")
    background: str = Field(default="#FFFFFF", description="Background color")
    surface: str = Field(default="#F3F4F6", description="Surface/card color")
    text_primary: str = Field(default="#111827", description="Primary text color")
    text_secondary: str = Field(default="#6B7280", description="Secondary text color")
    border: str = Field(default="#E5E7EB", description="Border color")
    error: str = Field(default="#EF4444", description="Error state color")
    success: str = Field(default="#10B981", description="Success state color")
    warning: str = Field(default="#F59E0B", description="Warning state color")
    
    # Typography
    font_family: str = Field(
        default="Inter, system-ui, sans-serif",
        description="Primary font family"
    )
    font_size_base: int = Field(default=16, description="Base font size in pixels")
    line_height: float = Field(default=1.5, description="Base line height")
    
    # Spacing scale (multipliers of base unit)
    spacing_unit: int = Field(default=4, description="Base spacing unit in pixels")
    
    # Border radius
    radius_sm: int = Field(default=4, description="Small border radius")
    radius_md: int = Field(default=8, description="Medium border radius")
    radius_lg: int = Field(default=16, description="Large border radius")
    radius_full: int = Field(default=9999, description="Full/pill border radius")
    
    # Shadows
    shadow_sm: str = Field(
        default="0 1px 2px 0 rgb(0 0 0 / 0.05)",
        description="Small shadow"
    )
    shadow_md: str = Field(
        default="0 4px 6px -1px rgb(0 0 0 / 0.1)",
        description="Medium shadow"
    )
    shadow_lg: str = Field(
        default="0 10px 15px -3px rgb(0 0 0 / 0.1)",
        description="Large shadow"
    )


class ThemeMetadata(BaseModel):
    """
    Theme properties for a component.
    Users can adjust colors, typography, and visual effects visually.
    """
    
    # Style preset
    style: ThemeStyle = Field(
        default=ThemeStyle.MINIMAL,
        description="Theme style preset"
    )
    
    # Colors (override theme tokens)
    background_color: Optional[str] = Field(
        default=None,
        description="Background color override"
    )
    text_color: Optional[str] = Field(
        default=None,
        description="Text color override"
    )
    border_color: Optional[str] = Field(
        default=None,
        description="Border color override"
    )
    
    # Typography
    font_size: Optional[int] = Field(
        default=None,
        description="Font size in pixels"
    )
    font_weight: FontWeight = Field(
        default=FontWeight.NORMAL,
        description="Font weight"
    )
    text_align: TextAlign = Field(
        default=TextAlign.LEFT,
        description="Text alignment"
    )
    
    # Border
    border_width: int = Field(default=0, ge=0, description="Border width in pixels")
    border_radius: BorderRadius = Field(default_factory=BorderRadius)
    
    # Effects
    shadow: Optional[str] = Field(
        default=None,
        description="Box shadow value or token (sm, md, lg)"
    )
    blur: int = Field(default=0, ge=0, description="Backdrop blur in pixels")


# =============================================================================
# MOTION METADATA
# =============================================================================


class MotionMetadata(BaseModel):
    """
    Animation and motion properties for a component.
    Users can add delightful animations without writing code.
    """
    
    enabled: bool = Field(
        default=False,
        description="Whether motion effects are enabled"
    )
    
    # Animation type
    type: MotionType = Field(
        default=MotionType.FADE_IN,
        description="Type of animation effect"
    )
    trigger: MotionTrigger = Field(
        default=MotionTrigger.ON_LOAD,
        description="When to trigger the animation"
    )
    
    # Timing
    duration: float = Field(
        default=0.3,
        ge=0,
        le=10,
        description="Animation duration in seconds"
    )
    delay: float = Field(
        default=0,
        ge=0,
        le=10,
        description="Delay before animation starts in seconds"
    )
    
    # Physics-based animation (for spring animations)
    stiffness: float = Field(
        default=100,
        ge=0,
        description="Spring stiffness (higher = snappier)"
    )
    damping: float = Field(
        default=10,
        ge=0,
        description="Spring damping (higher = less bounce)"
    )
    mass: float = Field(
        default=1,
        ge=0,
        description="Spring mass (higher = more momentum)"
    )
    
    # Easing (for non-spring animations)
    easing: str = Field(
        default="ease-out",
        description="Easing function (ease, ease-in, ease-out, ease-in-out, linear)"
    )
    
    # Stagger settings (for parent containers)
    stagger_children: bool = Field(
        default=False,
        description="Stagger animations of child elements"
    )
    stagger_delay: float = Field(
        default=0.1,
        ge=0,
        description="Delay between each child animation"
    )
    
    # Loop
    loop: bool = Field(default=False, description="Whether animation should loop")
    loop_count: int = Field(
        default=-1,
        description="Number of loops (-1 for infinite)"
    )


# =============================================================================
# IMAGE PLACEHOLDER
# =============================================================================


class ImagePlaceholder(BaseModel):
    """
    Image placeholder for detected image regions.
    Users can replace placeholders with actual images through upload.
    """
    
    id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for the image slot"
    )
    placeholder_url: Optional[str] = Field(
        default=None,
        description="URL of placeholder image"
    )
    uploaded_url: Optional[str] = Field(
        default=None,
        description="URL of user-uploaded image"
    )
    alt_text: str = Field(
        default="",
        description="Accessible alt text for the image"
    )
    
    # Image fitting
    object_fit: str = Field(
        default="cover",
        description="How image should fit (cover, contain, fill, none)"
    )
    object_position: str = Field(
        default="center",
        description="Position of image within container"
    )
    
    # Detected properties
    aspect_ratio: Optional[str] = Field(
        default=None,
        description="Aspect ratio (e.g., '16:9', '1:1')"
    )
    suggested_dimensions: Optional[tuple[int, int]] = Field(
        default=None,
        description="Suggested width and height in pixels"
    )
    
    @property
    def display_url(self) -> Optional[str]:
        """Return the URL to display (uploaded takes precedence)."""
        return self.uploaded_url or self.placeholder_url


# =============================================================================
# COMPONENT NODE
# =============================================================================


class ComponentNode(BaseModel):
    """
    A single node in the UI component tree.
    
    This is the core building block of the editable UI structure.
    Each node represents a visual element that can be:
    - Moved, resized, or deleted
    - Styled through theme properties
    - Animated through motion properties
    - Connected to data or images
    
    The tree structure allows nested layouts while keeping
    the data format simple and editable.
    """
    
    # Identity
    id: UUID = Field(
        default_factory=uuid4,
        description="Unique component identifier"
    )
    type: ComponentType = Field(
        ...,
        description="Type of UI component"
    )
    name: str = Field(
        default="",
        description="User-friendly name for the component"
    )
    
    # Content
    content: Optional[str] = Field(
        default=None,
        description="Text content (for text-based components)"
    )
    placeholder: Optional[str] = Field(
        default=None,
        description="Placeholder text (for inputs)"
    )
    
    # Bounding box from vision detection
    bounding_box: Optional[BoundingBox] = Field(
        default=None,
        description="Detected position and size from sketch"
    )
    
    # Metadata
    layout: LayoutMetadata = Field(
        default_factory=LayoutMetadata,
        description="Layout and positioning properties"
    )
    theme: ThemeMetadata = Field(
        default_factory=ThemeMetadata,
        description="Visual styling properties"
    )
    motion: MotionMetadata = Field(
        default_factory=MotionMetadata,
        description="Animation and motion properties"
    )
    
    # Image (for image-type components)
    image: Optional[ImagePlaceholder] = Field(
        default=None,
        description="Image placeholder for image components"
    )
    
    # Children (nested components)
    children: list["ComponentNode"] = Field(
        default_factory=list,
        description="Nested child components"
    )
    
    # Interaction hints
    interactive: bool = Field(
        default=False,
        description="Whether component responds to user interaction"
    )
    disabled: bool = Field(
        default=False,
        description="Whether component is disabled"
    )
    
    # Custom properties (for extensibility)
    custom_props: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom properties"
    )
    
    # AI metadata (hidden from user, used internally)
    detection_confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="AI confidence in component detection"
    )
    classification_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Classification confidence per type"
    )


# Enable self-referential model
ComponentNode.model_rebuild()


# =============================================================================
# UI TREE (ROOT DOCUMENT)
# =============================================================================


class UITree(BaseModel):
    """
    The complete UI tree document.
    
    This is the top-level structure returned by the analysis pipeline.
    It contains:
    - The root component tree
    - Global theme tokens
    - Document metadata
    - Export settings
    """
    
    # Document identity
    id: UUID = Field(
        default_factory=uuid4,
        description="Unique document identifier"
    )
    name: str = Field(
        default="Untitled Design",
        description="Document name"
    )
    version: str = Field(
        default="1.0.0",
        description="Schema version"
    )
    
    # Canvas dimensions (from original sketch)
    canvas_width: int = Field(
        default=1440,
        ge=1,
        description="Canvas width in pixels"
    )
    canvas_height: int = Field(
        default=900,
        ge=1,
        description="Canvas height in pixels"
    )
    
    # Global theme
    theme_tokens: ThemeTokens = Field(
        default_factory=ThemeTokens,
        description="Global design tokens"
    )
    theme_style: ThemeStyle = Field(
        default=ThemeStyle.MINIMAL,
        description="Applied theme style"
    )
    
    # Component tree
    root: ComponentNode = Field(
        ...,
        description="Root component containing the full UI tree"
    )
    
    # Metadata
    created_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp of creation"
    )
    updated_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp of last update"
    )
    source_image_url: Optional[str] = Field(
        default=None,
        description="URL of the original sketch image"
    )
    
    # Processing info (for debugging, hidden from users)
    processing_time_ms: Optional[int] = Field(
        default=None,
        description="Total processing time in milliseconds"
    )
    pipeline_version: str = Field(
        default="1.0.0",
        description="Version of the processing pipeline"
    )


# =============================================================================
# API REQUEST/RESPONSE MODELS
# =============================================================================


class AnalyzeRequest(BaseModel):
    """Request model for sketch analysis endpoint."""
    
    image_base64: Optional[str] = Field(
        default=None,
        description="Base64-encoded sketch image"
    )
    image_url: Optional[str] = Field(
        default=None,
        description="URL of sketch image to analyze"
    )
    theme_style: ThemeStyle = Field(
        default=ThemeStyle.MINIMAL,
        description="Theme style to apply"
    )
    enable_motion: bool = Field(
        default=False,
        description="Whether to inject motion metadata"
    )
    motion_intensity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Motion intensity level (0-1)"
    )


class AnalyzeResponse(BaseModel):
    """Response model for sketch analysis endpoint."""
    
    success: bool = Field(..., description="Whether analysis succeeded")
    ui_tree: Optional[UITree] = Field(
        default=None,
        description="Generated UI tree (if successful)"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message (if failed)"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal warnings during processing"
    )


class ExportRequest(BaseModel):
    """Request model for code export endpoint."""
    
    ui_tree: UITree = Field(..., description="UI tree to export")
    format: ExportFormat = Field(
        default=ExportFormat.REACT_TAILWIND,
        description="Export format"
    )
    include_motion: bool = Field(
        default=True,
        description="Whether to include motion code"
    )
    component_name: str = Field(
        default="GeneratedUI",
        description="Name of the root component"
    )


class ExportResponse(BaseModel):
    """Response model for code export endpoint."""
    
    success: bool = Field(..., description="Whether export succeeded")
    code: Optional[str] = Field(
        default=None,
        description="Generated code (if successful)"
    )
    files: dict[str, str] = Field(
        default_factory=dict,
        description="Map of filename to code content"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message (if failed)"
    )


class UpdateNodeRequest(BaseModel):
    """Request model for updating a single node."""
    
    node_id: UUID = Field(..., description="ID of node to update")
    updates: dict[str, Any] = Field(
        ...,
        description="Partial updates to apply"
    )


class WebSocketMessage(BaseModel):
    """WebSocket message format for live updates."""
    
    type: str = Field(
        ...,
        description="Message type (analyze, update, export, error)"
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Message payload"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Request ID for tracking"
    )


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def create_empty_container(
    name: str = "Container",
    width: str = "100%",
    height: str = "auto"
) -> ComponentNode:
    """Create an empty container node."""
    return ComponentNode(
        type=ComponentType.CONTAINER,
        name=name,
        layout=LayoutMetadata(
            width=width,
            height=height,
            direction=FlexDirection.COLUMN
        )
    )


def create_text_node(
    content: str,
    component_type: ComponentType = ComponentType.TEXT
) -> ComponentNode:
    """Create a text node with content."""
    return ComponentNode(
        type=component_type,
        name=f"{component_type.value.title()}",
        content=content
    )


def create_image_node(
    placeholder_url: Optional[str] = None,
    alt_text: str = "Image"
) -> ComponentNode:
    """Create an image node with placeholder."""
    return ComponentNode(
        type=ComponentType.IMAGE,
        name="Image",
        image=ImagePlaceholder(
            placeholder_url=placeholder_url,
            alt_text=alt_text
        )
    )
