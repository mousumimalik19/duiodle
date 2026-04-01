import { useCallback, useEffect, useRef } from "react";

interface ColorWheelProps {
  size?: number;
  onColorChange: (color: string) => void;
  className?: string;
}

function hslToHex(h: number, s: number, l: number): string {
  const sn = s / 100;
  const ln = l / 100;
  const a = sn * Math.min(ln, 1 - ln);
  const f = (n: number) => {
    const k = (n + h / 30) % 12;
    const color = ln - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
    return Math.round(255 * color)
      .toString(16)
      .padStart(2, "0");
  };
  return `#${f(0)}${f(8)}${f(4)}`;
}

export default function ColorWheel({
  size = 180,
  onColorChange,
  className,
}: ColorWheelProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const selDotRef = useRef<{ x: number; y: number } | null>(null);
  const isDragging = useRef(false);

  const drawWheel = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const cx = size / 2;
    const cy = size / 2;
    const radius = size / 2 - 4;

    const imageData = ctx.createImageData(size, size);

    for (let py = 0; py < size; py++) {
      for (let px = 0; px < size; px++) {
        const dx = px - cx;
        const dy = py - cy;
        const dist = Math.sqrt(dx * dx + dy * dy);

        const idx = (py * size + px) * 4;

        if (dist > radius) {
          imageData.data[idx + 3] = 0;
          continue;
        }

        const angle = (Math.atan2(dy, dx) * 180) / Math.PI + 180;
        const sat = dist / radius;

        const h = angle;
        const s = sat;
        const l = 0.5;
        const c = (1 - Math.abs(2 * l - 1)) * s;
        const x2 = c * (1 - Math.abs(((h / 60) % 2) - 1));
        const m = l - c / 2;
        let r = 0;
        let g = 0;
        let b = 0;
        if (h < 60) {
          r = c;
          g = x2;
          b = 0;
        } else if (h < 120) {
          r = x2;
          g = c;
          b = 0;
        } else if (h < 180) {
          r = 0;
          g = c;
          b = x2;
        } else if (h < 240) {
          r = 0;
          g = x2;
          b = c;
        } else if (h < 300) {
          r = x2;
          g = 0;
          b = c;
        } else {
          r = c;
          g = 0;
          b = x2;
        }

        imageData.data[idx] = Math.round((r + m) * 255);
        imageData.data[idx + 1] = Math.round((g + m) * 255);
        imageData.data[idx + 2] = Math.round((b + m) * 255);
        imageData.data[idx + 3] = 255;
      }
    }

    ctx.putImageData(imageData, 0, 0);

    if (selDotRef.current) {
      const { x, y } = selDotRef.current;
      ctx.beginPath();
      ctx.arc(x, y, 7, 0, Math.PI * 2);
      ctx.strokeStyle = "white";
      ctx.lineWidth = 2.5;
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(x, y, 7, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(0,0,0,0.5)";
      ctx.lineWidth = 1;
      ctx.stroke();
    }
  }, [size]);

  useEffect(() => {
    drawWheel();
  }, [drawWheel]);

  const pickColorAt = useCallback(
    (clientX: number, clientY: number) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      const scaleX = size / rect.width;
      const scaleY = size / rect.height;
      const x = (clientX - rect.left) * scaleX;
      const y = (clientY - rect.top) * scaleY;

      const cx = size / 2;
      const cy = size / 2;
      const radius = size / 2 - 4;
      const dx = x - cx;
      const dy = y - cy;
      if (Math.sqrt(dx * dx + dy * dy) > radius) return;

      const angle = (Math.atan2(dy, dx) * 180) / Math.PI + 180;
      const sat = Math.sqrt(dx * dx + dy * dy) / radius;
      const hex = hslToHex(angle, sat * 100, 50);
      selDotRef.current = { x, y };
      drawWheel();
      onColorChange(hex);
    },
    [size, drawWheel, onColorChange],
  );

  return (
    <canvas
      ref={canvasRef}
      width={size}
      height={size}
      onMouseDown={(e) => {
        isDragging.current = true;
        pickColorAt(e.clientX, e.clientY);
      }}
      onMouseMove={(e) => {
        if (isDragging.current) pickColorAt(e.clientX, e.clientY);
      }}
      onMouseUp={() => {
        isDragging.current = false;
      }}
      onMouseLeave={() => {
        isDragging.current = false;
      }}
      className={className}
      style={{ borderRadius: "50%", cursor: "crosshair", display: "block" }}
    />
  );
}
