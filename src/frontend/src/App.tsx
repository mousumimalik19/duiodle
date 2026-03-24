import { useEffect, useRef, useState } from "react";
import "./App.css";
import CardNav from "./components/CardNav";
import CircularGallery from "./components/CircularGallery";
import CurvedLoop from "./components/CurvedLoop";
import LiquidEther from "./components/LiquidEther";
import ScrollReveal from "./components/ScrollReveal";
import SketchMode from "./components/SketchMode";
import SpotlightCard from "./components/SpotlightCard";
import Stepper, { Step } from "./components/Stepper";
import TextCursor from "./components/TextCursor";
import UploadMode from "./components/UploadMode";
import { backend } from "./declarations/backend";

const navItems = [
  {
    label: "Create",
    bgColor: "#0D0716",
    textColor: "#fff",
    links: [
      { label: "Sketch On Canvas", ariaLabel: "Sketch" },
      { label: "Upload Sketch", ariaLabel: "Upload Sketch" },
    ],
  },
  {
    label: "Behind the Magic",
    bgColor: "#170D27",
    textColor: "#fff",
    links: [
      { label: "Detect", ariaLabel: "Detect" },
      { label: "Understand", ariaLabel: "Understand" },
      { label: "Style", ariaLabel: "Style" },
      { label: "Animate", ariaLabel: "Animate" },
      { label: "Generate Code", ariaLabel: "Generate Code" },
    ],
  },
  {
    label: "Choose a Vibe",
    bgColor: "#271E37",
    textColor: "#fff",
    links: [
      { label: "Minimal", ariaLabel: "Minimal" },
      { label: "Glass", ariaLabel: "Glass" },
      { label: "Modern", ariaLabel: "Modern" },
      { label: "Playful", ariaLabel: "Playful" },
      { label: "Brutalist", ariaLabel: "Brutalist" },
    ],
  },
];

const galleryItems = [
  {
    image: "/assets/uploads/doodle_recognition_engine-019d1bb3-6bc9-7409-8fa3-7f2392848ab5-4.png",
    text: "Sketch Recognition",
  },
  {
    image: "/assets/uploads/smart_layout_generator-019d1bb3-21b1-7582-909e-3467d512fbcb-3.png",
    text: "Layout Parsing",
  },
  {
    image: "/assets/uploads/element_suggestions-019d1bb3-8a79-74ec-b9d3-1a7b24231e17-5.png",
    text: "Component Mapping",
  },
  {
    image: "/assets/uploads/theme_intelligence-019d1bb3-180e-754f-b8f1-bcc879d77688-2.png",
    text: "Theme Intelligence",
  },
  {
    image: "/assets/uploads/white_and_blue_simple_company_newsletter-019d1bb4-f857-71a0-87ea-dff5bb766ac7-6.png",
    text: "Visual Refinement",
  },
  {
    image: "/assets/uploads/code_preview-019d1bb2-ff95-75ce-b2d8-6979b9e08bbc-1.png",
    text: "UI Output",
  },
];

const themeCards = [
  {
    title: "Minimal Dark",
    description: "Clean monochrome layouts with purposeful negative space.",
    gradient: "linear-gradient(135deg, #111827 0%, #1f2937 100%)",
    tag: "Dark",
  },
  {
    title: "Modern SaaS",
    description: "Sharp type, cool neutrals, and precise component grids.",
    gradient: "linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%)",
    tag: "Light",
  },
  {
    title: "Dashboard Pro",
    description: "Dense data layouts with structured hierarchy and clarity.",
    gradient: "linear-gradient(135deg, #0f172a 0%, #334155 100%)",
    tag: "Dark",
  },
  {
    title: "Creative Portfolio",
    description: "Editorial grids, expressive type, and flowing composition.",
    gradient: "linear-gradient(135deg, #7c3aed 0%, #ec4899 100%)",
    tag: "Light",
  },
  {
    title: "Startup Landing",
    description: "Conversion-focused layout with bold hierarchy and CTAs.",
    gradient: "linear-gradient(135deg, #065f46 0%, #10b981 100%)",
    tag: "Light",
  },
  {
    title: "Academic Interface",
    description: "Research-grade typography with structured document flow.",
    gradient: "linear-gradient(135deg, #4b3f2e 0%, #92816a 100%)",
    tag: "Light",
  },
];

export default function App() {
  const [theme, setTheme] = useState<"light" | "dark">(
    () => (localStorage.getItem("theme") as "light" | "dark") ?? "light",
  );
  const [sketchOpen, setSketchOpen] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [heroPulse, setHeroPulse] = useState(false);
  const [aiResult, setAiResult] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const heroRef = useRef<HTMLElement>(null);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () =>
    setTheme((prev) => (prev === "light" ? "dark" : "light"));

  const processDoodleToCode = async (imageBlob: Blob) => {
    try {
      setIsProcessing(true);
      const arrayBuffer = await imageBlob.arrayBuffer();
      const uint8Array = new Uint8Array(arrayBuffer);

      const result = await backend.process_doodle(Array.from(uint8Array));
      
      // INTEGRATION: Store the result and close overlays
      setAiResult(result);
      setSketchOpen(false);
      setUploadOpen(false);
    } catch (err) {
      console.error("Backend Error:", err);
      alert("AI Engine encountered an error. Please check your connection.");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleLaunchDuiodle = () => {
    if (sketchOpen || uploadOpen) {
      setSketchOpen(false);
      setUploadOpen(false);
      return;
    }

    const hero = heroRef.current;
    if (!hero) return;
    const rect = hero.getBoundingClientRect();
    const isVisible = rect.top >= 0 && rect.top < window.innerHeight * 0.5;
    if (isVisible) {
      setHeroPulse(true);
      setTimeout(() => setHeroPulse(false), 1000);
    } else {
      hero.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <div className="app">
      {/* 1. RESULT OVERLAY (INTEGRATION LAYER) */}
      {aiResult && (
        <div className="ai-result-view">
          <div className="result-container">
            <header className="result-header">
              <div className="header-left">
                <span className="ai-badge">Duiodle AI Output</span>
                <h2>Magic Generation Complete</h2>
              </div>
              <div className="header-right">
                <button className="btn-secondary" onClick={() => navigator.clipboard.writeText(aiResult)}>Copy Code</button>
                <button className="btn-close" onClick={() => setAiResult(null)}>×</button>
              </div>
            </header>
            <div className="result-content-grid">
              <div className="result-preview-panel">
                <span className="panel-label">Live Interface</span>
                <iframe srcDoc={aiResult} title="AI Preview" className="preview-frame" />
              </div>
              <div className="result-code-panel">
                <span className="panel-label">Structured Code</span>
                <pre className="code-display">
                  <code>{aiResult}</code>
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 2. OVERLAYS */}
      {sketchOpen && (
        <SketchMode
          theme={theme}
          toggleTheme={toggleTheme}
          onClose={() => setSketchOpen(false)}
          onGenerate={processDoodleToCode}
          isProcessing={isProcessing}
        />
      )}

      {uploadOpen && (
        <UploadMode
          theme={theme}
          toggleTheme={toggleTheme}
          onClose={() => setUploadOpen(false)}
          onUpload={processDoodleToCode}
          isProcessing={isProcessing}
        />
      )}

      {/* 3. UI ELEMENTS */}
      <SpotlightCard className="theme-toggle-wrap">
        <button
          type="button"
          className="theme-toggle"
          onClick={toggleTheme}
          aria-label={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
        >
          {theme === "light" ? "🌙" : "☀️"}
        </button>
      </SpotlightCard>

      <div className="card-spotlight nav-spotlight-wrap">
        <CardNav
          items={navItems}
          baseColor="#ffffff"
          menuColor="#111827"
          buttonBgColor="#111827"
          buttonTextColor="#ffffff"
          ease="power3.out"
        />
      </div>

      <section className="hero-section" ref={heroRef}>
        <div className="hero-liquid-layer">
          <LiquidEther
            colors={isProcessing ? ["#7c3aed", "#ec4899", "#ef4444"] : ["#fbff29", "#f9ff9e", "#ebf0a3"]}
            autoIntensity={isProcessing ? 4.0 : 2.2}
            autoDemo
          />
        </div>
        <div className="hero-cursor-layer">
          <TextCursor text="duiodle" spacing={80} />
        </div>
        <div className="hero-content">
          <h1 className="hero-title">duiodle</h1>
          <p className="hero-subtitle">
            Transform rough sketches into structured digital interfaces.
            <br />
            From intuition to implementation, powered by AI.
          </p>
          <div className={`hero-buttons${heroPulse ? " hero-buttons-pulse" : ""}`}>
            <SpotlightCard className="btn-spotlight-wrap">
              <button className="btn-outline" onClick={() => setSketchOpen(true)}>Sketch</button>
            </SpotlightCard>
            <SpotlightCard className="btn-spotlight-wrap">
              <button className="btn-outline" onClick={() => setUploadOpen(true)}>Upload</button>
            </SpotlightCard>
          </div>
        </div>
      </section>

      <section className="gallery-section">
        <div className="gallery-header">
          <div className="section-eyebrow">Capabilities</div>
          <h2 className="section-heading">What Duiodle Sees</h2>
        </div>
        <div className="gallery-inner">
          <CircularGallery items={galleryItems} bend={1} scrollSpeed={1.5} />
        </div>
      </section>

      <section className="about-section">
        <ScrollReveal baseOpacity={0.1} enableBlur>
          Duiodle bridges creativity and computation. By analyzing spatial hierarchy, 
          it converts hand-drawn sketches into structured interface systems ready for iteration.
        </ScrollReveal>
      </section>

      <section className="stepper-section">
        <div className="stepper-header">
          <div className="section-eyebrow">Behind the Magic</div>
          <h2 className="section-heading">How Duiodle Works</h2>
        </div>
        <Stepper initialStep={1}>
          <Step><h2>Sketch Input</h2><p>Wireframe capture.</p></Step>
          <Step><h2>Layout Recognition</h2><p>Hierarchy parsing.</p></Step>
          <Step><h2>Component Detection</h2><p>Mapping elements.</p></Step>
          <Step><h2>Theme Intelligence</h2><p>Applying vibes.</p></Step>
          <Step><h2>Interface Output</h2><p>Ready for code.</p></Step>
        </Stepper>
      </section>

      <section className="showcase-section">
        <div className="section-eyebrow">Generated with Duiodle</div>
        <h2 className="section-heading">Choose Your Aesthetic</h2>
        <div className="theme-cards">
          {themeCards.map((card) => (
            <SpotlightCard className="theme-card" key={card.title}>
              <div className="theme-card-visual" style={{ background: card.gradient }} />
              <div className="theme-card-body">
                <div className="theme-card-tag">{card.tag}</div>
                <h3 className="theme-card-title">{card.title}</h3>
                <p className="theme-card-desc">{card.description}</p>
              </div>
            </SpotlightCard>
          ))}
        </div>
      </section>

      <section className="cta-section">
        <h2 className="cta-heading">From imagination to interface.</h2>
        <SpotlightCard className="cta-btn-wrap">
          <button className="btn-primary" onClick={handleLaunchDuiodle}>Launch Duiodle</button>
        </SpotlightCard>
      </section>

      <footer className="footer">
        <div className="footer-loop">
          <CurvedLoop marqueeText="duiodle ✦ duiodle ✦ duiodle ✦" speed={1.5} />
        </div>
        <div className="footer-bottom">
          <div className="footer-credits">Made with ♥ by Rishika &amp; Mousumi</div>
          <div className="footer-caffeine">© {new Date().getFullYear()}</div>
        </div>
      </footer>
    </div>
  );
}