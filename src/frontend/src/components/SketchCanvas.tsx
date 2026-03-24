import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
} from "react";

export type DrawTool =
  | "cursor"
  | "brush"
  | "rect"
  | "circle"
  | "button-shape"
  | "text"
  | "eraser";

interface SketchCanvasProps {
  tool: DrawTool;
  color: string;
  brushSize: number;
  opacity: number;
  theme: "light" | "dark";
  zoom: number;
  onZoomChange: (zoom: number) => void;
}

export interface SketchCanvasHandle {
  undo: () => void;
  redo: () => void;
  clear: () => void;
  exportPNG: () => void;
}

const GRID_SIZE = 20;
const MAX_HISTORY = 50;
const BG_LIGHT = "#ffffff";
const BG_DARK = "#1a1a1a";

const SketchCanvas = forwardRef<SketchCanvasHandle, SketchCanvasProps>(
  (props, ref) => {
    const { tool, color, brushSize, opacity, theme, zoom, onZoomChange } =
      props;

    const containerRef = useRef<HTMLDivElement>(null);
    const bgCanvasRef = useRef<HTMLCanvasElement>(null);
    const drawCanvasRef = useRef<HTMLCanvasElement>(null);

    // Refs to avoid stale closures in event handlers
    const toolRef = useRef(tool);
    const colorRef = useRef(color);
    const brushSizeRef = useRef(brushSize);
    const opacityRef = useRef(opacity);
    const themeRef = useRef(theme);
    const zoomRef = useRef(zoom);

    useEffect(() => {
      toolRef.current = tool;
    }, [tool]);
    useEffect(() => {
      colorRef.current = color;
    }, [color]);
    useEffect(() => {
      brushSizeRef.current = brushSize;
    }, [brushSize]);
    useEffect(() => {
      opacityRef.current = opacity;
    }, [opacity]);
    useEffect(() => {
      zoomRef.current = zoom;
    }, [zoom]);

    // Undo/redo history
    const historyRef = useRef<ImageData[]>([]);
    const historyIndexRef = useRef(-1);

    // Drawing state
    const isDrawingRef = useRef(false);
    const pointsRef = useRef<{ x: number; y: number }[]>([]);
    const shapeStartRef = useRef({ x: 0, y: 0 });
    const previewBaseRef = useRef<ImageData | null>(null);

    const drawGrid = useCallback(() => {
      const canvas = bgCanvasRef.current;
      if (!canvas || canvas.width === 0) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const bg = themeRef.current === "dark" ? BG_DARK : BG_LIGHT;
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      ctx.fillStyle =
        themeRef.current === "dark"
          ? "rgba(255,255,255,0.04)"
          : "rgba(0,0,0,0.05)";
      for (let x = GRID_SIZE; x < canvas.width; x += GRID_SIZE) {
        for (let y = GRID_SIZE; y < canvas.height; y += GRID_SIZE) {
          ctx.beginPath();
          ctx.arc(x, y, 1, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }, []);

    const saveHistory = useCallback(() => {
      const canvas = drawCanvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      historyRef.current = historyRef.current.slice(
        0,
        historyIndexRef.current + 1,
      );
      historyRef.current.push(imageData);
      if (historyRef.current.length > MAX_HISTORY) {
        historyRef.current.shift();
      } else {
        historyIndexRef.current++;
      }
    }, []);

    const undo = useCallback(() => {
      const canvas = drawCanvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      if (historyIndexRef.current > 0) {
        historyIndexRef.current--;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.putImageData(historyRef.current[historyIndexRef.current], 0, 0);
      } else if (historyIndexRef.current === 0) {
        historyIndexRef.current = -1;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    }, []);

    const redo = useCallback(() => {
      const canvas = drawCanvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      if (historyIndexRef.current < historyRef.current.length - 1) {
        historyIndexRef.current++;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.putImageData(historyRef.current[historyIndexRef.current], 0, 0);
      }
    }, []);

    const clear = useCallback(() => {
      const canvas = drawCanvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      saveHistory();
    }, [saveHistory]);

    const exportPNG = useCallback(() => {
      const bgCanvas = bgCanvasRef.current;
      const drawCanvas = drawCanvasRef.current;
      if (!bgCanvas || !drawCanvas) return;
      const exportCanvas = document.createElement("canvas");
      exportCanvas.width = bgCanvas.width;
      exportCanvas.height = bgCanvas.height;
      const ctx = exportCanvas.getContext("2d");
      if (!ctx) return;
      ctx.drawImage(bgCanvas, 0, 0);
      ctx.drawImage(drawCanvas, 0, 0);
      const link = document.createElement("a");
      link.download = "sketch.png";
      link.href = exportCanvas.toDataURL("image/png");
      link.click();
    }, []);

    useImperativeHandle(ref, () => ({ undo, redo, clear, exportPNG }), [
      undo,
      redo,
      clear,
      exportPNG,
    ]);

    // Init / resize canvases
    const initCanvases = useCallback(() => {
      const container = containerRef.current;
      const bgCanvas = bgCanvasRef.current;
      const drawCanvas = drawCanvasRef.current;
      if (!container || !bgCanvas || !drawCanvas) return;

      let savedData: ImageData | null = null;
      const drawCtx = drawCanvas.getContext("2d");
      if (drawCtx && drawCanvas.width > 0 && drawCanvas.height > 0) {
        savedData = drawCtx.getImageData(
          0,
          0,
          drawCanvas.width,
          drawCanvas.height,
        );
      }

      const w = container.clientWidth;
      const h = container.clientHeight;
      bgCanvas.width = w;
      bgCanvas.height = h;
      drawCanvas.width = w;
      drawCanvas.height = h;

      drawGrid();

      if (savedData && drawCtx) {
        drawCtx.putImageData(savedData, 0, 0);
      }
      historyRef.current = [];
      historyIndexRef.current = -1;
    }, [drawGrid]);

    useEffect(() => {
      const container = containerRef.current;
      if (!container) return;
      const observer = new ResizeObserver(() => {
        initCanvases();
      });
      observer.observe(container);
      return () => observer.disconnect();
    }, [initCanvases]);

    // Theme change: redraw background, keep drawings
    useEffect(() => {
      themeRef.current = theme;
      drawGrid();
    }, [theme, drawGrid]);

    const getCanvasPos = useCallback((e: React.MouseEvent | MouseEvent) => {
      const canvas = drawCanvasRef.current;
      if (!canvas) return { x: 0, y: 0 };
      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;
      return {
        x: (e.clientX - rect.left) * scaleX,
        y: (e.clientY - rect.top) * scaleY,
      };
    }, []);

    const onMouseDown = useCallback(
      (e: React.MouseEvent<HTMLCanvasElement>) => {
        if (toolRef.current === "cursor") return;
        const pos = getCanvasPos(e);
        const canvas = drawCanvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        isDrawingRef.current = true;
        const t = toolRef.current;

        if (t === "brush") {
          pointsRef.current = [pos];
          ctx.globalAlpha = opacityRef.current / 100;
          ctx.globalCompositeOperation = "source-over";
          ctx.strokeStyle = colorRef.current;
          ctx.lineWidth = brushSizeRef.current;
          ctx.lineCap = "round";
          ctx.lineJoin = "round";
          ctx.beginPath();
          ctx.moveTo(pos.x, pos.y);
        } else if (t === "eraser") {
          pointsRef.current = [pos];
          ctx.globalCompositeOperation = "destination-out";
          ctx.globalAlpha = 1;
          ctx.lineWidth = brushSizeRef.current * 2.5;
          ctx.lineCap = "round";
          ctx.lineJoin = "round";
        } else if (t === "rect" || t === "circle" || t === "button-shape") {
          shapeStartRef.current = pos;
          previewBaseRef.current = ctx.getImageData(
            0,
            0,
            canvas.width,
            canvas.height,
          );
        } else if (t === "text") {
          ctx.globalAlpha = opacityRef.current / 100;
          ctx.globalCompositeOperation = "source-over";
          ctx.fillStyle = colorRef.current;
          ctx.font = `${brushSizeRef.current + 12}px Karla, sans-serif`;
          ctx.fillText("Text", pos.x, pos.y);
          saveHistory();
          isDrawingRef.current = false;
        }
      },
      [getCanvasPos, saveHistory],
    );

    const onMouseMove = useCallback(
      (e: React.MouseEvent<HTMLCanvasElement>) => {
        if (!isDrawingRef.current) return;
        const pos = getCanvasPos(e);
        const canvas = drawCanvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;
        const t = toolRef.current;

        if (t === "brush") {
          pointsRef.current.push(pos);
          const pts = pointsRef.current;
          ctx.globalAlpha = opacityRef.current / 100;
          ctx.globalCompositeOperation = "source-over";
          ctx.strokeStyle = colorRef.current;
          ctx.lineWidth = brushSizeRef.current;
          ctx.lineCap = "round";
          ctx.lineJoin = "round";

          if (pts.length >= 3) {
            const n = pts.length;
            const mid = {
              x: (pts[n - 2].x + pts[n - 1].x) / 2,
              y: (pts[n - 2].y + pts[n - 1].y) / 2,
            };
            const prevMid = {
              x: (pts[n - 3].x + pts[n - 2].x) / 2,
              y: (pts[n - 3].y + pts[n - 2].y) / 2,
            };
            ctx.beginPath();
            ctx.moveTo(prevMid.x, prevMid.y);
            ctx.quadraticCurveTo(pts[n - 2].x, pts[n - 2].y, mid.x, mid.y);
            ctx.stroke();
          } else if (pts.length === 2) {
            ctx.beginPath();
            ctx.moveTo(pts[0].x, pts[0].y);
            ctx.lineTo(pts[1].x, pts[1].y);
            ctx.stroke();
          }
        } else if (t === "eraser") {
          pointsRef.current.push(pos);
          const pts = pointsRef.current;
          ctx.globalCompositeOperation = "destination-out";
          ctx.globalAlpha = 1;
          ctx.lineWidth = brushSizeRef.current * 2.5;
          ctx.lineCap = "round";
          if (pts.length >= 2) {
            ctx.beginPath();
            ctx.moveTo(pts[pts.length - 2].x, pts[pts.length - 2].y);
            ctx.lineTo(pts[pts.length - 1].x, pts[pts.length - 1].y);
            ctx.stroke();
          }
        } else if (t === "rect" || t === "circle" || t === "button-shape") {
          if (previewBaseRef.current) {
            ctx.putImageData(previewBaseRef.current, 0, 0);
          }
          const start = shapeStartRef.current;
          const w = pos.x - start.x;
          const h = pos.y - start.y;
          ctx.globalAlpha = opacityRef.current / 100;
          ctx.globalCompositeOperation = "source-over";
          ctx.strokeStyle = colorRef.current;
          ctx.lineWidth = brushSizeRef.current;
          ctx.fillStyle = `${colorRef.current}22`;

          if (t === "rect") {
            ctx.beginPath();
            ctx.rect(start.x, start.y, w, h);
            ctx.fill();
            ctx.stroke();
          } else if (t === "circle") {
            const rx = Math.abs(w) / 2;
            const ry = Math.abs(h) / 2;
            ctx.beginPath();
            ctx.ellipse(
              start.x + w / 2,
              start.y + h / 2,
              Math.max(rx, 1),
              Math.max(ry, 1),
              0,
              0,
              Math.PI * 2,
            );
            ctx.fill();
            ctx.stroke();
          } else if (t === "button-shape") {
            const x = Math.min(start.x, pos.x);
            const y = Math.min(start.y, pos.y);
            const absW = Math.abs(w);
            const absH = Math.abs(h);
            const r = Math.min(absW, absH) * 0.25;
            ctx.beginPath();
            ctx.roundRect(x, y, absW, absH, r);
            ctx.fill();
            ctx.stroke();
            ctx.fillStyle = colorRef.current;
            ctx.font = `${Math.max(10, absH * 0.4)}px Karla, sans-serif`;
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText("Button", x + absW / 2, y + absH / 2);
            ctx.textAlign = "start";
            ctx.textBaseline = "alphabetic";
          }
        }
      },
      [getCanvasPos],
    );

    const onMouseUp = useCallback(() => {
      if (!isDrawingRef.current) return;
      isDrawingRef.current = false;
      const canvas = drawCanvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.globalCompositeOperation = "source-over";
      ctx.globalAlpha = 1;
      saveHistory();
      pointsRef.current = [];
      previewBaseRef.current = null;
    }, [saveHistory]);

    const onWheel = useCallback(
      (e: React.WheelEvent<HTMLDivElement>) => {
        if (!e.ctrlKey) return;
        e.preventDefault();
        const delta = e.deltaY > 0 ? -0.1 : 0.1;
        const newZoom = Math.max(0.25, Math.min(4, zoomRef.current + delta));
        onZoomChange(Math.round(newZoom * 10) / 10);
      },
      [onZoomChange],
    );

    const cursorStyle =
      tool === "eraser"
        ? "cell"
        : tool === "cursor"
          ? "default"
          : tool === "brush"
            ? "crosshair"
            : "crosshair";

    return (
      <div
        ref={containerRef}
        className="sketch-canvas-container"
        onWheel={onWheel}
        style={{
          position: "relative",
          width: "100%",
          height: "100%",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            transform: `scale(${zoom})`,
            transformOrigin: "top left",
            width: "100%",
            height: "100%",
            position: "absolute",
            top: 0,
            left: 0,
          }}
        >
          <canvas
            ref={bgCanvasRef}
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              pointerEvents: "none",
            }}
          />
          <canvas
            ref={drawCanvasRef}
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              cursor: cursorStyle,
            }}
            onMouseDown={onMouseDown}
            onMouseMove={onMouseMove}
            onMouseUp={onMouseUp}
            onMouseLeave={onMouseUp}
          />
        </div>

        <div className="sketch-zoom-badge">{Math.round(zoom * 100)}%</div>
      </div>
    );
  },
);

SketchCanvas.displayName = "SketchCanvas";
export default SketchCanvas;
