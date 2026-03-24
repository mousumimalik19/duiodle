"""
React Code Generator for Duiodle.

This module converts enriched UI trees into production-ready React + Tailwind
+ Framer Motion code. It handles recursive JSX generation, motion prop
spreading, and template rendering.

Author: Duiodle Team
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

from jinja2 import Environment, FileSystemLoader, Template

# Import TailwindMapper - handle both relative and absolute imports
try:
    from ..theme.tailwind_mapper import TailwindMapper
except ImportError:
    TailwindMapper = None  # type: ignore


class OutputFormat(Enum):
    """Supported output formats for code generation."""
    
    REACT_TAILWIND = "react_tailwind"
    REACT_CSS_MODULES = "react_css_modules"
    REACT_STYLED = "react_styled_components"
    HTML_TAILWIND = "html_tailwind"
    NEXT_JS = "nextjs"


class ComponentTag(Enum):
    """HTML/React element tags for component types."""
    
    DIV = "div"
    BUTTON = "button"
    INPUT = "input"
    IMG = "img"
    SPAN = "span"
    P = "p"
    H1 = "h1"
    H2 = "h2"
    H3 = "h3"
    H4 = "h4"
    H5 = "h5"
    H6 = "h6"
    A = "a"
    FORM = "form"
    LABEL = "label"
    TEXTAREA = "textarea"
    SELECT = "select"
    NAV = "nav"
    HEADER = "header"
    FOOTER = "footer"
    MAIN = "main"
    SECTION = "section"
    ARTICLE = "article"
    ASIDE = "aside"
    UL = "ul"
    OL = "ol"
    LI = "li"
    TABLE = "table"
    SVG = "svg"


@dataclass(frozen=True)
class RenderConfig:
    """Configuration for the React renderer."""
    
    # Indentation settings
    indent_size: int = 2
    use_tabs: bool = False
    
    # Component settings
    use_motion_wrappers: bool = True
    use_semantic_tags: bool = True
    generate_keys: bool = True
    
    # Output settings
    format: OutputFormat = OutputFormat.REACT_TAILWIND
    include_imports: bool = True
    include_type_annotations: bool = True
    
    # Template settings
    template_name: str = "page.tsx.j2"
    component_name: str = "Page"
    
    # Class name settings
    use_class_name: bool = True  # className vs class
    merge_classes: bool = True
    
    # Motion settings
    motion_prefix: str = "motion"
    include_exit_animations: bool = False
    include_hover_animations: bool = True
    include_tap_animations: bool = True


@dataclass
class RenderContext:
    """Context passed during recursive rendering."""
    
    depth: int = 0
    parent_type: Optional[str] = None
    sibling_index: int = 0
    total_siblings: int = 1
    in_motion_wrapper: bool = False
    key_prefix: str = ""
    
    def child_context(
        self,
        parent_type: str,
        sibling_index: int = 0,
        total_siblings: int = 1
    ) -> "RenderContext":
        """Create a child context with incremented depth."""
        return RenderContext(
            depth=self.depth + 1,
            parent_type=parent_type,
            sibling_index=sibling_index,
            total_siblings=total_siblings,
            in_motion_wrapper=self.in_motion_wrapper,
            key_prefix=f"{self.key_prefix}{sibling_index}_" if self.key_prefix else f"{sibling_index}_"
        )


class ReactRenderer:
    """
    Converts enriched UI trees into React + Tailwind + Framer Motion code.
    
    This renderer handles:
    - Recursive JSX generation
    - Tailwind class mapping
    - Framer Motion integration
    - Proper indentation and formatting
    - Template-based page generation
    
    Example:
        >>> mapper = TailwindMapper(theme_tokens)
        >>> renderer = ReactRenderer(mapper)
        >>> code = renderer.render(ui_tree)
        >>> print(code)
    """
    
    # Component type to HTML tag mapping
    TYPE_TO_TAG: dict[str, str] = {
        "container": "div",
        "card": "div",
        "button": "button",
        "input": "input",
        "text": "p",
        "heading": "h2",
        "h1": "h1",
        "h2": "h2",
        "h3": "h3",
        "h4": "h4",
        "h5": "h5",
        "h6": "h6",
        "paragraph": "p",
        "span": "span",
        "image": "img",
        "icon": "span",
        "spacer": "div",
        "divider": "hr",
        "link": "a",
        "form": "form",
        "label": "label",
        "textarea": "textarea",
        "select": "select",
        "checkbox": "input",
        "radio": "input",
        "toggle": "button",
        "slider": "input",
        "badge": "span",
        "chip": "span",
        "avatar": "div",
        "modal": "div",
        "dropdown": "div",
        "tooltip": "div",
        "alert": "div",
        "toast": "div",
        "progress": "div",
        "skeleton": "div",
        "nav": "nav",
        "header": "header",
        "footer": "footer",
        "section": "section",
        "article": "article",
        "sidebar": "aside",
        "list": "ul",
        "list_item": "li",
        "table": "table",
        "grid": "div",
        "flex": "div",
        "hero": "section",
        "cta": "div",
        "feature": "div",
        "testimonial": "div",
        "pricing": "div",
        "faq": "div",
    }
    
    # Self-closing tags that don't have children
    SELF_CLOSING_TAGS: set[str] = {"img", "input", "hr", "br"}
    
    def __init__(
        self,
        tailwind_mapper: Optional[Any] = None,
        config: Optional[RenderConfig] = None
    ) -> None:
        """
        Initialize the React renderer.
        
        Args:
            tailwind_mapper: TailwindMapper instance for class generation.
            config: Render configuration options.
        """
        self.tailwind_mapper = tailwind_mapper
        self.config = config or RenderConfig()
        
        # Set up Jinja2 environment
        template_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
        
        # Custom type renderers
        self._custom_renderers: dict[str, Callable] = {}
        
        # Register built-in custom renderers
        self._register_builtin_renderers()
    
    def _register_builtin_renderers(self) -> None:
        """Register built-in custom renderers for specific component types."""
        self._custom_renderers["image"] = self._render_image
        self._custom_renderers["input"] = self._render_input
        self._custom_renderers["checkbox"] = self._render_checkbox
        self._custom_renderers["radio"] = self._render_radio
        self._custom_renderers["link"] = self._render_link
        self._custom_renderers["icon"] = self._render_icon
    
    def register_renderer(
        self,
        component_type: str,
        renderer: Callable[[dict, RenderContext], str]
    ) -> None:
        """
        Register a custom renderer for a component type.
        
        Args:
            component_type: The component type to handle.
            renderer: Callable that takes (node, context) and returns JSX string.
        """
        self._custom_renderers[component_type] = renderer
    
    def render(
        self,
        tree: dict[str, Any],
        use_template: bool = True
    ) -> str:
        """
        Render a UI tree to React code.
        
        Args:
            tree: The enriched UI tree to render.
            use_template: Whether to wrap in page template.
        
        Returns:
            Complete React component code as string.
        """
        # Generate JSX content
        context = RenderContext()
        jsx_content = self._render_node(tree, context)
        
        if not use_template:
            return jsx_content
        
        # Load and render template
        try:
            template = self.jinja_env.get_template(self.config.template_name)
        except Exception:
            # Fallback to inline template if file not found
            template = Template(self._get_fallback_template())
        
        # Determine required imports
        imports = self._collect_imports(tree)
        
        return template.render(
            content=jsx_content,
            component_name=self.config.component_name,
            imports=imports,
            has_motion=self._tree_has_motion(tree),
            has_images=self._tree_has_images(tree),
            has_links=self._tree_has_links(tree)
        )
    
    def render_component(
        self,
        tree: dict[str, Any],
        component_name: str = "Component"
    ) -> str:
        """
        Render a tree as a standalone React component.
        
        Args:
            tree: The UI tree to render.
            component_name: Name for the component.
        
        Returns:
            React component code.
        """
        jsx_content = self._render_node(tree, RenderContext())
        has_motion = self._tree_has_motion(tree)
        
        imports = ['import React from "react";']
        if has_motion:
            imports.append('import { motion } from "framer-motion";')
        
        return f"""{chr(10).join(imports)}

export default function {component_name}() {{
  return (
    {self._indent(jsx_content, 2)}
  );
}}
"""
    
    def _render_node(
        self,
        node: dict[str, Any],
        context: RenderContext
    ) -> str:
        """
        Recursively render a single node to JSX.
        
        Args:
            node: The node to render.
            context: Current render context.
        
        Returns:
            JSX string for the node and its children.
        """
        node_type = node.get("type", "container")
        
        # Check for custom renderer
        if node_type in self._custom_renderers:
            return self._custom_renderers[node_type](node, context)
        
        # Get appropriate HTML tag
        tag = self._get_tag_for_type(node_type)
        
        # Check if node has motion
        has_motion = self._node_has_motion(node) and self.config.use_motion_wrappers
        
        # Build attributes
        attributes = self._build_attributes(node, context, has_motion)
        
        # Get children
        children = node.get("children", [])
        
        # Handle self-closing tags
        if tag in self.SELF_CLOSING_TAGS:
            return self._render_self_closing(tag, attributes, has_motion)
        
        # Render opening tag
        if has_motion:
            opening = f"<{self.config.motion_prefix}.{tag}{attributes}>"
            closing = f"</{self.config.motion_prefix}.{tag}>"
        else:
            opening = f"<{tag}{attributes}>"
            closing = f"</{tag}>"
        
        # No children - render on single line or with text content
        if not children:
            text_content = node.get("content", node.get("text", ""))
            if text_content:
                return f"{opening}{self._escape_jsx(text_content)}{closing}"
            return f"{opening}{closing}"
        
        # Render children
        child_jsx_parts = []
        for i, child in enumerate(children):
            child_context = context.child_context(
                parent_type=node_type,
                sibling_index=i,
                total_siblings=len(children)
            )
            child_jsx = self._render_node(child, child_context)
            child_jsx_parts.append(child_jsx)
        
        # Format with proper indentation
        indent = self._get_indent(1)
        children_jsx = f"\n{indent}".join(child_jsx_parts)
        
        return f"{opening}\n{indent}{children_jsx}\n{closing}"
    
    def _render_self_closing(
        self,
        tag: str,
        attributes: str,
        has_motion: bool
    ) -> str:
        """Render a self-closing tag."""
        if has_motion:
            return f"<{self.config.motion_prefix}.{tag}{attributes} />"
        return f"<{tag}{attributes} />"
    
    def _render_image(
        self,
        node: dict[str, Any],
        context: RenderContext
    ) -> str:
        """Custom renderer for image nodes."""
        classes = self._get_classes_for_node(node)
        
        # Get image properties
        src = node.get("src", node.get("placeholder", {}).get("src", "/placeholder.svg"))
        alt = node.get("alt", node.get("placeholder", {}).get("alt", "Image"))
        
        # Build attributes
        attrs = [f'className="{classes}"'] if classes else []
        attrs.append(f'src="{src}"')
        attrs.append(f'alt="{alt}"')
        
        # Add dimensions if specified
        if "width" in node:
            attrs.append(f'width={{{node["width"]}}}')
        if "height" in node:
            attrs.append(f'height={{{node["height"]}}}')
        
        # Add motion if present
        motion_attrs = self._get_motion_attributes(node)
        if motion_attrs:
            attrs.extend(motion_attrs)
            tag = f"{self.config.motion_prefix}.img"
        else:
            tag = "img"
        
        attr_str = " " + " ".join(attrs) if attrs else ""
        return f"<{tag}{attr_str} />"
    
    def _render_input(
        self,
        node: dict[str, Any],
        context: RenderContext
    ) -> str:
        """Custom renderer for input nodes."""
        classes = self._get_classes_for_node(node)
        
        # Get input properties
        input_type = node.get("input_type", "text")
        placeholder = node.get("placeholder", "")
        name = node.get("name", "")
        
        attrs = [f'className="{classes}"'] if classes else []
        attrs.append(f'type="{input_type}"')
        if placeholder:
            attrs.append(f'placeholder="{placeholder}"')
        if name:
            attrs.append(f'name="{name}"')
        
        attr_str = " " + " ".join(attrs) if attrs else ""
        return f"<input{attr_str} />"
    
    def _render_checkbox(
        self,
        node: dict[str, Any],
        context: RenderContext
    ) -> str:
        """Custom renderer for checkbox nodes."""
        classes = self._get_classes_for_node(node)
        checked = node.get("checked", False)
        
        attrs = ['type="checkbox"']
        if classes:
            attrs.append(f'className="{classes}"')
        if checked:
            attrs.append("defaultChecked")
        
        attr_str = " " + " ".join(attrs)
        return f"<input{attr_str} />"
    
    def _render_radio(
        self,
        node: dict[str, Any],
        context: RenderContext
    ) -> str:
        """Custom renderer for radio nodes."""
        classes = self._get_classes_for_node(node)
        name = node.get("name", "radio-group")
        value = node.get("value", "")
        
        attrs = ['type="radio"', f'name="{name}"']
        if classes:
            attrs.append(f'className="{classes}"')
        if value:
            attrs.append(f'value="{value}"')
        
        attr_str = " " + " ".join(attrs)
        return f"<input{attr_str} />"
    
    def _render_link(
        self,
        node: dict[str, Any],
        context: RenderContext
    ) -> str:
        """Custom renderer for link nodes."""
        classes = self._get_classes_for_node(node)
        href = node.get("href", "#")
        text = node.get("content", node.get("text", "Link"))
        target = node.get("target", "")
        
        attrs = [f'href="{href}"']
        if classes:
            attrs.append(f'className="{classes}"')
        if target:
            attrs.append(f'target="{target}"')
            if target == "_blank":
                attrs.append('rel="noopener noreferrer"')
        
        attr_str = " " + " ".join(attrs)
        return f"<a{attr_str}>{self._escape_jsx(text)}</a>"
    
    def _render_icon(
        self,
        node: dict[str, Any],
        context: RenderContext
    ) -> str:
        """Custom renderer for icon nodes."""
        classes = self._get_classes_for_node(node)
        icon_name = node.get("icon", "star")
        
        # Render as a span with icon class
        class_str = f"{classes} icon-{icon_name}" if classes else f"icon-{icon_name}"
        return f'<span className="{class_str}" aria-hidden="true" />'
    
    def _build_attributes(
        self,
        node: dict[str, Any],
        context: RenderContext,
        has_motion: bool
    ) -> str:
        """Build attribute string for a JSX element."""
        attrs: list[str] = []
        
        # Add key if configured and in a list
        if self.config.generate_keys and context.total_siblings > 1:
            key = node.get("id", f"{context.key_prefix}{context.sibling_index}")
            attrs.append(f'key="{key}"')
        
        # Add className
        classes = self._get_classes_for_node(node)
        if classes:
            attrs.append(f'className="{classes}"')
        
        # Add motion attributes
        if has_motion:
            motion_attrs = self._get_motion_attributes(node)
            attrs.extend(motion_attrs)
        
        # Add accessibility attributes
        a11y_attrs = self._get_accessibility_attributes(node)
        attrs.extend(a11y_attrs)
        
        # Add data attributes
        data_attrs = self._get_data_attributes(node)
        attrs.extend(data_attrs)
        
        if not attrs:
            return ""
        
        return " " + " ".join(attrs)
    
    def _get_classes_for_node(self, node: dict[str, Any]) -> str:
        """Get Tailwind classes for a node."""
        # If mapper is available, use it
        if self.tailwind_mapper is not None:
            try:
                return self.tailwind_mapper.map_node_to_classes(node)
            except Exception:
                pass
        
        # Fallback: use tailwind_classes from node or build basic classes
        if "tailwind_classes" in node:
            return node["tailwind_classes"]
        
        return self._build_fallback_classes(node)
    
    def _build_fallback_classes(self, node: dict[str, Any]) -> str:
        """Build fallback Tailwind classes when mapper is unavailable."""
        classes: list[str] = []
        node_type = node.get("type", "container")
        layout = node.get("layout", "")
        style = node.get("style", {})
        
        # Layout classes
        if node_type in ("container", "card", "flex", "grid"):
            if layout == "row":
                classes.extend(["flex", "flex-row"])
            elif layout == "column":
                classes.extend(["flex", "flex-col"])
            else:
                classes.append("flex")
        
        # Style-based classes
        if style:
            # Background
            if "background" in style:
                bg = style["background"]
                if bg.startswith("#"):
                    classes.append(f"bg-[{bg}]")
            
            # Text color
            if "text" in style:
                text = style["text"]
                if text.startswith("#"):
                    classes.append(f"text-[{text}]")
            
            # Border radius
            if "radius" in style:
                radius = style["radius"]
                if radius == "none" or radius == "0":
                    classes.append("rounded-none")
                elif radius == "full":
                    classes.append("rounded-full")
                else:
                    classes.append("rounded-lg")
            
            # Padding
            if "padding" in style:
                classes.append("p-4")
        
        # Type-specific defaults
        if node_type == "button":
            classes.extend(["px-4", "py-2", "rounded", "cursor-pointer"])
        elif node_type == "card":
            classes.extend(["rounded-lg", "shadow-md", "p-4"])
        elif node_type == "spacer":
            direction = node.get("direction", "vertical")
            size = node.get("size", 4)
            if direction == "horizontal":
                classes.append(f"w-{size}")
            else:
                classes.append(f"h-{size}")
        elif node_type == "divider":
            classes.extend(["border-t", "border-gray-200", "w-full"])
        elif node_type == "image":
            classes.extend(["object-cover"])
        
        return " ".join(classes)
    
    def _get_motion_attributes(self, node: dict[str, Any]) -> list[str]:
        """Extract motion attributes from a node."""
        motion = node.get("motion", {})
        if not motion:
            return []
        
        attrs: list[str] = []
        
        # Initial state
        if "initial" in motion:
            attrs.append(f"initial={{{self._dict_to_jsx(motion['initial'])}}}")
        
        # Animate state
        if "animate" in motion:
            attrs.append(f"animate={{{self._dict_to_jsx(motion['animate'])}}}")
        
        # Exit state
        if "exit" in motion and self.config.include_exit_animations:
            attrs.append(f"exit={{{self._dict_to_jsx(motion['exit'])}}}")
        
        # Transition
        if "transition" in motion:
            attrs.append(f"transition={{{self._dict_to_jsx(motion['transition'])}}}")
        
        # Hover state
        if "whileHover" in motion and self.config.include_hover_animations:
            attrs.append(f"whileHover={{{self._dict_to_jsx(motion['whileHover'])}}}")
        
        # Tap/Press state
        if "whileTap" in motion and self.config.include_tap_animations:
            attrs.append(f"whileTap={{{self._dict_to_jsx(motion['whileTap'])}}}")
        
        # Viewport-based animations
        if "whileInView" in motion:
            attrs.append(f"whileInView={{{self._dict_to_jsx(motion['whileInView'])}}}")
            if "viewport" in motion:
                attrs.append(f"viewport={{{self._dict_to_jsx(motion['viewport'])}}}")
        
        return attrs
    
    def _get_accessibility_attributes(self, node: dict[str, Any]) -> list[str]:
        """Extract accessibility attributes from a node."""
        attrs: list[str] = []
        a11y = node.get("accessibility", {})
        
        if "role" in a11y:
            attrs.append(f'role="{a11y["role"]}"')
        if "aria-label" in a11y:
            attrs.append(f'aria-label="{a11y["aria-label"]}"')
        if "aria-hidden" in a11y:
            attrs.append(f'aria-hidden={{{str(a11y["aria-hidden"]).lower()}}}')
        if "tabIndex" in a11y:
            attrs.append(f'tabIndex={{{a11y["tabIndex"]}}}')
        
        return attrs
    
    def _get_data_attributes(self, node: dict[str, Any]) -> list[str]:
        """Extract data attributes from a node."""
        attrs: list[str] = []
        data = node.get("data", {})
        
        for key, value in data.items():
            safe_key = key.replace("_", "-")
            if isinstance(value, bool):
                attrs.append(f'data-{safe_key}={{{str(value).lower()}}}')
            elif isinstance(value, (int, float)):
                attrs.append(f'data-{safe_key}={{{value}}}')
            else:
                attrs.append(f'data-{safe_key}="{value}"')
        
        return attrs
    
    def _get_tag_for_type(self, node_type: str) -> str:
        """Get the HTML tag for a component type."""
        return self.TYPE_TO_TAG.get(node_type, "div")
    
    def _dict_to_jsx(self, d: dict[str, Any]) -> str:
        """Convert a Python dict to JSX object literal string."""
        if not d:
            return "{}"
        
        parts: list[str] = []
        for key, value in d.items():
            # Handle camelCase conversion
            jsx_key = self._to_camel_case(key)
            
            if isinstance(value, bool):
                parts.append(f"{jsx_key}: {str(value).lower()}")
            elif isinstance(value, str):
                parts.append(f'{jsx_key}: "{value}"')
            elif isinstance(value, dict):
                parts.append(f"{jsx_key}: {self._dict_to_jsx(value)}")
            elif isinstance(value, list):
                list_str = json.dumps(value)
                parts.append(f"{jsx_key}: {list_str}")
            else:
                parts.append(f"{jsx_key}: {value}")
        
        return "{ " + ", ".join(parts) + " }"
    
    def _to_camel_case(self, snake_str: str) -> str:
        """Convert snake_case to camelCase."""
        components = snake_str.split("_")
        return components[0] + "".join(x.title() for x in components[1:])
    
    def _escape_jsx(self, text: str) -> str:
        """Escape text for JSX content."""
        # Escape curly braces and angle brackets
        text = text.replace("{", "&#123;")
        text = text.replace("}", "&#125;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        return text
    
    def _get_indent(self, level: int) -> str:
        """Get indentation string for a given level."""
        if self.config.use_tabs:
            return "\t" * level
        return " " * (self.config.indent_size * level)
    
    def _indent(self, text: str, levels: int) -> str:
        """Indent all lines of text by given levels."""
        indent = self._get_indent(levels)
        lines = text.split("\n")
        return "\n".join(indent + line if line.strip() else line for line in lines)
    
    def _node_has_motion(self, node: dict[str, Any]) -> bool:
        """Check if a node has motion metadata."""
        motion = node.get("motion", {})
        return bool(motion and (motion.get("initial") or motion.get("animate")))
    
    def _tree_has_motion(self, tree: dict[str, Any]) -> bool:
        """Check if any node in the tree has motion."""
        if self._node_has_motion(tree):
            return True
        for child in tree.get("children", []):
            if self._tree_has_motion(child):
                return True
        return False
    
    def _tree_has_images(self, tree: dict[str, Any]) -> bool:
        """Check if tree contains image nodes."""
        if tree.get("type") == "image":
            return True
        for child in tree.get("children", []):
            if self._tree_has_images(child):
                return True
        return False
    
    def _tree_has_links(self, tree: dict[str, Any]) -> bool:
        """Check if tree contains link nodes."""
        if tree.get("type") == "link":
            return True
        for child in tree.get("children", []):
            if self._tree_has_links(child):
                return True
        return False
    
    def _collect_imports(self, tree: dict[str, Any]) -> list[str]:
        """Collect required imports based on tree content."""
        imports = ['import React from "react";']
        
        if self._tree_has_motion(tree):
            imports.append('import { motion } from "framer-motion";')
        
        return imports
    
    def _get_fallback_template(self) -> str:
        """Return fallback template if file template not found."""
        return '''{{ imports | join("\\n") }}

export default function {{ component_name }}() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8">
      {{ content }}
    </main>
  );
}
'''


def render_tree_to_react(
    tree: dict[str, Any],
    tailwind_mapper: Optional[Any] = None,
    config: Optional[RenderConfig] = None
) -> str:
    """
    Convenience function to render a UI tree to React code.
    
    Args:
        tree: The UI tree to render.
        tailwind_mapper: Optional TailwindMapper instance.
        config: Optional render configuration.
    
    Returns:
        React component code as string.
    """
    renderer = ReactRenderer(tailwind_mapper, config)
    return renderer.render(tree)


def render_component(
    tree: dict[str, Any],
    component_name: str = "Component",
    tailwind_mapper: Optional[Any] = None
) -> str:
    """
    Render a tree as a standalone React component.
    
    Args:
        tree: The UI tree to render.
        component_name: Name for the component.
        tailwind_mapper: Optional TailwindMapper instance.
    
    Returns:
        React component code.
    """
    renderer = ReactRenderer(tailwind_mapper)
    return renderer.render_component(tree, component_name)
