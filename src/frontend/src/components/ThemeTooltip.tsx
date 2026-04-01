import { useRef, useState } from "react";

interface ThemeTooltipProps {
  themeId: string;
  description: string;
}

export default function ThemeTooltip({
  themeId,
  description,
}: ThemeTooltipProps) {
  const [visible, setVisible] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const isBrutalist = themeId === "brutalist";

  const tooltipStyle: React.CSSProperties = isBrutalist
    ? {
        background: "#fbff29",
        color: "#000",
        border: "2px solid #000",
        fontWeight: 700,
        boxShadow: "none",
        borderRadius: "4px",
        padding: "6px 10px",
        fontSize: "11px",
        maxWidth: "200px",
        whiteSpace: "normal",
        lineHeight: 1.4,
        zIndex: 9999,
        position: "absolute",
        bottom: "calc(100% + 8px)",
        left: "50%",
        transform: "translateX(-50%)",
        pointerEvents: "none",
      }
    : {
        background: "#111827",
        color: "#fff",
        border: "none",
        fontWeight: 400,
        boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
        borderRadius: "8px",
        padding: "6px 10px",
        fontSize: "11px",
        maxWidth: "200px",
        whiteSpace: "normal",
        lineHeight: 1.4,
        zIndex: 9999,
        position: "absolute",
        bottom: "calc(100% + 8px)",
        left: "50%",
        transform: "translateX(-50%)",
        pointerEvents: "none",
      };

  const show = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setVisible(true);
  };

  const hide = () => {
    timerRef.current = setTimeout(() => setVisible(false), 150);
  };

  return (
    <span
      style={{
        position: "relative",
        display: "inline-flex",
        alignItems: "center",
      }}
      onMouseEnter={show}
      onMouseLeave={hide}
    >
      <button
        type="button"
        aria-label={`Info about ${themeId} theme`}
        onFocus={show}
        onBlur={hide}
        onTouchStart={(e) => {
          e.preventDefault();
          setVisible((v) => !v);
        }}
        style={{
          fontSize: "11px",
          opacity: 0.55,
          cursor: "pointer",
          userSelect: "none",
          lineHeight: 1,
          display: "inline-flex",
          alignItems: "center",
          marginLeft: "4px",
          background: "none",
          border: "none",
          padding: 0,
          color: "inherit",
        }}
      >
        ⓘ
      </button>
      {visible && (
        <span style={tooltipStyle}>
          {description}
          {!isBrutalist && (
            <span
              style={{
                position: "absolute",
                bottom: "-5px",
                left: "50%",
                transform: "translateX(-50%)",
                width: 0,
                height: 0,
                borderLeft: "5px solid transparent",
                borderRight: "5px solid transparent",
                borderTop: "5px solid #111827",
              }}
            />
          )}
        </span>
      )}
    </span>
  );
}
