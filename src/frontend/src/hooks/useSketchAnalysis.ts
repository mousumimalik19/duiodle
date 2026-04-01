import { useCallback, useRef, useState } from "react";
import { toast } from "sonner";
import { useActor } from "./useActor";

export interface DetectedElement {
  component: string;
  bounds: { x: number; y: number; w: number; h: number };
  content: string | null;
  children: DetectedElement[];
}

export interface ParsedAnalysis {
  sketch_id: string;
  detected_elements: DetectedElement[];
  analysis: {
    layout_type: string;
    confidence: number;
    detected_components: string[];
    auto_improvements: string[];
  };
}

export type DesignTheme =
  | "minimal"
  | "brutalist"
  | "glass"
  | "modern-saas"
  | "monochrome"
  | "animated"
  | "playful";

export type FidelityLevel = "high" | "medium" | "low";

// ─── Theme Overlays (short visual rules per theme) ────────────────────────────
const THEME_OVERLAYS: Record<DesignTheme, string> = {
  minimal:
    "White space is the hero. Use 1px borders, zero shadows, and ultra-thin typography. No decorative elements.",
  brutalist:
    "Hard-edged. Use border-2 border-black, shadow-[4px_4px_0px_0px_rgba(0,0,0,1)], and bright neon accents.",
  glass:
    "Backdrop-blur is mandatory. Use bg-white/10 backdrop-blur-md border border-white/20. Add soft colorful blobs in the background.",
  "modern-saas":
    "Bento-grid style. Use deep shadow-xl, large rounded-3xl corners, and subtle indigo/slate gradients.",
  monochrome:
    "Strict color limit. Use only shades of one color (e.g., Emerald). Use transparency and weights to create hierarchy.",
  animated:
    "Motion-first. Every component must use motion.div. Use staggered fade-ins and 'spring' physics for all transitions.",
  playful:
    "Claymorphism. Use rounded-full, soft 'squishy' shadows, and a bubbly, oversized aesthetic with pastel colors.",
};

export const DESIGN_THEME_LABELS: Record<DesignTheme, string> = {
  minimal: "Minimal",
  brutalist: "Brutalist",
  glass: "Glass",
  "modern-saas": "Modern SaaS",
  monochrome: "Monochrome",
  animated: "Animated",
  playful: "Playful",
};
// ──────────────────────────────────────────────────────────────────────────────

export function isCanisterStoppedError(err: unknown): boolean {
  const msg =
    err instanceof Error
      ? err.message
      : typeof err === "string"
        ? err
        : JSON.stringify(err);
  const lower = msg.toLowerCase();
  return (
    lower.includes("canister is stopped") ||
    lower.includes("reject code: 5") ||
    lower.includes("ic0508") ||
    lower.includes('"reject_code":5') ||
    /reject.?code.{0,5}5/.test(lower)
  );
}

function getFidelityPrompt(level: FidelityLevel): string {
  if (level === "low")
    return "Act as a UX Architect. Generate a high-quality Low-Fidelity Wireframe. STYLING: Use only bg-gray-100 for backgrounds and border-gray-400 for outlines. No shadows, no gradients, and no rounded corners (use rounded-none). PLACEHOLDERS: Represent images as gray boxes with a centered 'X' made of two diagonal lines. TYPOGRAPHY: Use a generic monospace font like 'Courier' or 'monospace' to indicate that content is draft-only. ICONS: Use simple geometric shapes (circles or squares) instead of real icons. GOAL: The output should look like a professional Balsamiq or Figma wireframe, focusing 100% on structure and 0% on aesthetic.";
  if (level === "medium")
    return "Generate a polished mockup. Use real colors and basic Tailwind components (buttons, cards). Use clean typography and standard spacing. It should look like a finished design but remain static and simple.";
  return "Generate production-ready React code. Use advanced Tailwind (arbitrary values, complex grids), accessibility (aria-labels), and Framer Motion for all interactions. Code must be modular and include hover/active states.";
}

function buildEdgePrompt(
  designTheme: DesignTheme,
  fidelityLevel: FidelityLevel,
): string {
  const baseFidelity = getFidelityPrompt(fidelityLevel);

  // Matrix exception: Low fidelity modifies certain theme overlays
  let themeOverlay = THEME_OVERLAYS[designTheme];
  if (fidelityLevel === "low") {
    const LOW_FI_THEME_OVERLAYS: Record<DesignTheme, string> = {
      minimal:
        "Ultra-clean wireframe: lots of white space, 1px light gray borders (border-gray-300), no rounded corners. Keep it stark and spacious.",
      brutalist:
        "Thick 2px black borders (border-2 border-black), very heavy oversized boxes, no rounded corners. Use border-gray-900 for all outlines to show the structural weight.",
      glass:
        "Use simple transparent-outline boxes only. No backdrop-blur, no gradients, no transparency effects. Just flat border-gray-400 outlines on bg-gray-100.",
      "modern-saas":
        "Bento-style grid layout using gray boxes of varying sizes (some tall, some wide). Show the bento structure with border-gray-400 on bg-gray-100.",
      monochrome:
        "Use different shades of gray to create hierarchy: bg-gray-100, bg-gray-300, bg-gray-500 for nested depth. No other colors.",
      animated:
        "Skip motion. Focus on layout structure and how elements would transition spatially. Show placeholder zones for animated regions with border-dashed border-gray-400.",
      playful:
        "Use large rounded-2xl gray boxes to show the bubbly structural layout. Keep them bg-gray-100 with border-gray-400, hinting at the chunky proportions.",
    };
    themeOverlay = LOW_FI_THEME_OVERLAYS[designTheme];
  }

  const finalPrompt = `${baseFidelity} ${themeOverlay} Analyze this sketch and write the code.`;

  return `You are a Vision-to-Code parser. Analyze this hand-drawn UI sketch and return a structured JSON UI tree.

Extract all UI elements with their exact positions in a 1000x1000 coordinate system.

GENERATION INSTRUCTIONS: ${finalPrompt}

Return ONLY this JSON structure with no markdown, no explanation:
{
  "sketch_id": "edge_<timestamp>",
  "detected_elements": [
    {
      "component": "button|input|card|nav|image|text|icon|container",
      "bounds": { "x": 0, "y": 0, "w": 100, "h": 50 },
      "content": "label text or null",
      "children": []
    }
  ]
}

Rules:
- Read any handwritten text exactly as written
- Identify containers (large boxes holding other elements) and nest children inside them
- Map each element to the closest component type
- Reflect the actual spatial position of elements in x,y coordinates
- Output ONLY raw JSON`;
}

// Use v1 for gemini-2.5-flash availability
const GEMINI_API_VERSION = "v1";
const DEFAULT_MODEL = "gemini-2.5-flash";

function buildAnalysisFromElements(
  elements: DetectedElement[],
): ParsedAnalysis["analysis"] {
  return {
    layout_type: "flex-column",
    confidence: 0.78,
    detected_components: elements.map((e) => e.component),
    auto_improvements: [],
  };
}

function parseGeminiText(rawText: string): ParsedAnalysis {
  const cleaned = rawText
    .replace(/^```[\w]*\n?/m, "")
    .replace(/\n?```$/m, "")
    .trim();

  const parsed = JSON.parse(cleaned) as ParsedAnalysis;

  if (!parsed || !Array.isArray(parsed.detected_elements)) {
    throw new Error("Unexpected response format");
  }

  if (!parsed.analysis) {
    parsed.analysis = buildAnalysisFromElements(parsed.detected_elements);
  }

  return parsed;
}

async function callGeminiWithModel(
  imageBase64: string,
  mimeType: string,
  apiKey: string,
  model: string,
  prompt: string,
): Promise<ParsedAnalysis> {
  const url = `https://generativelanguage.googleapis.com/${GEMINI_API_VERSION}/models/${model}:generateContent?key=${apiKey}`;

  const body = {
    contents: [
      {
        parts: [
          { inline_data: { mime_type: mimeType, data: imageBase64 } },
          { text: prompt },
        ],
      },
    ],
  };

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Gemini API error: ${res.status} ${errText}`);
  }

  const rawBody = await res.text();
  const envelope = JSON.parse(rawBody);

  const text: string | undefined =
    envelope?.candidates?.[0]?.content?.parts?.[0]?.text;

  if (!text) {
    throw new Error("Unexpected response format: no text in Gemini response");
  }

  return parseGeminiText(text);
}

async function callGeminiDirect(
  imageBase64: string,
  mimeType: string,
  apiKey: string,
  prompt: string,
): Promise<ParsedAnalysis> {
  const storedModel =
    localStorage.getItem("duiodle_gemini_model") ?? DEFAULT_MODEL;
  const preferredModel = storedModel
    .replace(/^models\//, "")
    .replace(/-latest$/, "");

  const cascade: string[] = [];
  if (preferredModel !== DEFAULT_MODEL) cascade.push(preferredModel);
  cascade.push(DEFAULT_MODEL);
  cascade.push("gemini-1.5-flash");

  let lastError: Error = new Error("All models failed");
  for (const model of cascade) {
    try {
      return await callGeminiWithModel(
        imageBase64,
        mimeType,
        apiKey,
        model,
        prompt,
      );
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      if (msg.includes("404")) {
        lastError = err instanceof Error ? err : new Error(msg);
        continue;
      }
      throw err;
    }
  }
  throw lastError;
}

export function useSketchAnalysis() {
  const { actor, isFetching } = useActor();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ParsedAnalysis | null>(null);
  const [isCanisterStopped, setIsCanisterStopped] = useState(false);
  const [isEdgeMode, setIsEdgeMode] = useState(false);

  const lastArgsRef = useRef<{
    imageBase64: string;
    mimeType: string;
    designTheme: DesignTheme;
    fidelityLevel: FidelityLevel;
  } | null>(null);
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const analyze = useCallback(
    async (
      imageBase64: string,
      mimeType: string,
      designTheme: DesignTheme = "minimal",
      fidelityLevel: FidelityLevel = "high",
    ) => {
      lastArgsRef.current = {
        imageBase64,
        mimeType,
        designTheme,
        fidelityLevel,
      };

      setLoading(true);
      setError(null);
      setResult(null);
      setIsCanisterStopped(false);
      setIsEdgeMode(false);

      const apiKey = localStorage.getItem("duiodle_gemini_key") ?? "";

      if (!apiKey) {
        setError(
          "Please add your Gemini API key in settings to enable AI analysis.",
        );
        setLoading(false);
        return;
      }

      const prompt = buildEdgePrompt(designTheme, fidelityLevel);

      // Step 1: Try ICP canister
      let canisterSucceeded = false;

      if (actor && !isFetching) {
        try {
          const rawResponse = await actor.analyzeSketch(
            imageBase64,
            mimeType,
            apiKey,
          );

          let parsed: ParsedAnalysis | null = null;
          try {
            const envelope = JSON.parse(rawResponse);
            const text: string | undefined =
              envelope?.candidates?.[0]?.content?.parts?.[0]?.text;
            if (text) {
              parsed = parseGeminiText(text);
            } else if (envelope?.detected_elements) {
              parsed = envelope as ParsedAnalysis;
              if (!parsed.analysis) {
                parsed.analysis = buildAnalysisFromElements(
                  parsed.detected_elements,
                );
              }
            }
          } catch {
            try {
              parsed = parseGeminiText(rawResponse);
            } catch {
              // fall through to edge mode
            }
          }

          if (parsed?.detected_elements) {
            setResult(parsed);
            canisterSucceeded = true;
          }
        } catch (canisterErr) {
          if (isCanisterStoppedError(canisterErr)) {
            setIsCanisterStopped(true);
          }
        }
      }

      // Step 2: Edge Mode fallback
      if (!canisterSucceeded) {
        setIsEdgeMode(true);

        toast(
          `⚡ Edge Mode — ${DESIGN_THEME_LABELS[designTheme]} theme · ${
            fidelityLevel === "high"
              ? "High Fidelity"
              : fidelityLevel === "medium"
                ? "Static Mockup"
                : "Wireframe"
          }`,
          {
            duration: 3500,
            style: {
              background: "#1a1025",
              color: "#f0e8ff",
              border: "1px solid rgba(251,255,41,0.25)",
              borderRadius: "10px",
              fontSize: "13.5px",
              fontFamily: "Karla, sans-serif",
              letterSpacing: "0.01em",
            },
          },
        );

        try {
          const edgeResult = await callGeminiDirect(
            imageBase64,
            mimeType,
            apiKey,
            prompt,
          );
          setResult(edgeResult);
        } catch (edgeErr) {
          const msg =
            edgeErr instanceof Error
              ? edgeErr.message
              : "Edge Mode analysis failed";
          setError(msg);
          setIsEdgeMode(false);
        }
      }

      setLoading(false);
    },
    [actor, isFetching],
  );

  const retry = useCallback(() => {
    if (lastArgsRef.current) {
      const { imageBase64, mimeType, designTheme, fidelityLevel } =
        lastArgsRef.current;
      analyze(imageBase64, mimeType, designTheme, fidelityLevel);
    }
  }, [analyze]);

  const clearRetry = useCallback(() => {
    if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
  }, []);

  return {
    loading,
    error,
    result,
    analyze,
    retry,
    isCanisterStopped,
    isEdgeMode,
    clearRetry,
  };
}
