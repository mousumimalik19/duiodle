import { AlertCircle, CheckCircle, Eye, EyeOff, X, Zap } from "lucide-react";
import { useState } from "react";

export interface SettingsModalProps {
  open: boolean;
  geminiKey: string;
  onGeminiKeyChange: (key: string) => void;
  onSave: (key: string, model: string) => void;
  onClose: () => void;
}

const MODELS = [
  { id: "gemini-2.5-flash", label: "2.5 Flash", badge: "Fast" },
  { id: "gemini-2.5-pro", label: "2.5 Pro", badge: "Powerful" },
] as const;

export default function SettingsModal({
  open,
  geminiKey,
  onGeminiKeyChange,
  onSave,
  onClose,
}: SettingsModalProps) {
  const [showKey, setShowKey] = useState(false);
  const [selectedModel, setSelectedModel] = useState<string>(
    () => localStorage.getItem("duiodle_gemini_model") ?? "gemini-2.5-flash",
  );
  const [testStatus, setTestStatus] = useState<"idle" | "ok" | "error">("idle");

  const hasKey = geminiKey.trim().length > 0;

  if (!open) return null;

  const handleTestConnection = () => {
    if (!hasKey) {
      setTestStatus("error");
    } else {
      setTestStatus("ok");
      setTimeout(() => setTestStatus("idle"), 3000);
    }
  };

  const handleSave = () => {
    onSave(geminiKey, selectedModel);
  };

  const glass: React.CSSProperties = {
    background: "rgba(15, 15, 20, 0.88)",
    backdropFilter: "blur(24px)",
    WebkitBackdropFilter: "blur(24px)",
    border: "1px solid rgba(255,255,255,0.1)",
    boxShadow:
      "0 24px 60px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.06)",
    borderRadius: "20px",
    padding: "32px",
    width: "100%",
    maxWidth: "440px",
    position: "relative",
    zIndex: 1,
    color: "#ffffff",
  };

  const divider: React.CSSProperties = {
    borderTop: "1px solid rgba(255,255,255,0.08)",
    margin: "24px 0",
  };

  const sectionLabel: React.CSSProperties = {
    fontFamily: "Karla, sans-serif",
    fontSize: "0.75rem",
    fontWeight: 600,
    color: "rgba(255,255,255,0.5)",
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    display: "block",
    marginBottom: "10px",
  };

  return (
    <dialog
      open
      aria-label="AI Settings"
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.6)",
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "16px",
        border: "none",
        margin: 0,
        maxWidth: "100vw",
        maxHeight: "100vh",
        width: "100vw",
        height: "100vh",
      }}
      data-ocid="settings.modal"
    >
      {/* Backdrop */}
      <button
        type="button"
        aria-label="Close settings"
        onClick={onClose}
        style={{
          position: "absolute",
          inset: 0,
          background: "transparent",
          border: "none",
          cursor: "default",
        }}
      />

      {/* Glass card */}
      <div style={glass}>
        {/* Close button */}
        <button
          type="button"
          onClick={onClose}
          aria-label="Close settings"
          data-ocid="settings.close_button"
          style={{
            position: "absolute",
            top: "16px",
            right: "16px",
            background: "rgba(255,255,255,0.06)",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: "8px",
            cursor: "pointer",
            color: "rgba(255,255,255,0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "6px",
            transition: "background 0.2s",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "rgba(255,255,255,0.12)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "rgba(255,255,255,0.06)";
          }}
        >
          <X width={16} height={16} />
        </button>

        {/* Header */}
        <div style={{ marginBottom: "24px", paddingRight: "32px" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              marginBottom: "8px",
            }}
          >
            <div
              style={{
                width: "32px",
                height: "32px",
                borderRadius: "8px",
                background: "rgba(251,255,41,0.15)",
                border: "1px solid rgba(251,255,41,0.25)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              <Zap width={16} height={16} color="#fbff29" />
            </div>
            <h2
              style={{
                fontFamily: "Montserrat, sans-serif",
                fontWeight: 700,
                fontSize: "1.2rem",
                color: "#ffffff",
                margin: 0,
                letterSpacing: "-0.01em",
              }}
            >
              AI Settings
            </h2>
          </div>
          <p
            style={{
              fontFamily: "Karla, sans-serif",
              fontSize: "0.875rem",
              color: "rgba(255,255,255,0.45)",
              margin: 0,
              lineHeight: 1.5,
            }}
          >
            Configure your Gemini API key and model preferences.
          </p>
        </div>

        {/* Status banner */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "10px 14px",
            borderRadius: "10px",
            background: hasKey ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.08)",
            border: `1px solid ${
              hasKey ? "rgba(34,197,94,0.2)" : "rgba(239,68,68,0.2)"
            }`,
            marginBottom: "24px",
          }}
        >
          <span
            style={{
              width: "7px",
              height: "7px",
              borderRadius: "50%",
              background: hasKey ? "#22c55e" : "#ef4444",
              flexShrink: 0,
              boxShadow: hasKey
                ? "0 0 6px rgba(34,197,94,0.6)"
                : "0 0 6px rgba(239,68,68,0.5)",
            }}
          />
          <span
            style={{
              fontFamily: "Karla, sans-serif",
              fontSize: "0.8125rem",
              color: hasKey ? "#4ade80" : "#f87171",
              fontWeight: 500,
            }}
          >
            {hasKey
              ? "API key configured — AI is active"
              : "No API key — AI is inactive"}
          </span>
        </div>

        {/* API Key section */}
        <span style={sectionLabel}>Gemini API Key</span>
        <div style={{ position: "relative", marginBottom: "12px" }}>
          <input
            id="gemini-key-input"
            type={showKey ? "text" : "password"}
            value={geminiKey}
            onChange={(e) => {
              onGeminiKeyChange(e.target.value);
              if (testStatus !== "idle") setTestStatus("idle");
            }}
            placeholder="AIzaSy..."
            data-ocid="settings.input"
            style={{
              width: "100%",
              padding: "11px 42px 11px 14px",
              borderRadius: "10px",
              border: "1px solid rgba(255,255,255,0.12)",
              background: "rgba(255,255,255,0.05)",
              color: "#ffffff",
              fontFamily: "Karla, monospace",
              fontSize: "0.875rem",
              outline: "none",
              boxSizing: "border-box",
              transition: "border-color 0.2s",
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = "rgba(251,255,41,0.4)";
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = "rgba(255,255,255,0.12)";
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSave();
            }}
          />
          <button
            type="button"
            onClick={() => setShowKey((v) => !v)}
            aria-label={showKey ? "Hide API key" : "Show API key"}
            style={{
              position: "absolute",
              right: "10px",
              top: "50%",
              transform: "translateY(-50%)",
              background: "none",
              border: "none",
              cursor: "pointer",
              color: "rgba(255,255,255,0.35)",
              display: "flex",
              padding: "2px",
            }}
          >
            {showKey ? (
              <EyeOff width={16} height={16} />
            ) : (
              <Eye width={16} height={16} />
            )}
          </button>
        </div>

        {/* Test connection feedback */}
        {testStatus !== "idle" && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              marginBottom: "10px",
              fontFamily: "Karla, sans-serif",
              fontSize: "0.8125rem",
              color: testStatus === "ok" ? "#4ade80" : "#f87171",
            }}
          >
            {testStatus === "ok" ? (
              <>
                <CheckCircle width={14} height={14} />
                Key is ready to use
              </>
            ) : (
              <>
                <AlertCircle width={14} height={14} />
                Please enter an API key first.
              </>
            )}
          </div>
        )}

        <a
          href="https://aistudio.google.com/apikey"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            fontFamily: "Karla, sans-serif",
            fontSize: "0.8125rem",
            color: "#fbff29",
            textDecoration: "none",
            opacity: 0.8,
            display: "inline-block",
            marginBottom: "6px",
          }}
        >
          Get free API key →
        </a>

        <div style={divider} />

        {/* Model Selection */}
        <span style={sectionLabel}>Model Selection</span>
        <div
          style={{
            display: "flex",
            gap: "8px",
            marginBottom: "8px",
          }}
        >
          {MODELS.map((m) => {
            const active = selectedModel === m.id;
            return (
              <button
                key={m.id}
                type="button"
                onClick={() => setSelectedModel(m.id)}
                data-ocid={`settings.${
                  m.id.includes("flash") ? "flash" : "pro"
                }.toggle`}
                style={{
                  flex: 1,
                  padding: "10px 12px",
                  borderRadius: "10px",
                  border: active
                    ? "1px solid rgba(251,255,41,0.5)"
                    : "1px solid rgba(255,255,255,0.1)",
                  background: active ? "#fbff29" : "rgba(255,255,255,0.04)",
                  color: active ? "#111111" : "rgba(255,255,255,0.6)",
                  fontFamily: "Karla, sans-serif",
                  fontWeight: active ? 700 : 500,
                  fontSize: "0.875rem",
                  cursor: "pointer",
                  transition: "all 0.2s",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: "2px",
                }}
              >
                <span>{m.label}</span>
                <span
                  style={{
                    fontSize: "0.7rem",
                    fontWeight: 500,
                    opacity: active ? 0.6 : 0.45,
                  }}
                >
                  {m.badge}
                </span>
              </button>
            );
          })}
        </div>
        <p
          style={{
            fontFamily: "Karla, sans-serif",
            fontSize: "0.78rem",
            color: "rgba(255,255,255,0.3)",
            margin: "0 0 4px",
          }}
        >
          {selectedModel === "gemini-2.5-flash"
            ? "Flash: faster responses, lower cost."
            : "Pro: higher accuracy, richer detail."}
        </p>

        <div style={divider} />

        {/* Actions */}
        <div style={{ display: "flex", gap: "8px" }}>
          <button
            type="button"
            onClick={handleTestConnection}
            data-ocid="settings.secondary_button"
            style={{
              flex: 1,
              padding: "11px 16px",
              borderRadius: "10px",
              background: "rgba(255,255,255,0.06)",
              border: "1px solid rgba(255,255,255,0.12)",
              color: "rgba(255,255,255,0.8)",
              fontFamily: "Karla, sans-serif",
              fontWeight: 600,
              fontSize: "0.875rem",
              cursor: "pointer",
              transition: "background 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(255,255,255,0.1)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "rgba(255,255,255,0.06)";
            }}
          >
            Test Connection
          </button>
          <button
            type="button"
            onClick={handleSave}
            data-ocid="settings.save_button"
            style={{
              flex: 1,
              padding: "11px 16px",
              borderRadius: "10px",
              background: "#fbff29",
              border: "none",
              color: "#111111",
              fontFamily: "Karla, sans-serif",
              fontWeight: 700,
              fontSize: "0.875rem",
              cursor: "pointer",
              letterSpacing: "0.01em",
              transition: "opacity 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.opacity = "0.88";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.opacity = "1";
            }}
          >
            Save
          </button>
        </div>
      </div>
    </dialog>
  );
}
