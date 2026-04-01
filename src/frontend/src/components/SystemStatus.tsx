import { useCallback, useEffect, useRef, useState } from "react";
import { useActor } from "../hooks/useActor";

type Status = "checking" | "running" | "stopped";

export default function SystemStatus() {
  const { actor, isFetching } = useActor();
  const [status, setStatus] = useState<Status>("checking");
  const [waking, setWaking] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const checkHealth = useCallback(async () => {
    if (!actor) return;
    try {
      const res = await (
        actor as unknown as { healthCheck: () => Promise<string> }
      ).healthCheck();
      if (typeof res === "string") {
        setStatus("running");
      }
    } catch {
      setStatus("stopped");
    }
  }, [actor]);

  const handleWakeUp = useCallback(async () => {
    setWaking(true);
    let attempts = 0;
    const poll = async () => {
      attempts++;
      try {
        const res = await (
          actor as unknown as { healthCheck: () => Promise<string> }
        ).healthCheck();
        if (typeof res === "string") {
          setStatus("running");
          setWaking(false);
          return;
        }
      } catch {
        // still stopped
      }
      if (attempts < 6) {
        setTimeout(poll, 5000);
      } else {
        setWaking(false);
      }
    };
    poll();
  }, [actor]);

  useEffect(() => {
    if (isFetching || !actor) return;
    checkHealth();
    const delay = status === "stopped" ? 5000 : 30000;
    intervalRef.current = setInterval(checkHealth, delay);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [actor, isFetching, checkHealth, status]);

  const dotColor =
    status === "running"
      ? "#22c55e"
      : status === "stopped"
        ? "#ef4444"
        : "#eab308";

  const label =
    status === "running"
      ? "Backend Running on ICP"
      : status === "stopped"
        ? "Canister Stopped"
        : "Connecting to ICP...";

  return (
    <div
      data-ocid="system_status.panel"
      style={{
        position: "fixed",
        bottom: "16px",
        left: "16px",
        zIndex: 40,
        display: "flex",
        alignItems: "center",
        gap: "8px",
        background: "rgba(13,7,22,0.88)",
        border: "1px solid rgba(255,255,255,0.08)",
        borderRadius: "24px",
        padding: "6px 12px 6px 8px",
        backdropFilter: "blur(12px)",
        boxShadow: "0 2px 16px rgba(0,0,0,0.4)",
      }}
    >
      {/* Pulsing dot */}
      <span
        data-ocid="system_status.toggle"
        style={{
          position: "relative",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          width: "14px",
          height: "14px",
        }}
      >
        <span
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: "50%",
            background: dotColor,
            opacity: 0.25,
            animation: "sys-ping 1.4s cubic-bezier(0,0,0.2,1) infinite",
          }}
        />
        <span
          style={{
            position: "relative",
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            background: dotColor,
            flexShrink: 0,
          }}
        />
      </span>

      <span
        style={{
          fontSize: "11px",
          color: "rgba(255,255,255,0.7)",
          fontFamily: "Karla, sans-serif",
          letterSpacing: "0.02em",
          whiteSpace: "nowrap",
        }}
      >
        {label}
      </span>

      {status === "stopped" && (
        <button
          type="button"
          data-ocid="system_status.primary_button"
          onClick={handleWakeUp}
          disabled={waking}
          title="Run ./demo-prepare.sh to restart the canister, then click to re-check"
          style={{
            marginLeft: "4px",
            padding: "2px 8px",
            background: "rgba(251,255,41,0.12)",
            border: "1px solid rgba(251,255,41,0.4)",
            borderRadius: "12px",
            color: "#fbff29",
            fontSize: "10.5px",
            fontFamily: "Karla, sans-serif",
            cursor: waking ? "not-allowed" : "pointer",
            opacity: waking ? 0.6 : 1,
            transition: "all 0.2s",
            whiteSpace: "nowrap",
          }}
        >
          {waking ? "Checking..." : "Wake Up"}
        </button>
      )}

      <style>{`
        @keyframes sys-ping {
          75%, 100% { transform: scale(2.2); opacity: 0; }
        }
      `}</style>
    </div>
  );
}
