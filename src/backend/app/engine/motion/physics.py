"""
Motion Physics Engine - Animation Presets and Physics Definitions.

This module defines motion presets with physics-based animation properties.
Presets are designed to be framework-agnostic and can be translated to
Framer Motion, CSS animations, or other animation systems.

The physics module focuses on:
- Defining reusable motion presets
- Physics-based spring animations
- Easing functions and timing
- Stagger configurations for lists
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from copy import deepcopy


class TransitionType(str, Enum):
    """Animation transition types."""
    
    TWEEN = "tween"
    SPRING = "spring"
    INERTIA = "inertia"
    KEYFRAMES = "keyframes"


class EasingFunction(str, Enum):
    """Common easing functions for tween animations."""
    
    LINEAR = "linear"
    EASE_IN = "easeIn"
    EASE_OUT = "easeOut"
    EASE_IN_OUT = "easeInOut"
    EASE_IN_CUBIC = "easeInCubic"
    EASE_OUT_CUBIC = "easeOutCubic"
    EASE_IN_OUT_CUBIC = "easeInOutCubic"
    EASE_IN_EXPO = "easeInExpo"
    EASE_OUT_EXPO = "easeOutExpo"
    EASE_IN_OUT_EXPO = "easeInOutExpo"
    EASE_IN_BACK = "easeInBack"
    EASE_OUT_BACK = "easeOutBack"
    EASE_IN_OUT_BACK = "easeInOutBack"
    EASE_IN_ELASTIC = "easeInElastic"
    EASE_OUT_ELASTIC = "easeOutElastic"
    ANTICIPATE = "anticipate"


@dataclass(frozen=True)
class SpringConfig:
    """
    Physics-based spring configuration.
    
    Spring animations provide natural, organic motion by simulating
    real-world physics. Adjust stiffness, damping, and mass to
    control the feel of the animation.
    
    Attributes:
        stiffness: Spring stiffness (higher = snappier). Default: 100
        damping: Resistance force (higher = less oscillation). Default: 10
        mass: Virtual mass of the animated object. Default: 1
        velocity: Initial velocity of the animation. Default: 0
        rest_delta: Threshold for considering animation complete. Default: 0.01
        rest_speed: Speed threshold for stopping. Default: 0.01
    """
    
    stiffness: float = 100.0
    damping: float = 10.0
    mass: float = 1.0
    velocity: float = 0.0
    rest_delta: float = 0.01
    rest_speed: float = 0.01
    
    def to_dict(self) -> dict[str, Any]:
        """Convert spring config to dictionary format."""
        return {
            "type": "spring",
            "stiffness": self.stiffness,
            "damping": self.damping,
            "mass": self.mass,
            "velocity": self.velocity,
            "restDelta": self.rest_delta,
            "restSpeed": self.rest_speed,
        }


@dataclass(frozen=True)
class TweenConfig:
    """
    Tween (duration-based) animation configuration.
    
    Tween animations run for a fixed duration with an easing function.
    More predictable than springs but less organic.
    
    Attributes:
        duration: Animation duration in seconds
        ease: Easing function to use
        delay: Delay before animation starts
        repeat: Number of times to repeat (0 = no repeat)
        repeat_type: How to repeat ("loop", "reverse", "mirror")
        repeat_delay: Delay between repetitions
    """
    
    duration: float = 0.3
    ease: EasingFunction = EasingFunction.EASE_OUT
    delay: float = 0.0
    repeat: int = 0
    repeat_type: str = "loop"
    repeat_delay: float = 0.0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert tween config to dictionary format."""
        result = {
            "type": "tween",
            "duration": self.duration,
            "ease": self.ease.value,
        }
        
        if self.delay > 0:
            result["delay"] = self.delay
            
        if self.repeat > 0:
            result["repeat"] = self.repeat
            result["repeatType"] = self.repeat_type
            if self.repeat_delay > 0:
                result["repeatDelay"] = self.repeat_delay
                
        return result


@dataclass(frozen=True)
class StaggerConfig:
    """
    Configuration for staggered animations on child elements.
    
    Stagger creates a cascading effect where each child animates
    with a delay relative to the previous child.
    
    Attributes:
        stagger_children: Delay between each child's animation start
        delay_children: Initial delay before first child animates
        stagger_direction: 1 for forward, -1 for reverse order
        when: "beforeChildren", "afterChildren", or "sync"
    """
    
    stagger_children: float = 0.1
    delay_children: float = 0.0
    stagger_direction: int = 1
    when: str = "beforeChildren"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert stagger config to dictionary format."""
        return {
            "staggerChildren": self.stagger_children,
            "delayChildren": self.delay_children,
            "staggerDirection": self.stagger_direction,
            "when": self.when,
        }


@dataclass
class MotionPreset:
    """
    Complete motion preset definition.
    
    A motion preset defines the complete animation behavior including:
    - Initial state (where animation starts)
    - Animate state (where animation ends)
    - Exit state (optional, for unmount animations)
    - Transition configuration
    - Stagger configuration for containers
    
    Attributes:
        name: Unique identifier for the preset
        description: Human-readable description
        initial: Initial property values
        animate: Target property values
        exit: Exit animation properties (optional)
        transition: Transition configuration dict
        hover: Hover state properties (optional)
        tap: Tap/click state properties (optional)
        focus: Focus state properties (optional)
        stagger: Stagger configuration for children (optional)
        viewport_trigger: Whether to trigger on viewport entry
        viewport_once: Whether to animate only once on viewport entry
        viewport_margin: Margin for viewport detection
    """
    
    name: str
    description: str = ""
    initial: dict[str, Any] = field(default_factory=dict)
    animate: dict[str, Any] = field(default_factory=dict)
    exit: Optional[dict[str, Any]] = None
    transition: dict[str, Any] = field(default_factory=dict)
    hover: Optional[dict[str, Any]] = None
    tap: Optional[dict[str, Any]] = None
    focus: Optional[dict[str, Any]] = None
    stagger: Optional[StaggerConfig] = None
    viewport_trigger: bool = False
    viewport_once: bool = True
    viewport_margin: str = "0px"
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert preset to dictionary format for injection.
        
        Returns:
            Dictionary containing all motion properties.
        """
        result: dict[str, Any] = {
            "initial": deepcopy(self.initial),
            "animate": deepcopy(self.animate),
            "transition": deepcopy(self.transition),
        }
        
        if self.exit is not None:
            result["exit"] = deepcopy(self.exit)
            
        if self.hover is not None:
            result["whileHover"] = deepcopy(self.hover)
            
        if self.tap is not None:
            result["whileTap"] = deepcopy(self.tap)
            
        if self.focus is not None:
            result["whileFocus"] = deepcopy(self.focus)
            
        if self.stagger is not None:
            result["transition"]["staggerChildren"] = self.stagger.stagger_children
            result["transition"]["delayChildren"] = self.stagger.delay_children
            
        if self.viewport_trigger:
            result["viewport"] = {
                "once": self.viewport_once,
                "margin": self.viewport_margin,
            }
            
        return result
    
    def with_delay(self, delay: float) -> "MotionPreset":
        """
        Create a copy of this preset with an added delay.
        
        Args:
            delay: Delay in seconds before animation starts.
            
        Returns:
            New MotionPreset with the delay applied.
        """
        new_transition = deepcopy(self.transition)
        new_transition["delay"] = delay
        
        return MotionPreset(
            name=f"{self.name}_delayed",
            description=f"{self.description} (delayed {delay}s)",
            initial=deepcopy(self.initial),
            animate=deepcopy(self.animate),
            exit=deepcopy(self.exit) if self.exit else None,
            transition=new_transition,
            hover=deepcopy(self.hover) if self.hover else None,
            tap=deepcopy(self.tap) if self.tap else None,
            focus=deepcopy(self.focus) if self.focus else None,
            stagger=self.stagger,
            viewport_trigger=self.viewport_trigger,
            viewport_once=self.viewport_once,
            viewport_margin=self.viewport_margin,
        )
    
    def with_duration(self, duration: float) -> "MotionPreset":
        """
        Create a copy of this preset with a different duration.
        
        Args:
            duration: New duration in seconds.
            
        Returns:
            New MotionPreset with the duration applied.
        """
        new_transition = deepcopy(self.transition)
        new_transition["duration"] = duration
        
        return MotionPreset(
            name=f"{self.name}_duration_{duration}",
            description=f"{self.description} ({duration}s)",
            initial=deepcopy(self.initial),
            animate=deepcopy(self.animate),
            exit=deepcopy(self.exit) if self.exit else None,
            transition=new_transition,
            hover=deepcopy(self.hover) if self.hover else None,
            tap=deepcopy(self.tap) if self.tap else None,
            focus=deepcopy(self.focus) if self.focus else None,
            stagger=self.stagger,
            viewport_trigger=self.viewport_trigger,
            viewport_once=self.viewport_once,
            viewport_margin=self.viewport_margin,
        )


# =============================================================================
# PREDEFINED MOTION PRESETS
# =============================================================================

# Basic Fade Animations
PRESET_FADE_IN = MotionPreset(
    name="fade_in",
    description="Simple fade in animation",
    initial={"opacity": 0},
    animate={"opacity": 1},
    exit={"opacity": 0},
    transition={"duration": 0.3, "ease": "easeOut"},
)

PRESET_FADE_IN_SLOW = MotionPreset(
    name="fade_in_slow",
    description="Slow fade in for dramatic effect",
    initial={"opacity": 0},
    animate={"opacity": 1},
    exit={"opacity": 0},
    transition={"duration": 0.6, "ease": "easeInOut"},
)

# Slide Animations
PRESET_SLIDE_UP = MotionPreset(
    name="slide_up",
    description="Slide up from below with fade",
    initial={"opacity": 0, "y": 20},
    animate={"opacity": 1, "y": 0},
    exit={"opacity": 0, "y": -20},
    transition={"duration": 0.4, "ease": "easeOut"},
)

PRESET_SLIDE_DOWN = MotionPreset(
    name="slide_down",
    description="Slide down from above with fade",
    initial={"opacity": 0, "y": -20},
    animate={"opacity": 1, "y": 0},
    exit={"opacity": 0, "y": 20},
    transition={"duration": 0.4, "ease": "easeOut"},
)

PRESET_SLIDE_LEFT = MotionPreset(
    name="slide_left",
    description="Slide in from the right",
    initial={"opacity": 0, "x": 30},
    animate={"opacity": 1, "x": 0},
    exit={"opacity": 0, "x": -30},
    transition={"duration": 0.4, "ease": "easeOut"},
)

PRESET_SLIDE_RIGHT = MotionPreset(
    name="slide_right",
    description="Slide in from the left",
    initial={"opacity": 0, "x": -30},
    animate={"opacity": 1, "x": 0},
    exit={"opacity": 0, "x": 30},
    transition={"duration": 0.4, "ease": "easeOut"},
)

# Scale Animations
PRESET_SCALE_IN = MotionPreset(
    name="scale_in",
    description="Scale up from smaller size",
    initial={"opacity": 0, "scale": 0.9},
    animate={"opacity": 1, "scale": 1},
    exit={"opacity": 0, "scale": 0.9},
    transition={"duration": 0.3, "ease": "easeOut"},
)

PRESET_SCALE_UP = MotionPreset(
    name="scale_up",
    description="Scale up from tiny",
    initial={"opacity": 0, "scale": 0.5},
    animate={"opacity": 1, "scale": 1},
    exit={"opacity": 0, "scale": 0.5},
    transition={"duration": 0.4, "ease": "easeOut"},
)

PRESET_GROW = MotionPreset(
    name="grow",
    description="Grow from nothing",
    initial={"opacity": 0, "scale": 0},
    animate={"opacity": 1, "scale": 1},
    exit={"opacity": 0, "scale": 0},
    transition={"duration": 0.3, "ease": "easeOut"},
)

# Spring Animations
PRESET_SPRING_POP = MotionPreset(
    name="spring_pop",
    description="Bouncy spring pop-in effect",
    initial={"opacity": 0, "scale": 0.8},
    animate={"opacity": 1, "scale": 1},
    exit={"opacity": 0, "scale": 0.8},
    transition={
        "type": "spring",
        "stiffness": 200,
        "damping": 15,
        "mass": 1,
    },
)

PRESET_SPRING_BOUNCE = MotionPreset(
    name="spring_bounce",
    description="Energetic bounce animation",
    initial={"opacity": 0, "y": 50, "scale": 0.9},
    animate={"opacity": 1, "y": 0, "scale": 1},
    exit={"opacity": 0, "y": 30},
    transition={
        "type": "spring",
        "stiffness": 300,
        "damping": 20,
        "mass": 0.8,
    },
)

PRESET_SPRING_GENTLE = MotionPreset(
    name="spring_gentle",
    description="Soft, gentle spring motion",
    initial={"opacity": 0, "y": 15},
    animate={"opacity": 1, "y": 0},
    exit={"opacity": 0, "y": 15},
    transition={
        "type": "spring",
        "stiffness": 100,
        "damping": 20,
        "mass": 1,
    },
)

PRESET_SPRING_WOBBLY = MotionPreset(
    name="spring_wobbly",
    description="Wobbly, playful spring",
    initial={"opacity": 0, "scale": 0.7, "rotate": -5},
    animate={"opacity": 1, "scale": 1, "rotate": 0},
    exit={"opacity": 0, "scale": 0.7},
    transition={
        "type": "spring",
        "stiffness": 150,
        "damping": 8,
        "mass": 1,
    },
)

# Combined Effect Animations
PRESET_SLIDE_SCALE = MotionPreset(
    name="slide_scale",
    description="Slide up while scaling in",
    initial={"opacity": 0, "y": 30, "scale": 0.95},
    animate={"opacity": 1, "y": 0, "scale": 1},
    exit={"opacity": 0, "y": -20, "scale": 0.95},
    transition={"duration": 0.5, "ease": "easeOut"},
)

PRESET_FLIP_IN = MotionPreset(
    name="flip_in",
    description="3D flip rotation entrance",
    initial={"opacity": 0, "rotateY": 90},
    animate={"opacity": 1, "rotateY": 0},
    exit={"opacity": 0, "rotateY": -90},
    transition={"duration": 0.6, "ease": "easeOut"},
)

PRESET_ROTATE_IN = MotionPreset(
    name="rotate_in",
    description="Rotate while fading in",
    initial={"opacity": 0, "rotate": -10, "scale": 0.9},
    animate={"opacity": 1, "rotate": 0, "scale": 1},
    exit={"opacity": 0, "rotate": 10, "scale": 0.9},
    transition={"duration": 0.4, "ease": "easeOut"},
)

# Interactive State Presets
PRESET_BUTTON_INTERACTIVE = MotionPreset(
    name="button_interactive",
    description="Interactive button with hover and tap states",
    initial={"opacity": 0, "y": 10},
    animate={"opacity": 1, "y": 0},
    exit={"opacity": 0, "y": 10},
    transition={"duration": 0.3, "ease": "easeOut"},
    hover={"scale": 1.02, "y": -2},
    tap={"scale": 0.98},
)

PRESET_CARD_INTERACTIVE = MotionPreset(
    name="card_interactive",
    description="Interactive card with hover lift effect",
    initial={"opacity": 0, "y": 20},
    animate={"opacity": 1, "y": 0},
    exit={"opacity": 0, "y": 20},
    transition={"duration": 0.4, "ease": "easeOut"},
    hover={"y": -5, "scale": 1.01},
    tap={"scale": 0.99},
)

PRESET_IMAGE_HOVER = MotionPreset(
    name="image_hover",
    description="Image with zoom on hover",
    initial={"opacity": 0, "scale": 1.05},
    animate={"opacity": 1, "scale": 1},
    exit={"opacity": 0},
    transition={"duration": 0.5, "ease": "easeOut"},
    hover={"scale": 1.05},
)

# Container/List Animations with Stagger
PRESET_STAGGER_CHILDREN = MotionPreset(
    name="stagger_children",
    description="Container that staggers children animations",
    initial={"opacity": 0},
    animate={"opacity": 1},
    exit={"opacity": 0},
    transition={"duration": 0.2},
    stagger=StaggerConfig(
        stagger_children=0.08,
        delay_children=0.1,
        when="beforeChildren",
    ),
)

PRESET_STAGGER_FAST = MotionPreset(
    name="stagger_fast",
    description="Fast stagger for quick lists",
    initial={"opacity": 0},
    animate={"opacity": 1},
    exit={"opacity": 0},
    transition={"duration": 0.15},
    stagger=StaggerConfig(
        stagger_children=0.04,
        delay_children=0.05,
        when="beforeChildren",
    ),
)

# Viewport-triggered Animations
PRESET_VIEWPORT_FADE = MotionPreset(
    name="viewport_fade",
    description="Fade in when scrolled into view",
    initial={"opacity": 0, "y": 30},
    animate={"opacity": 1, "y": 0},
    transition={"duration": 0.6, "ease": "easeOut"},
    viewport_trigger=True,
    viewport_once=True,
    viewport_margin="-100px",
)

PRESET_VIEWPORT_SCALE = MotionPreset(
    name="viewport_scale",
    description="Scale in when scrolled into view",
    initial={"opacity": 0, "scale": 0.9},
    animate={"opacity": 1, "scale": 1},
    transition={"duration": 0.5, "ease": "easeOut"},
    viewport_trigger=True,
    viewport_once=True,
    viewport_margin="-50px",
)

# No Animation Preset
PRESET_NONE = MotionPreset(
    name="none",
    description="No animation (instant appearance)",
    initial={},
    animate={},
    transition={"duration": 0},
)


# =============================================================================
# PRESET REGISTRY
# =============================================================================

_PRESET_REGISTRY: dict[str, MotionPreset] = {
    # Basic fades
    "fade_in": PRESET_FADE_IN,
    "fade_in_slow": PRESET_FADE_IN_SLOW,
    
    # Slides
    "slide_up": PRESET_SLIDE_UP,
    "slide_down": PRESET_SLIDE_DOWN,
    "slide_left": PRESET_SLIDE_LEFT,
    "slide_right": PRESET_SLIDE_RIGHT,
    
    # Scales
    "scale_in": PRESET_SCALE_IN,
    "scale_up": PRESET_SCALE_UP,
    "grow": PRESET_GROW,
    
    # Springs
    "spring_pop": PRESET_SPRING_POP,
    "spring_bounce": PRESET_SPRING_BOUNCE,
    "spring_gentle": PRESET_SPRING_GENTLE,
    "spring_wobbly": PRESET_SPRING_WOBBLY,
    
    # Combined
    "slide_scale": PRESET_SLIDE_SCALE,
    "flip_in": PRESET_FLIP_IN,
    "rotate_in": PRESET_ROTATE_IN,
    
    # Interactive
    "button_interactive": PRESET_BUTTON_INTERACTIVE,
    "card_interactive": PRESET_CARD_INTERACTIVE,
    "image_hover": PRESET_IMAGE_HOVER,
    
    # Stagger
    "stagger_children": PRESET_STAGGER_CHILDREN,
    "stagger_fast": PRESET_STAGGER_FAST,
    
    # Viewport
    "viewport_fade": PRESET_VIEWPORT_FADE,
    "viewport_scale": PRESET_VIEWPORT_SCALE,
    
    # None
    "none": PRESET_NONE,
}


def get_motion_preset(name: str) -> MotionPreset:
    """
    Retrieve a motion preset by name.
    
    Args:
        name: The name of the preset to retrieve.
        
    Returns:
        The requested MotionPreset, or fade_in as fallback.
        
    Example:
        >>> preset = get_motion_preset("spring_pop")
        >>> preset.name
        'spring_pop'
    """
    return _PRESET_REGISTRY.get(name, PRESET_FADE_IN)


def get_available_presets() -> list[str]:
    """
    Get a list of all available preset names.
    
    Returns:
        List of preset name strings.
    """
    return list(_PRESET_REGISTRY.keys())


def register_preset(preset: MotionPreset) -> None:
    """
    Register a custom motion preset.
    
    Args:
        preset: The MotionPreset to register.
        
    Raises:
        ValueError: If a preset with the same name already exists.
    """
    if preset.name in _PRESET_REGISTRY:
        raise ValueError(f"Preset '{preset.name}' already exists")
    _PRESET_REGISTRY[preset.name] = preset


def get_preset_for_component(component_type: str) -> MotionPreset:
    """
    Get the recommended motion preset for a component type.
    
    This provides sensible defaults for different UI components.
    
    Args:
        component_type: The type of UI component (e.g., "button", "card").
        
    Returns:
        A suitable MotionPreset for the component type.
    """
    component_presets: dict[str, str] = {
        "button": "button_interactive",
        "card": "card_interactive",
        "container": "stagger_children",
        "image": "image_hover",
        "text": "slide_up",
        "heading": "slide_up",
        "icon": "spring_pop",
        "badge": "scale_in",
        "input": "fade_in",
        "divider": "fade_in",
        "list": "stagger_children",
        "nav": "slide_down",
        "hero": "viewport_fade",
        "section": "viewport_fade",
        "footer": "fade_in_slow",
    }
    
    preset_name = component_presets.get(component_type, "fade_in")
    return get_motion_preset(preset_name)


def create_custom_spring(
    stiffness: float = 100,
    damping: float = 10,
    mass: float = 1,
    initial_props: Optional[dict[str, Any]] = None,
    animate_props: Optional[dict[str, Any]] = None,
) -> MotionPreset:
    """
    Create a custom spring animation preset.
    
    Args:
        stiffness: Spring stiffness (higher = snappier).
        damping: Damping coefficient (higher = less bounce).
        mass: Virtual mass of the object.
        initial_props: Initial animation state.
        animate_props: Target animation state.
        
    Returns:
        A custom MotionPreset with spring physics.
    """
    spring_config = SpringConfig(
        stiffness=stiffness,
        damping=damping,
        mass=mass,
    )
    
    return MotionPreset(
        name=f"custom_spring_{stiffness}_{damping}",
        description=f"Custom spring (stiffness={stiffness}, damping={damping})",
        initial=initial_props or {"opacity": 0, "scale": 0.9},
        animate=animate_props or {"opacity": 1, "scale": 1},
        transition=spring_config.to_dict(),
    )


def create_stagger_preset(
    stagger_delay: float = 0.1,
    initial_delay: float = 0.0,
    child_preset: str = "slide_up",
) -> MotionPreset:
    """
    Create a container preset with staggered children.
    
    Args:
        stagger_delay: Delay between each child's animation.
        initial_delay: Delay before first child starts.
        child_preset: Name of preset to use for children.
        
    Returns:
        A MotionPreset configured for staggered children.
    """
    return MotionPreset(
        name=f"stagger_{stagger_delay}",
        description=f"Stagger container (delay={stagger_delay}s)",
        initial={"opacity": 1},
        animate={"opacity": 1},
        transition={"duration": 0.1},
        stagger=StaggerConfig(
            stagger_children=stagger_delay,
            delay_children=initial_delay,
        ),
    )
