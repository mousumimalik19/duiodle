import {
  ArrowLeft,
  Circle,
  Download,
  Eraser,
  Moon,
  MousePointer2,
  Paintbrush2,
  RectangleHorizontal,
  Redo2,
  Shapes,
  Sun,
  Type,
  Undo2,
  X,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import ColorWheel from "./ColorWheel";
import SketchCanvas, {
  type DrawTool,
  type SketchCanvasHandle,
} from "./SketchCanvas";

interface SketchModeProps {
  theme: "light" | "dark";
  toggleTheme: () => void;
  onClose: () => void;
}

type PanelTool = "cursor" | "brush" | "shapes" | "text" | "eraser";
type Mode = "sketch" | "structure" | "preview";

const TOOLS: {
  id: PanelTool;
  label: string;
  shortcut: string;
  icon: React.ReactNode;
}[] = [
  {
    id: "cursor",
    label: "Cursor",
    shortcut: "V",
    icon: <MousePointer2 size={18} />,
  },
  {
    id: "brush",
    label: "Brush",
    shortcut: "B",
    icon: <Paintbrush2 size={18} />,
  },
  { id: "shapes", label: "Shapes", shortcut: "S", icon: <Shapes size={18} /> },
  { id: "text", label: "Text", shortcut: "T", icon: <Type size={18} /> },
  { id: "eraser", label: "Eraser", shortcut: "E", icon: <Eraser size={18} /> },
];

export default function SketchMode({
  theme,
  toggleTheme,
  onClose,
}: SketchModeProps) {
  const [visible, setVisible] = useState(false);
  const [exiting, setExiting] = useState(false);

  const [mode, setMode] = useState<Mode>("sketch");
  const [analyzing, setAnalyzing] = useState(false);

  const [activeTool, setActiveTool] = useState<PanelTool>("brush");
  const [activeShape, setActiveShape] = useState<
    "rect" | "circle" | "button-shape"
  >("rect");
  const [showShapeMenu, setShowShapeMenu] = useState(false);

  const [color, setColor] = useState("#111111");
  const [brushSize, setBrushSize] = useState(4);
  const [opacity, setOpacity] = useState(100);
  const [zoom, setZoom] = useState(1);

  const [projectName, setProjectName] = useState("Untitled Project");
  const [editingName, setEditingName] = useState(false);

  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [showFloatingWheel, setShowFloatingWheel] = useState(false);
  const [floatingWheelPos, setFloatingWheelPos] = useState({ x: 300, y: 200 });
  const [hexInput, setHexInput] = useState("#111111");

  const [bouncingTool, setBouncingTool] = useState<string | null>(null);
  const [ripplePos, setRipplePos] = useState<{ x: number; y: number } | null>(
    null,
  );

  const canvasRef = useRef<SketchCanvasHandle>(null);
  const canvasAreaRef = useRef<HTMLDivElement>(null);
  const nameInputRef = useRef<HTMLInputElement>(null);

  // Entry animation
  useEffect(() => {
    const raf = requestAnimationFrame(() => setVisible(true));
    return () => cancelAnimationFrame(raf);
  }, []);

  const handleClose = useCallback(() => {
    setExiting(true);
    setTimeout(() => onClose(), 280);
  }, [onClose]);

  const selectTool = useCallback((toolId: PanelTool) => {
    setActiveTool(toolId);
    setBouncingTool(toolId);
    setShowShapeMenu(toolId === "shapes");
    setTimeout(() => setBouncingTool(null), 400);
  }, []);

  const handleColorChange = useCallback(
    (newColor: string, e?: React.MouseEvent) => {
      setColor(newColor);
      setHexInput(newColor);
      if (e) {
        const rect = (e.target as HTMLElement).getBoundingClientRect();
        setRipplePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
        setTimeout(() => setRipplePos(null), 600);
      }
    },
    [],
  );

  const handleHexInput = useCallback((val: string) => {
    setHexInput(val);
    if (/^#[0-9a-fA-F]{6}$/.test(val)) {
      setColor(val);
    }
  }, []);

  const handleModeChange = useCallback((newMode: Mode) => {
    setMode(newMode);
    if (newMode === "structure") {
      setAnalyzing(true);
      setTimeout(() => setAnalyzing(false), 2500);
    }
  }, []);

  const handleClearConfirm = useCallback(() => {
    canvasRef.current?.clear();
    setShowClearConfirm(false);
  }, []);

  // Canvas right-click shows floating color wheel
  const handleCanvasContextMenu = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      if (activeTool === "brush") {
        setFloatingWheelPos({ x: e.clientX, y: e.clientY });
        setShowFloatingWheel(true);
      }
    },
    [activeTool],
  );

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Don't fire if typing in an input
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      )
        return;

      if (e.ctrlKey && e.key === "z") {
        e.preventDefault();
        canvasRef.current?.undo();
      } else if (
        e.ctrlKey &&
        (e.key === "y" || (e.shiftKey && e.key === "Z"))
      ) {
        e.preventDefault();
        canvasRef.current?.redo();
      } else if (e.ctrlKey && e.shiftKey && e.key === "Delete") {
        e.preventDefault();
        setShowClearConfirm(true);
      } else if (!e.ctrlKey && !e.altKey) {
        switch (e.key.toLowerCase()) {
          case "b":
            selectTool("brush");
            break;
          case "e":
            selectTool("eraser");
            break;
          case "v":
            selectTool("cursor");
            break;
          case "t":
            selectTool("text");
            break;
          case "s":
            selectTool("shapes");
            break;
          case "escape":
            handleClose();
            break;
        }
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [selectTool, handleClose]);

  const activeDrawTool: DrawTool =
    activeTool === "shapes" ? activeShape : (activeTool as DrawTool);

  const panels =
    theme === "light"
      ? {
          bg: "#f5f5f5",
          toolbar: "#ffffff",
          border: "#e0e0e0",
          text: "#111",
          textMuted: "#666",
        }
      : {
          bg: "#1e1e1e",
          toolbar: "#141414",
          border: "#333",
          text: "#eee",
          textMuted: "#888",
        };

  const containerClass = `sketch-mode-overlay${visible && !exiting ? " sketch-mode-visible" : ""}${exiting ? " sketch-mode-exiting" : ""}`;

  return (
    <div
      className={containerClass}
      style={{
        background: panels.bg,
        color: panels.text,
        fontFamily: "Karla, sans-serif",
      }}
      data-ocid="sketch.modal"
    >
      {/* ── TOP TOOLBAR ── */}
      <div
        className="sketch-toolbar"
        style={{
          background: panels.toolbar,
          borderBottom: `1px solid ${panels.border}`,
          color: panels.text,
        }}
      >
        {/* Left: Back + Name */}
        <div className="sketch-toolbar-left">
          <button
            type="button"
            className="sketch-toolbar-btn sketch-back-btn"
            onClick={handleClose}
            title="Back to home"
            data-ocid="sketch.close_button"
            style={{ color: panels.text }}
          >
            <ArrowLeft size={16} />
            <span>Back</span>
          </button>

          {editingName ? (
            <input
              ref={nameInputRef}
              className="sketch-project-name-input"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              onBlur={() => setEditingName(false)}
              onKeyDown={(e) => {
                if (e.key === "Enter") setEditingName(false);
              }}
              data-ocid="sketch.input"
              style={{
                background: "transparent",
                border: `1px solid ${panels.border}`,
                color: panels.text,
              }}
            />
          ) : (
            <button
              type="button"
              className="sketch-project-name"
              onClick={() => setEditingName(true)}
              style={{ color: panels.text }}
              title="Click to rename"
            >
              {projectName}
            </button>
          )}
        </div>

        {/* Center: Mode tabs */}
        <div className="sketch-mode-tabs">
          {(["sketch", "structure", "preview"] as Mode[]).map((m) => (
            <button
              key={m}
              type="button"
              className={`sketch-mode-tab${mode === m ? " sketch-mode-tab-active" : ""}`}
              onClick={() => handleModeChange(m)}
              data-ocid={`sketch.${m}.tab`}
              style={{
                color: mode === m ? "#111" : panels.textMuted,
              }}
            >
              {m.charAt(0).toUpperCase() + m.slice(1)}
            </button>
          ))}
        </div>

        {/* Right: Actions */}
        <div className="sketch-toolbar-right">
          <button
            type="button"
            className="sketch-toolbar-btn"
            onClick={() => canvasRef.current?.undo()}
            title="Undo (Ctrl+Z)"
            style={{ color: panels.text }}
            data-ocid="sketch.undo.button"
          >
            <Undo2 size={16} />
          </button>
          <button
            type="button"
            className="sketch-toolbar-btn"
            onClick={() => canvasRef.current?.redo()}
            title="Redo (Ctrl+Y)"
            style={{ color: panels.text }}
            data-ocid="sketch.redo.button"
          >
            <Redo2 size={16} />
          </button>
          <button
            type="button"
            className="sketch-toolbar-btn"
            onClick={toggleTheme}
            title={theme === "light" ? "Switch to dark" : "Switch to light"}
            style={{ color: panels.text }}
            data-ocid="sketch.theme.toggle"
          >
            {theme === "light" ? <Moon size={16} /> : <Sun size={16} />}
          </button>
          <button
            type="button"
            className="sketch-toolbar-btn sketch-export-btn"
            onClick={() => canvasRef.current?.exportPNG()}
            title="Export as PNG"
            data-ocid="sketch.export.button"
          >
            <Download size={16} />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* ── MAIN BODY ── */}
      <div className="sketch-body">
        {/* LEFT PANEL */}
        <div
          className="sketch-left-panel"
          style={{
            background: panels.bg,
            borderRight: `1px solid ${panels.border}`,
          }}
        >
          {TOOLS.map((tool) => (
            <div key={tool.id} className="sketch-tool-wrapper">
              <button
                type="button"
                className={`sketch-tool-btn${activeTool === tool.id ? " sketch-tool-active" : ""}${bouncingTool === tool.id ? " sketch-tool-bounce" : ""}`}
                onClick={() => selectTool(tool.id)}
                aria-label={`${tool.label} (${tool.shortcut})`}
                data-ocid={`sketch.${tool.id}.button`}
                style={{
                  color: activeTool === tool.id ? "#111" : panels.textMuted,
                  background:
                    activeTool === tool.id ? "#fbff29" : "transparent",
                }}
              >
                {tool.icon}
              </button>
              <span
                className="sketch-tool-tooltip"
                style={{
                  background: panels.toolbar,
                  color: panels.text,
                  borderColor: panels.border,
                }}
              >
                {tool.label}
                <kbd>{tool.shortcut}</kbd>
              </span>

              {/* Shape sub-menu */}
              {tool.id === "shapes" &&
                showShapeMenu &&
                activeTool === "shapes" && (
                  <div
                    className="sketch-shape-submenu"
                    style={{
                      background: panels.toolbar,
                      border: `1px solid ${panels.border}`,
                      color: panels.text,
                    }}
                  >
                    <button
                      type="button"
                      className={`sketch-shape-btn${activeShape === "rect" ? " active" : ""}`}
                      onClick={() => setActiveShape("rect")}
                      title="Rectangle"
                      style={{
                        color:
                          activeShape === "rect" ? "#fbff29" : panels.textMuted,
                      }}
                      data-ocid="sketch.rect.button"
                    >
                      <RectangleHorizontal size={15} />
                    </button>
                    <button
                      type="button"
                      className={`sketch-shape-btn${activeShape === "circle" ? " active" : ""}`}
                      onClick={() => setActiveShape("circle")}
                      title="Circle/Ellipse"
                      style={{
                        color:
                          activeShape === "circle"
                            ? "#fbff29"
                            : panels.textMuted,
                      }}
                      data-ocid="sketch.circle.button"
                    >
                      <Circle size={15} />
                    </button>
                    <button
                      type="button"
                      className={`sketch-shape-btn${activeShape === "button-shape" ? " active" : ""}`}
                      onClick={() => setActiveShape("button-shape")}
                      title="Button placeholder"
                      style={{
                        color:
                          activeShape === "button-shape"
                            ? "#fbff29"
                            : panels.textMuted,
                      }}
                      data-ocid="sketch.buttonshape.button"
                    >
                      <RectangleHorizontal
                        size={13}
                        strokeWidth={2.5}
                        style={{ borderRadius: 3 }}
                      />
                    </button>
                  </div>
                )}
            </div>
          ))}

          {/* Divider + Clear button */}
          <div
            className="sketch-panel-divider"
            style={{ background: panels.border }}
          />
          <div className="sketch-tool-wrapper">
            <button
              type="button"
              className="sketch-tool-btn sketch-clear-btn"
              onClick={() => setShowClearConfirm(true)}
              title="Clear canvas (Ctrl+Shift+Del)"
              style={{ color: panels.textMuted }}
              data-ocid="sketch.clear.button"
            >
              <X size={16} />
            </button>
            <span
              className="sketch-tool-tooltip"
              style={{
                background: panels.toolbar,
                color: panels.text,
                borderColor: panels.border,
              }}
            >
              Clear
            </span>
          </div>
        </div>

        {/* CANVAS AREA */}
        <div
          ref={canvasAreaRef}
          className="sketch-canvas-area"
          onContextMenu={handleCanvasContextMenu}
        >
          {mode === "sketch" && (
            <SketchCanvas
              ref={canvasRef}
              tool={activeDrawTool}
              color={color}
              brushSize={brushSize}
              opacity={opacity}
              theme={theme}
              zoom={zoom}
              onZoomChange={setZoom}
            />
          )}

          {mode === "preview" && (
            <div
              className="sketch-placeholder-view"
              style={{ color: panels.textMuted }}
            >
              <div className="sketch-placeholder-icon">👁</div>
              <div
                className="sketch-placeholder-title"
                style={{
                  color: panels.text,
                  fontFamily: "Montserrat, sans-serif",
                }}
              >
                Preview Mode
              </div>
              <div className="sketch-placeholder-sub">
                Preview your sketch as a structured interface.
              </div>
            </div>
          )}

          {/* Structure mode scan overlay */}
          {mode === "structure" && analyzing && (
            <div className="sketch-scan-overlay">
              <div className="sketch-scan-lines" />
              <div className="sketch-scan-beam" />
              <div
                className="sketch-scan-text"
                style={{ fontFamily: "Montserrat, sans-serif" }}
              >
                Analyzing structural logic
                <span className="sketch-scan-dots">
                  <span>.</span>
                  <span>.</span>
                  <span>.</span>
                </span>
              </div>
            </div>
          )}

          {mode === "structure" && !analyzing && (
            <div
              className="sketch-placeholder-view"
              style={{ color: panels.textMuted }}
            >
              <div className="sketch-placeholder-icon">🔷</div>
              <div
                className="sketch-placeholder-title"
                style={{
                  color: panels.text,
                  fontFamily: "Montserrat, sans-serif",
                }}
              >
                Structure Detected
              </div>
              <div className="sketch-placeholder-sub">
                Component hierarchy and layout zones identified.
              </div>
            </div>
          )}
        </div>

        {/* RIGHT PANEL */}
        <div
          className="sketch-right-panel"
          style={{
            background: panels.bg,
            borderLeft: `1px solid ${panels.border}`,
          }}
        >
          <div className="sketch-panel-section">
            <div
              className="sketch-panel-label"
              style={{ color: panels.textMuted }}
            >
              Properties
            </div>
          </div>

          {/* Color Wheel */}
          <div className="sketch-panel-section">
            <div
              className="sketch-panel-label"
              style={{ color: panels.textMuted }}
            >
              Color
            </div>
            <div className="sketch-color-wheel-wrap">
              <ColorWheel
                size={160}
                onColorChange={(c) => handleColorChange(c)}
              />
              {ripplePos && (
                <div
                  className="sketch-color-ripple"
                  style={{ left: ripplePos.x, top: ripplePos.y }}
                />
              )}
            </div>
            <div className="sketch-color-swatch-row">
              <div
                className="sketch-color-swatch"
                style={{ background: color }}
                title={color}
              />
              <input
                className="sketch-hex-input"
                value={hexInput}
                onChange={(e) => handleHexInput(e.target.value)}
                maxLength={7}
                spellCheck={false}
                data-ocid="sketch.color.input"
                style={{
                  background: "transparent",
                  border: `1px solid ${panels.border}`,
                  color: panels.text,
                }}
              />
            </div>
          </div>

          {/* Brush size */}
          <div className="sketch-panel-section">
            <div
              className="sketch-panel-label"
              style={{ color: panels.textMuted }}
            >
              Brush Size{" "}
              <span style={{ color: panels.text }}>{brushSize}px</span>
            </div>
            <input
              type="range"
              min={1}
              max={30}
              value={brushSize}
              onChange={(e) => setBrushSize(Number(e.target.value))}
              className="sketch-slider"
              data-ocid="sketch.brushsize.input"
            />
          </div>

          {/* Opacity */}
          <div className="sketch-panel-section">
            <div
              className="sketch-panel-label"
              style={{ color: panels.textMuted }}
            >
              Opacity <span style={{ color: panels.text }}>{opacity}%</span>
            </div>
            <input
              type="range"
              min={1}
              max={100}
              value={opacity}
              onChange={(e) => setOpacity(Number(e.target.value))}
              className="sketch-slider"
              data-ocid="sketch.opacity.input"
            />
          </div>

          {/* Zoom */}
          <div className="sketch-panel-section">
            <div
              className="sketch-panel-label"
              style={{ color: panels.textMuted }}
            >
              Zoom{" "}
              <span style={{ color: panels.text }}>
                {Math.round(zoom * 100)}%
              </span>
            </div>
            <input
              type="range"
              min={25}
              max={400}
              step={5}
              value={Math.round(zoom * 100)}
              onChange={(e) => setZoom(Number(e.target.value) / 100)}
              className="sketch-slider"
              data-ocid="sketch.zoom.input"
            />
          </div>

          {/* Keyboard shortcuts hint */}
          <div className="sketch-panel-section sketch-shortcuts-section">
            <div
              className="sketch-panel-label"
              style={{ color: panels.textMuted }}
            >
              Shortcuts
            </div>
            <div
              className="sketch-shortcuts"
              style={{ color: panels.textMuted }}
            >
              {[
                ["B", "Brush"],
                ["E", "Eraser"],
                ["V", "Cursor"],
                ["T", "Text"],
                ["S", "Shapes"],
                ["Ctrl+Z", "Undo"],
                ["Ctrl+Y", "Redo"],
              ].map(([key, label]) => (
                <div key={key} className="sketch-shortcut-row">
                  <kbd
                    className="sketch-kbd"
                    style={{
                      background: panels.toolbar,
                      color: panels.text,
                      borderColor: panels.border,
                    }}
                  >
                    {key}
                  </kbd>
                  <span>{label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── FLOATING COLOR WHEEL ── */}
      {showFloatingWheel && (
        <>
          {/* Backdrop to close */}
          <div
            className="sketch-floating-backdrop"
            onClick={() => setShowFloatingWheel(false)}
            onKeyDown={(e) => {
              if (e.key === "Escape") setShowFloatingWheel(false);
            }}
            role="presentation"
          />
          <div
            className="sketch-floating-wheel"
            style={{
              top: Math.min(floatingWheelPos.y - 110, window.innerHeight - 280),
              left: Math.min(floatingWheelPos.x - 110, window.innerWidth - 280),
              background: panels.toolbar,
              border: `1px solid ${panels.border}`,
            }}
          >
            <div
              className="sketch-floating-wheel-header"
              style={{ color: panels.text }}
            >
              <span
                style={{
                  fontFamily: "Montserrat, sans-serif",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  letterSpacing: "0.04em",
                }}
              >
                Color
              </span>
              <button
                type="button"
                onClick={() => setShowFloatingWheel(false)}
                style={{
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  color: panels.textMuted,
                  display: "flex",
                }}
                data-ocid="sketch.floating_wheel.close_button"
              >
                <X size={14} />
              </button>
            </div>
            <ColorWheel
              size={200}
              onColorChange={(c) => {
                handleColorChange(c);
              }}
            />
            <div
              className="sketch-floating-swatch"
              style={{ background: color }}
            />
          </div>
        </>
      )}

      {/* ── CLEAR CONFIRM DIALOG ── */}
      {showClearConfirm && (
        <div className="sketch-dialog-overlay" data-ocid="sketch.dialog">
          <div
            className="sketch-dialog"
            style={{
              background: panels.toolbar,
              border: `1px solid ${panels.border}`,
              color: panels.text,
            }}
          >
            <div
              className="sketch-dialog-title"
              style={{ fontFamily: "Montserrat, sans-serif" }}
            >
              Clear canvas?
            </div>
            <div
              className="sketch-dialog-body"
              style={{ color: panels.textMuted }}
            >
              This cannot be undone.
            </div>
            <div className="sketch-dialog-actions">
              <button
                type="button"
                className="sketch-dialog-btn sketch-dialog-cancel"
                onClick={() => setShowClearConfirm(false)}
                style={{
                  border: `1px solid ${panels.border}`,
                  color: panels.text,
                }}
                data-ocid="sketch.clear.cancel_button"
              >
                Cancel
              </button>
              <button
                type="button"
                className="sketch-dialog-btn sketch-dialog-confirm"
                onClick={handleClearConfirm}
                data-ocid="sketch.clear.confirm_button"
              >
                Clear
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
