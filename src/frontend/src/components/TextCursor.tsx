import { AnimatePresence, motion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import "./TextCursor.css";

interface TrailItem {
  id: number;
  x: number;
  y: number;
  angle: number;
  randomX?: number;
  randomY?: number;
  randomRotate?: number;
}

interface TextCursorProps {
  text?: string;
  spacing?: number;
  followMouseDirection?: boolean;
  randomFloat?: boolean;
  exitDuration?: number;
  removalInterval?: number;
  maxPoints?: number;
}

const TextCursor = ({
  text = "duiodle",
  spacing = 80,
  followMouseDirection = true,
  randomFloat = true,
  exitDuration = 0.3,
  removalInterval = 20,
  maxPoints = 10,
}: TextCursorProps) => {
  const [trail, setTrail] = useState<TrailItem[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);
  const lastMoveTimeRef = useRef(Date.now());
  const idCounter = useRef(0);
  const spacingRef = useRef(spacing);
  const followMouseDirectionRef = useRef(followMouseDirection);
  const randomFloatRef = useRef(randomFloat);
  const maxPointsRef = useRef(maxPoints);

  useEffect(() => {
    spacingRef.current = spacing;
  }, [spacing]);
  useEffect(() => {
    followMouseDirectionRef.current = followMouseDirection;
  }, [followMouseDirection]);
  useEffect(() => {
    randomFloatRef.current = randomFloat;
  }, [randomFloat]);
  useEffect(() => {
    maxPointsRef.current = maxPoints;
  }, [maxPoints]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      const createRandomData = () =>
        randomFloatRef.current
          ? {
              randomX: Math.random() * 10 - 5,
              randomY: Math.random() * 10 - 5,
              randomRotate: Math.random() * 10 - 5,
            }
          : {};

      setTrail((prev) => {
        const newTrail = [...prev];
        if (newTrail.length === 0) {
          newTrail.push({
            id: idCounter.current++,
            x: mouseX,
            y: mouseY,
            angle: 0,
            ...createRandomData(),
          });
        } else {
          const last = newTrail[newTrail.length - 1];
          const dx = mouseX - last.x;
          const dy = mouseY - last.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          if (distance >= spacingRef.current) {
            const rawAngle = (Math.atan2(dy, dx) * 180) / Math.PI;
            const computedAngle = followMouseDirectionRef.current
              ? rawAngle
              : 0;
            const steps = Math.floor(distance / spacingRef.current);
            for (let i = 1; i <= steps; i++) {
              const t = (spacingRef.current * i) / distance;
              const newX = last.x + dx * t;
              const newY = last.y + dy * t;
              newTrail.push({
                id: idCounter.current++,
                x: newX,
                y: newY,
                angle: computedAngle,
                ...createRandomData(),
              });
            }
          }
        }
        return newTrail.length > maxPointsRef.current
          ? newTrail.slice(newTrail.length - maxPointsRef.current)
          : newTrail;
      });
      lastMoveTimeRef.current = Date.now();
    };

    container.addEventListener("mousemove", handleMouseMove);
    return () => container.removeEventListener("mousemove", handleMouseMove);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      if (Date.now() - lastMoveTimeRef.current > 100) {
        setTrail((prev) => (prev.length > 0 ? prev.slice(1) : prev));
      }
    }, removalInterval);
    return () => clearInterval(interval);
  }, [removalInterval]);

  return (
    <div ref={containerRef} className="text-cursor-container">
      <div className="text-cursor-inner">
        <AnimatePresence>
          {trail.map((item) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, scale: 1, rotate: item.angle }}
              animate={{
                opacity: 1,
                scale: 1,
                x: randomFloat ? [0, item.randomX || 0, 0] : 0,
                y: randomFloat ? [0, item.randomY || 0, 0] : 0,
                rotate: randomFloat
                  ? [
                      item.angle,
                      item.angle + (item.randomRotate || 0),
                      item.angle,
                    ]
                  : item.angle,
              }}
              exit={{ opacity: 0, scale: 0 }}
              transition={{
                opacity: { duration: exitDuration, ease: "easeOut" },
                ...(randomFloat && {
                  x: {
                    duration: 2,
                    ease: "easeInOut",
                    repeat: Number.POSITIVE_INFINITY,
                    repeatType: "mirror",
                  },
                  y: {
                    duration: 2,
                    ease: "easeInOut",
                    repeat: Number.POSITIVE_INFINITY,
                    repeatType: "mirror",
                  },
                  rotate: {
                    duration: 2,
                    ease: "easeInOut",
                    repeat: Number.POSITIVE_INFINITY,
                    repeatType: "mirror",
                  },
                }),
              }}
              className="text-cursor-item"
              style={{ left: item.x, top: item.y }}
            >
              {text}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default TextCursor;
