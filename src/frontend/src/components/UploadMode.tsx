import {
  ArrowLeft,
  Crop,
  Download,
  ImagePlus,
  Moon,
  Sliders,
  Sun,
  ZoomIn,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  DESIGN_THEME_LABELS,
  type DesignTheme,
  type FidelityLevel,
  useSketchAnalysis,
} from "../hooks/useSketchAnalysis";
import StructureResult from "./StructureResult";

interface UploadModeProps {
  theme: "light" | "dark";
  toggleTheme: () => void;
  onClose: () => void;
  geminiKey: string;
  onOpenSettings: () => void;
}

type UploadTab = "upload" | "analyze" | "structure";
type UploadTool = "upload" | "crop" | "zoom" | "contrast";

export default function UploadMode({
  theme,
  toggleTheme,
  onClose,
  geminiKey,
  onOpenSettings,
}: UploadModeProps) {
  const [visible, setVisible] = useState(false);
  const [exiting, setExiting] = useState(false);
  const [activeTab, setActiveTab] = useState<UploadTab>("upload");
  const {
    loading: geminiLoading,
    error: geminiError,
    result: geminiResult,
    analyze: analyzeSketch,
    isEdgeMode,
  } = useSketchAnalysis();
  const [activeTool, setActiveTool] = useState<UploadTool>("upload");
  const [dragOver, setDragOver] = useState(false);
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [contrastValue, setContrastValue] = useState(100);
  const [edgesEnabled, setEdgesEnabled] = useState(false);
  const [designTheme, setDesignTheme] = useState<DesignTheme>("minimal");
  const [fidelityLevel, setFidelityLevel] = useState<FidelityLevel>("high");
  const [scanning, setScanning] = useState(false);
  const [structureReady, setStructureReady] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const raf = requestAnimationFrame(() => setVisible(true));
    return () => cancelAnimationFrame(raf);
  }, []);

  const handleClose = useCallback(() => {
    setExiting(true);
    setTimeout(() => onClose(), 280);
  }, [onClose]);

  const handleFile = useCallback((file: File) => {
    if (!file) return;
    const url = URL.createObjectURL(file);
    setUploadedImage(url);
    setActiveTab("analyze");
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleBrowse = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleStartStructuring = useCallback(() => {
    setActiveTab("structure");
    setScanning(true);
    setStructureReady(false);
    setTimeout(() => {
      setScanning(false);
      setStructureReady(true);
    }, 2500);
    // Convert uploaded image to base64 and call Gemini in parallel
    if (uploadedImage) {
      fetch(uploadedImage)
        .then((r) => r.blob())
        .then(
          (blob) =>
            new Promise<string>((resolve) => {
              const fr = new FileReader();
              fr.onload = () => resolve(fr.result as string);
              fr.readAsDataURL(blob);
            }),
        )
        .then((dataUrl) => {
          const mimeType =
            dataUrl.split(";")[0].replace("data:", "") || "image/jpeg";
          const base64 = dataUrl.replace(/^data:[^;]+;base64,/, "");
          const savedKey =
            localStorage.getItem("duiodle_gemini_key") || geminiKey;
          if (!savedKey.trim()) {
            alert(
              "Please click the Gear icon and add your Gemini API Key first!",
            );
            onOpenSettings();
            return;
          }
          analyzeSketch(base64, mimeType, designTheme, fidelityLevel);
        })
        .catch(() => {
          /* ignore fetch errors */
        });
    }
  }, [
    uploadedImage,
    analyzeSketch,
    geminiKey,
    onOpenSettings,
    designTheme,
    fidelityLevel,
  ]);

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

  const dropzoneBorder = dragOver
    ? "#fbff29"
    : theme === "dark"
      ? "#555"
      : "#ccc";

  const TOOLS: { id: UploadTool; label: string; icon: React.ReactNode }[] = [
    { id: "upload", label: "Upload", icon: <ImagePlus size={18} /> },
    { id: "crop", label: "Crop", icon: <Crop size={18} /> },
    { id: "zoom", label: "Zoom", icon: <ZoomIn size={18} /> },
    { id: "contrast", label: "Contrast", icon: <Sliders size={18} /> },
  ];

  const containerClass = `upload-mode-overlay${visible && !exiting ? " upload-mode-visible" : ""}${exiting ? " upload-mode-exiting" : ""}`;

  const showStructureResult =
    activeTab === "structure" && structureReady && !scanning;

  return (
    <div
      className={containerClass}
      style={{
        background: panels.bg,
        color: panels.text,
        fontFamily: "Karla, sans-serif",
      }}
      data-ocid="upload.modal"
    >
      {/* TOP TOOLBAR */}
      <div
        className="sketch-toolbar"
        style={{
          background: panels.toolbar,
          borderBottom: `1px solid ${panels.border}`,
          color: panels.text,
        }}
      >
        <div className="sketch-toolbar-left">
          <button
            type="button"
            className="sketch-toolbar-btn sketch-back-btn"
            onClick={handleClose}
            title="Back to home"
            data-ocid="upload.close_button"
            style={{ color: panels.text }}
          >
            <ArrowLeft size={16} />
            <span>Back</span>
          </button>
          <span
            style={{
              fontFamily: "Montserrat, sans-serif",
              fontWeight: 600,
              fontSize: "0.85rem",
              letterSpacing: "0.04em",
              color: panels.textMuted,
            }}
          >
            Upload Workspace
          </span>
        </div>

        <div className="sketch-mode-tabs">
          {(["upload", "analyze", "structure"] as UploadTab[]).map((tab) => (
            <button
              key={tab}
              type="button"
              className={`sketch-mode-tab${activeTab === tab ? " sketch-mode-tab-active" : ""}`}
              onClick={() => setActiveTab(tab)}
              data-ocid={`upload.${tab}.tab`}
              style={{ color: activeTab === tab ? "#111" : panels.textMuted }}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        <div className="sketch-toolbar-right">
          <button
            type="button"
            className="sketch-toolbar-btn"
            onClick={toggleTheme}
            title={theme === "light" ? "Switch to dark" : "Switch to light"}
            style={{ color: panels.text }}
            data-ocid="upload.theme.toggle"
          >
            {theme === "light" ? <Moon size={16} /> : <Sun size={16} />}
          </button>
          <button
            type="button"
            className={`sketch-toolbar-btn sketch-export-btn${!uploadedImage ? " sketch-export-disabled" : ""}`}
            disabled={!uploadedImage}
            title="Export"
            data-ocid="upload.export.button"
            style={{ opacity: uploadedImage ? 1 : 0.4 }}
          >
            <Download size={16} />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* MAIN BODY */}
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
                className={`sketch-tool-btn${activeTool === tool.id ? " sketch-tool-active" : ""}`}
                onClick={() => setActiveTool(tool.id)}
                aria-label={tool.label}
                data-ocid={`upload.${tool.id}.button`}
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
              </span>
            </div>
          ))}
        </div>

        {/* STRUCTURE RESULT — spans canvas + right panel */}
        {showStructureResult ? (
          <StructureResult
            theme={theme}
            panels={panels}
            onBack={() => {
              setStructureReady(false);
              setActiveTab("analyze");
            }}
            analysisData={geminiResult}
            isAnalyzing={geminiLoading}
            analysisError={geminiError}
            isEdgeMode={isEdgeMode}
          />
        ) : (
          <>
            {/* CENTER AREA */}
            <div className="sketch-canvas-area">
              {/* Upload dropzone — no image */}
              {!uploadedImage && activeTab === "upload" && (
                <div className="upload-center-wrap">
                  <div
                    className={`upload-dropzone${dragOver ? " drag-over" : ""}`}
                    style={{ borderColor: dropzoneBorder }}
                    onDragOver={(e) => {
                      e.preventDefault();
                      setDragOver(true);
                    }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={handleDrop}
                    data-ocid="upload.dropzone"
                  >
                    <div className="upload-dropzone-icon">
                      <ImagePlus
                        size={40}
                        strokeWidth={1.2}
                        color={theme === "dark" ? "#888" : "#999"}
                      />
                    </div>
                    <p
                      className="upload-dropzone-title"
                      style={{
                        fontFamily: "Montserrat, sans-serif",
                        color: panels.text,
                      }}
                    >
                      Drag &amp; Drop your Sketch
                    </p>
                    <p
                      className="upload-dropzone-sub"
                      style={{ color: panels.textMuted }}
                    >
                      or
                    </p>
                    <button
                      type="button"
                      className="upload-browse-btn"
                      onClick={handleBrowse}
                      data-ocid="upload.upload_button"
                    >
                      Browse Files
                    </button>
                    <p
                      className="upload-dropzone-formats"
                      style={{ color: panels.textMuted }}
                    >
                      Accepted: PNG · JPG · JPEG · PDF
                    </p>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".png,.jpg,.jpeg,.pdf"
                      style={{ display: "none" }}
                      onChange={handleFileChange}
                      data-ocid="upload.dropzone"
                    />
                  </div>
                </div>
              )}

              {/* Uploaded image preview */}
              {uploadedImage && activeTab === "analyze" && (
                <div className="upload-image-wrap">
                  <img
                    src={uploadedImage}
                    alt="Uploaded sketch"
                    className="upload-image-preview"
                    style={{ filter: `contrast(${contrastValue}%)` }}
                  />
                </div>
              )}

              {/* Structure scanning overlay */}
              {activeTab === "structure" && scanning && (
                <div className="sketch-scan-overlay">
                  <div className="sketch-scan-lines" />
                  <div className="sketch-scan-beam" />
                  <div
                    className="sketch-scan-text"
                    style={{ fontFamily: "Montserrat, sans-serif" }}
                  >
                    Interpreting layout structure
                    <span className="sketch-scan-dots">
                      <span>.</span>
                      <span>.</span>
                      <span>.</span>
                    </span>
                  </div>
                </div>
              )}

              {/* Show image under analyze if tab is not upload */}
              {uploadedImage && activeTab === "upload" && (
                <div className="upload-image-wrap">
                  <img
                    src={uploadedImage}
                    alt="Uploaded sketch"
                    className="upload-image-preview"
                  />
                </div>
              )}

              {/* Structure tab before structuring started */}
              {activeTab === "structure" && !scanning && !structureReady && (
                <div
                  className="sketch-placeholder-view"
                  style={{ color: panels.textMuted }}
                >
                  <div className="sketch-placeholder-icon">📋</div>
                  <div
                    className="sketch-placeholder-title"
                    style={{
                      color: panels.text,
                      fontFamily: "Montserrat, sans-serif",
                    }}
                  >
                    Ready to Structure
                  </div>
                  <div className="sketch-placeholder-sub">
                    Use the right panel to start structuring your uploaded
                    image.
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
              {!uploadedImage ? (
                <>
                  <div className="sketch-panel-section">
                    <div
                      className="sketch-panel-label"
                      style={{
                        fontFamily: "Montserrat, sans-serif",
                        color: panels.text,
                        fontWeight: 700,
                        fontSize: "0.9rem",
                      }}
                    >
                      Upload Info
                    </div>
                  </div>
                  <div className="sketch-panel-section">
                    <p
                      style={{
                        color: panels.textMuted,
                        fontSize: "0.82rem",
                        lineHeight: 1.6,
                      }}
                    >
                      Drop a sketch to begin analysis.
                    </p>
                  </div>
                  <div className="sketch-panel-section">
                    <div
                      className="sketch-panel-label"
                      style={{ color: panels.textMuted }}
                    >
                      Accepted Formats
                    </div>
                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: 6,
                        marginTop: 8,
                      }}
                    >
                      {["PNG", "JPG", "JPEG", "PDF"].map((fmt) => (
                        <div
                          key={fmt}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: 8,
                            color: panels.text,
                            fontSize: "0.8rem",
                          }}
                        >
                          <span
                            style={{
                              width: 6,
                              height: 6,
                              borderRadius: "50%",
                              background: "#fbff29",
                              flexShrink: 0,
                              display: "inline-block",
                            }}
                          />
                          {fmt}
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div className="sketch-panel-section">
                    <div
                      className="sketch-panel-label"
                      style={{
                        fontFamily: "Montserrat, sans-serif",
                        color: panels.text,
                        fontWeight: 700,
                        fontSize: "0.9rem",
                      }}
                    >
                      Image Analysis
                    </div>
                  </div>

                  {/* Detect Edges toggle */}
                  <div className="sketch-panel-section">
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                      }}
                    >
                      <span style={{ color: panels.text, fontSize: "0.82rem" }}>
                        Detect Edges
                      </span>
                      <button
                        type="button"
                        onClick={() => setEdgesEnabled((v) => !v)}
                        data-ocid="upload.edges.toggle"
                        style={{
                          width: 36,
                          height: 20,
                          borderRadius: 10,
                          border: "none",
                          background: edgesEnabled ? "#fbff29" : panels.border,
                          cursor: "pointer",
                          position: "relative",
                          transition: "background 200ms",
                          flexShrink: 0,
                        }}
                        aria-label="Toggle edge detection"
                      >
                        <span
                          style={{
                            position: "absolute",
                            top: 3,
                            left: edgesEnabled ? 18 : 3,
                            width: 14,
                            height: 14,
                            borderRadius: "50%",
                            background: edgesEnabled ? "#111" : "#fff",
                            transition: "left 200ms",
                          }}
                        />
                      </button>
                    </div>
                  </div>

                  {/* Contrast slider */}
                  <div className="sketch-panel-section">
                    <div
                      className="sketch-panel-label"
                      style={{ color: panels.textMuted }}
                    >
                      Adjust Contrast{" "}
                      <span style={{ color: panels.text }}>
                        {contrastValue}%
                      </span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={200}
                      value={contrastValue}
                      onChange={(e) => setContrastValue(Number(e.target.value))}
                      className="sketch-slider"
                      data-ocid="upload.contrast.input"
                    />
                  </div>

                  {/* Crop tool */}
                  <div className="sketch-panel-section">
                    <button
                      type="button"
                      onClick={() => setActiveTool("crop")}
                      data-ocid="upload.crop.button"
                      style={{
                        width: "100%",
                        padding: "8px 12px",
                        borderRadius: 6,
                        border: `1px solid ${panels.border}`,
                        background:
                          activeTool === "crop"
                            ? "rgba(251,255,41,0.15)"
                            : "transparent",
                        color: panels.text,
                        cursor: "pointer",
                        fontSize: "0.82rem",
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                        fontFamily: "Karla, sans-serif",
                      }}
                    >
                      <Crop size={14} />
                      Crop Tool
                    </button>
                  </div>

                  <div style={{ flex: 1 }} />

                  {/* Divider */}
                  <div
                    className="sketch-panel-divider"
                    style={{ background: panels.border, margin: "12px 0" }}
                  />

                  {/* Style: Design Theme + Fidelity */}
                  <div className="sketch-panel-section">
                    <div
                      className="sketch-panel-label"
                      style={{ color: panels.textMuted }}
                    >
                      Design Theme
                    </div>
                    <select
                      value={designTheme}
                      onChange={(e) =>
                        setDesignTheme(e.target.value as DesignTheme)
                      }
                      data-ocid="upload.theme.select"
                      style={{
                        width: "100%",
                        padding: "6px 8px",
                        borderRadius: 6,
                        border: `1px solid ${panels.border}`,
                        background: "transparent",
                        color: panels.text,
                        fontSize: "0.82rem",
                        fontFamily: "Karla, sans-serif",
                        cursor: "pointer",
                      }}
                    >
                      {(
                        Object.entries(DESIGN_THEME_LABELS) as [
                          DesignTheme,
                          string,
                        ][]
                      ).map(([id, label]) => (
                        <option
                          key={id}
                          value={id}
                          style={{
                            background: theme === "dark" ? "#1a1a1a" : "#fff",
                          }}
                        >
                          {label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="sketch-panel-section">
                    <div
                      className="sketch-panel-label"
                      style={{ color: panels.textMuted }}
                    >
                      Fidelity
                    </div>
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                      {(["high", "medium", "low"] as FidelityLevel[]).map(
                        (f) => (
                          <button
                            key={f}
                            type="button"
                            data-ocid={`upload.fidelity.${f}.toggle`}
                            onClick={() => setFidelityLevel(f)}
                            style={{
                              flex: "1 1 28%",
                              padding: "5px 4px",
                              borderRadius: 6,
                              border: `1px solid ${fidelityLevel === f ? "#fbff29" : panels.border}`,
                              background:
                                fidelityLevel === f
                                  ? "rgba(251,255,41,0.12)"
                                  : "transparent",
                              color:
                                fidelityLevel === f
                                  ? "#fbff29"
                                  : panels.textMuted,
                              fontSize: "0.75rem",
                              fontFamily: "Karla, sans-serif",
                              cursor: "pointer",
                              transition: "all 150ms",
                            }}
                          >
                            {f === "high"
                              ? "High"
                              : f === "medium"
                                ? "Medium"
                                : "Low"}
                          </button>
                        ),
                      )}
                    </div>
                    <div
                      style={{
                        fontSize: "0.7rem",
                        color: panels.textMuted,
                        marginTop: 4,
                      }}
                    >
                      {fidelityLevel === "high"
                        ? "Production-ready + Framer Motion"
                        : fidelityLevel === "medium"
                          ? "Static mockup with real styles"
                          : "Wireframe only"}
                    </div>
                  </div>

                  {/* Start Structuring */}
                  <div className="sketch-panel-section">
                    <button
                      type="button"
                      className="upload-structure-btn"
                      onClick={handleStartStructuring}
                      data-ocid="upload.primary_button"
                    >
                      Start Structuring
                    </button>
                  </div>
                </>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
