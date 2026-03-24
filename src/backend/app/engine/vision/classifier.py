"""
Shape Classifier Module

This module provides rule-based classification of primitive geometric
shapes into UI intent hints. It bridges the gap between raw vision
detections and semantic UI components.

The classifier is intentionally simple and rule-based, designed to be
easily replaced with ML-based classification in the future.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .base import DetectedShape, PrimitiveShapeType


class UIHint(str, Enum):
    """
    UI intent hints derived from shape analysis.
    
    These hints guide the layout resolver in determining
    what type of UI component a shape likely represents.
    """
    # Structural
    CONTAINER = "container"
    CARD = "card"
    SECTION = "section"
    HEADER = "header"
    FOOTER = "footer"
    SIDEBAR = "sidebar"
    MODAL = "modal"
    
    # Interactive
    BUTTON = "button"
    INPUT = "input"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    TOGGLE = "toggle"
    SLIDER = "slider"
    
    # Content
    TEXT = "text"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LABEL = "label"
    
    # Media
    IMAGE = "image"
    ICON = "icon"
    AVATAR = "avatar"
    
    # Decorative
    DIVIDER = "divider"
    SPACER = "spacer"
    BADGE = "badge"
    
    # Navigation
    NAV_ITEM = "nav_item"
    TAB = "tab"
    MENU = "menu"
    
    # Data
    LIST_ITEM = "list_item"
    TABLE_CELL = "table_cell"
    PROGRESS = "progress"
    
    # Unknown
    UNKNOWN = "unknown"


@dataclass
class ClassificationRule:
    """
    A single classification rule for shape-to-UI mapping.
    
    Attributes:
        shape_type: The primitive shape type to match.
        ui_hint: The UI hint to assign.
        priority: Rule priority (higher = checked first).
        min_aspect_ratio: Minimum width/height ratio.
        max_aspect_ratio: Maximum width/height ratio.
        min_area: Minimum normalized area.
        max_area: Maximum normalized area.
        min_confidence: Minimum detection confidence.
    """
    shape_type: PrimitiveShapeType
    ui_hint: UIHint
    priority: int = 0
    min_aspect_ratio: Optional[float] = None
    max_aspect_ratio: Optional[float] = None
    min_area: Optional[float] = None
    max_area: Optional[float] = None
    min_confidence: float = 0.0
    
    def matches(self, shape: DetectedShape) -> bool:
        """
        Check if this rule matches the given shape.
        
        Args:
            shape: The detected shape to check.
        
        Returns:
            True if all rule conditions are satisfied.
        """
        # Check shape type
        if shape.shape_type != self.shape_type:
            return False
        
        # Check confidence
        if shape.confidence < self.min_confidence:
            return False
        
        # Check aspect ratio
        aspect_ratio = shape.bbox.aspect_ratio
        if self.min_aspect_ratio is not None:
            if aspect_ratio < self.min_aspect_ratio:
                return False
        if self.max_aspect_ratio is not None:
            if aspect_ratio > self.max_aspect_ratio:
                return False
        
        # Check area
        area = shape.bbox.area
        if self.min_area is not None:
            if area < self.min_area:
                return False
        if self.max_area is not None:
            if area > self.max_area:
                return False
        
        return True


@dataclass
class ClassifiedShape:
    """
    A shape with UI classification applied.
    
    This extends the base detection with semantic UI information.
    
    Attributes:
        detection: The original detected shape.
        ui_hint: The inferred UI intent.
        hint_confidence: Confidence in the UI hint assignment.
        alternative_hints: Other possible UI hints with confidence.
        metadata: Additional classification metadata.
    """
    detection: DetectedShape
    ui_hint: UIHint
    hint_confidence: float
    alternative_hints: List[Tuple[UIHint, float]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = self.detection.to_dict()
        result.update({
            "ui_hint": self.ui_hint.value,
            "hint_confidence": self.hint_confidence,
            "alternative_hints": [
                {"hint": h.value, "confidence": c}
                for h, c in self.alternative_hints
            ],
            "metadata": self.metadata,
        })
        return result


class ShapeClassifier:
    """
    Rule-based classifier for mapping shapes to UI hints.
    
    The classifier uses a set of configurable rules to determine
    what UI component a detected shape most likely represents.
    
    Rules are evaluated in priority order, with the first matching
    rule determining the classification.
    
    Example:
        classifier = ShapeClassifier()
        classified = classifier.classify(detected_shape)
        print(f"UI Hint: {classified.ui_hint}")
        
        # Batch classification
        all_classified = classifier.classify_batch(shapes)
    """
    
    # Default classification rules
    DEFAULT_RULES: List[ClassificationRule] = [
        # Lines -> Dividers
        ClassificationRule(
            shape_type=PrimitiveShapeType.LINE,
            ui_hint=UIHint.DIVIDER,
            priority=100,
        ),
        
        # Small circles -> Icons
        ClassificationRule(
            shape_type=PrimitiveShapeType.CIRCLE,
            ui_hint=UIHint.ICON,
            priority=90,
            max_area=0.02,
        ),
        
        # Medium circles -> Avatars
        ClassificationRule(
            shape_type=PrimitiveShapeType.CIRCLE,
            ui_hint=UIHint.AVATAR,
            priority=85,
            min_area=0.02,
            max_area=0.08,
        ),
        
        # Large circles -> Images
        ClassificationRule(
            shape_type=PrimitiveShapeType.CIRCLE,
            ui_hint=UIHint.IMAGE,
            priority=80,
            min_area=0.08,
        ),
        
        # Small ellipses -> Badges
        ClassificationRule(
            shape_type=PrimitiveShapeType.ELLIPSE,
            ui_hint=UIHint.BADGE,
            priority=75,
            max_area=0.01,
        ),
        
        # Wide thin rectangles at top -> Headers
        ClassificationRule(
            shape_type=PrimitiveShapeType.RECTANGLE,
            ui_hint=UIHint.HEADER,
            priority=95,
            min_aspect_ratio=3.0,
            max_area=0.15,
        ),
        
        # Small rectangles with button-like proportions -> Buttons
        ClassificationRule(
            shape_type=PrimitiveShapeType.RECTANGLE,
            ui_hint=UIHint.BUTTON,
            priority=70,
            min_aspect_ratio=1.5,
            max_aspect_ratio=5.0,
            max_area=0.05,
        ),
        
        # Tall thin rectangles -> Inputs
        ClassificationRule(
            shape_type=PrimitiveShapeType.RECTANGLE,
            ui_hint=UIHint.INPUT,
            priority=65,
            min_aspect_ratio=3.0,
            max_aspect_ratio=15.0,
            max_area=0.08,
        ),
        
        # Square-ish small rectangles -> Checkboxes
        ClassificationRule(
            shape_type=PrimitiveShapeType.RECTANGLE,
            ui_hint=UIHint.CHECKBOX,
            priority=60,
            min_aspect_ratio=0.8,
            max_aspect_ratio=1.2,
            max_area=0.005,
        ),
        
        # Medium rectangles -> Cards
        ClassificationRule(
            shape_type=PrimitiveShapeType.RECTANGLE,
            ui_hint=UIHint.CARD,
            priority=50,
            min_area=0.05,
            max_area=0.3,
        ),
        
        # Large rectangles -> Containers
        ClassificationRule(
            shape_type=PrimitiveShapeType.RECTANGLE,
            ui_hint=UIHint.CONTAINER,
            priority=40,
            min_area=0.3,
        ),
        
        # Default rectangle -> Container
        ClassificationRule(
            shape_type=PrimitiveShapeType.RECTANGLE,
            ui_hint=UIHint.CONTAINER,
            priority=10,
        ),
        
        # Triangles -> Icons (likely arrows or indicators)
        ClassificationRule(
            shape_type=PrimitiveShapeType.TRIANGLE,
            ui_hint=UIHint.ICON,
            priority=70,
        ),
        
        # Text regions -> Text
        ClassificationRule(
            shape_type=PrimitiveShapeType.TEXT_REGION,
            ui_hint=UIHint.TEXT,
            priority=100,
        ),
        
        # Polygons -> Generic containers
        ClassificationRule(
            shape_type=PrimitiveShapeType.POLYGON,
            ui_hint=UIHint.CONTAINER,
            priority=20,
        ),
        
        # Ellipses -> Images by default
        ClassificationRule(
            shape_type=PrimitiveShapeType.ELLIPSE,
            ui_hint=UIHint.IMAGE,
            priority=30,
        ),
    ]
    
    def __init__(
        self,
        custom_rules: Optional[List[ClassificationRule]] = None,
        use_default_rules: bool = True
    ) -> None:
        """
        Initialize the shape classifier.
        
        Args:
            custom_rules: Additional custom rules to add.
            use_default_rules: Whether to include default rules.
        """
        self._rules: List[ClassificationRule] = []
        
        if use_default_rules:
            self._rules.extend(self.DEFAULT_RULES)
        
        if custom_rules:
            self._rules.extend(custom_rules)
        
        # Sort by priority (highest first)
        self._rules.sort(key=lambda r: r.priority, reverse=True)
    
    def add_rule(self, rule: ClassificationRule) -> None:
        """
        Add a new classification rule.
        
        Args:
            rule: The rule to add.
        """
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority, reverse=True)
    
    def classify(self, shape: DetectedShape) -> ClassifiedShape:
        """
        Classify a single detected shape.
        
        Args:
            shape: The shape to classify.
        
        Returns:
            ClassifiedShape with UI hint and confidence.
        """
        matched_hints: List[Tuple[UIHint, float]] = []
        
        for rule in self._rules:
            if rule.matches(shape):
                # Calculate hint confidence based on rule and detection
                hint_confidence = self._calculate_hint_confidence(shape, rule)
                matched_hints.append((rule.ui_hint, hint_confidence))
        
        # Handle no matches
        if not matched_hints:
            return ClassifiedShape(
                detection=shape,
                ui_hint=UIHint.UNKNOWN,
                hint_confidence=0.3,
                alternative_hints=[],
                metadata={"classification_method": "fallback"},
            )
        
        # Primary hint is the first match (highest priority)
        primary_hint, primary_confidence = matched_hints[0]
        
        # Alternative hints are remaining matches
        alternative_hints = matched_hints[1:5]  # Limit to top 5
        
        return ClassifiedShape(
            detection=shape,
            ui_hint=primary_hint,
            hint_confidence=primary_confidence,
            alternative_hints=alternative_hints,
            metadata={
                "classification_method": "rule_based",
                "rules_matched": len(matched_hints),
            },
        )
    
    def classify_batch(
        self,
        shapes: List[DetectedShape]
    ) -> List[ClassifiedShape]:
        """
        Classify multiple shapes.
        
        Args:
            shapes: List of shapes to classify.
        
        Returns:
            List of classified shapes.
        """
        return [self.classify(shape) for shape in shapes]
    
    def classify_to_dict(
        self,
        shapes: List[DetectedShape]
    ) -> List[Dict[str, Any]]:
        """
        Classify shapes and return as dictionaries.
        
        Args:
            shapes: List of shapes to classify.
        
        Returns:
            List of classification dictionaries.
        """
        classified = self.classify_batch(shapes)
        return [c.to_dict() for c in classified]
    
    def _calculate_hint_confidence(
        self,
        shape: DetectedShape,
        rule: ClassificationRule
    ) -> float:
        """
        Calculate confidence score for a hint assignment.
        
        Combines detection confidence with rule specificity.
        
        Args:
            shape: The detected shape.
            rule: The matched rule.
        
        Returns:
            Confidence score in [0, 1].
        """
        # Base confidence from detection
        base_confidence = shape.confidence
        
        # Rule specificity bonus
        specificity_bonus = 0.0
        
        # More specific rules (with constraints) get higher confidence
        if rule.min_aspect_ratio is not None or rule.max_aspect_ratio is not None:
            specificity_bonus += 0.05
        if rule.min_area is not None or rule.max_area is not None:
            specificity_bonus += 0.05
        if rule.min_confidence > 0:
            specificity_bonus += 0.03
        
        # Combine scores
        combined = (base_confidence * 0.7) + (specificity_bonus * 0.3) + 0.2
        
        # Clamp to [0, 1]
        return min(1.0, max(0.0, combined))
    
    def get_possible_hints_for_shape(
        self,
        shape_type: PrimitiveShapeType
    ) -> List[UIHint]:
        """
        Get all possible UI hints for a shape type.
        
        Args:
            shape_type: The primitive shape type.
        
        Returns:
            List of possible UI hints.
        """
        hints = set()
        for rule in self._rules:
            if rule.shape_type == shape_type:
                hints.add(rule.ui_hint)
        return list(hints)


def create_default_classifier() -> ShapeClassifier:
    """
    Factory function to create a classifier with default settings.
    
    Returns:
        Configured ShapeClassifier instance.
    """
    return ShapeClassifier(use_default_rules=True)


def classify_shapes(
    shapes: List[DetectedShape]
) -> List[ClassifiedShape]:
    """
    Convenience function for one-shot classification.
    
    Args:
        shapes: List of shapes to classify.
    
    Returns:
        List of classified shapes.
    """
    classifier = create_default_classifier()
    return classifier.classify_batch(shapes)
