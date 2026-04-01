import { useEffect, useRef, useState } from "react";
import "./App.css";
import { Settings } from "lucide-react";
import CardNav from "./components/CardNav";
import CircularGallery from "./components/CircularGallery";
import CurvedLoop from "./components/CurvedLoop";
import LiquidEther from "./components/LiquidEther";
import ScrollReveal from "./components/ScrollReveal";
import SettingsModal from "./components/SettingsModal";
import SketchMode from "./components/SketchMode";
import SpotlightCard from "./components/SpotlightCard";
import Stepper, { Step } from "./components/Stepper";
import SystemStatus from "./components/SystemStatus";
import TextCursor from "./components/TextCursor";
import ThemeTooltip from "./components/ThemeTooltip";
import UploadMode from "./components/UploadMode";
import { Toaster } from "./components/ui/sonner";

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
      { label: "Minimal", ariaLabel: "Minimal", themeId: "minimal" },
      { label: "Brutalist", ariaLabel: "Brutalist", themeId: "brutalist" },
      { label: "Glass", ariaLabel: "Glass", themeId: "glass" },
      {
        label: "Modern SaaS",
        ariaLabel: "Modern SaaS",
        themeId: "modern-saas",
      },
      { label: "Monochrome", ariaLabel: "Monochrome", themeId: "monochrome" },
      { label: "Animated", ariaLabel: "Animated", themeId: "animated" },
      { label: "Playful", ariaLabel: "Playful", themeId: "playful" },
    ],
  },
];

const galleryItems = [
  {
    image: "/assets/uploads/doodle_recognition_engine-new.png",
    text: "Sketch Recognition",
  },
  {
    image: "/assets/uploads/smart_layout_generator-new.png",
    text: "Layout Parsing",
  },
  {
    image: "/assets/uploads/element_suggestions-new.png",
    text: "Component Mapping",
  },
  {
    image: "/assets/uploads/theme_intelligence-new.png",
    text: "Theme Intelligence",
  },
  {
    image: "/assets/uploads/newsletter-new.png",
    text: "Visual Refinement",
  },
  {
    image: "/assets/uploads/code_preview-new.png",
    text: "UI Output",
  },
];

const themeCards = [
  {
    themeId: "minimal",
    title: "Minimal",
    description: "Clean Swiss design with focus on white space.",
    gradient: "linear-gradient(135deg, #f8f8f8 0%, #e5e5e5 100%)",
    tag: "Swiss",
  },
  {
    themeId: "brutalist",
    title: "Brutalist",
    description: "Raw, high-contrast UI with bold black outlines.",
    gradient: "linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%)",
    tag: "Neo-Brutalist",
  },
  {
    themeId: "glass",
    title: "Glass",
    description: "Translucent panels with heavy background blur.",
    gradient: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    tag: "Glassmorphism",
  },
  {
    themeId: "modern-saas",
    title: "Modern SaaS",
    description: "Premium Bento-grid layout with soft shadows.",
    gradient: "linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%)",
    tag: "SaaS",
  },
  {
    themeId: "monochrome",
    title: "Monochrome",
    description: "High-end aesthetic using a single-color palette.",
    gradient: "linear-gradient(135deg, #1a1a1a 0%, #4a4a4a 100%)",
    tag: "Mono",
  },
  {
    themeId: "animated",
    title: "Animated",
    description: "Kinetic UI featuring fluid Framer Motion transitions.",
    gradient: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
    tag: "Motion",
  },
  {
    themeId: "playful",
    title: "Playful",
    description: "Bouncy, claymorphic shapes with pastel colors.",
    gradient: "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)",
    tag: "Claymorphic",
  },
];

export default function App() {
  const [theme, setTheme] = useState<"light" | "dark">(
    () => (localStorage.getItem("theme") as "light" | "dark") ?? "light",
  );
  const [sketchOpen, setSketchOpen] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const workspaceOpen = sketchOpen || uploadOpen;
  const [heroPulse, setHeroPulse] = useState(false);
  const heroRef = useRef<HTMLElement>(null);

  // AI Settings state
  const [showApiSettings, setShowApiSettings] = useState(false);
  const [geminiKey, setGeminiKey] = useState(
    () => localStorage.getItem("duiodle_gemini_key") ?? "",
  );
  const [geminiModel, setGeminiModel] = useState(
    () => localStorage.getItem("duiodle_gemini_model") ?? "gemini-2.5-flash",
  );
  const hasKey = geminiKey.trim().length > 0;

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () =>
    setTheme((prev) => (prev === "light" ? "dark" : "light"));

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

  const handleSaveKey = (key: string, model: string) => {
    localStorage.setItem("duiodle_gemini_key", key.trim());
    localStorage.setItem("duiodle_gemini_model", model);
    setGeminiKey(key.trim());
    setGeminiModel(model);
    setShowApiSettings(false);
  };

  const handleCloseSettings = () => {
    setGeminiKey(localStorage.getItem("duiodle_gemini_key") ?? "");
    setShowApiSettings(false);
  };

  return (
    <div className="app" data-gemini-model={geminiModel}>
      {/* FIXED TOP-RIGHT GEAR BUTTON */}
      <button
        type="button"
        onClick={() => setShowApiSettings(true)}
        title="API Settings"
        aria-label="API Settings"
        data-ocid="settings.open_modal_button"
        style={{
          position: "fixed",
          top: "24px",
          right: "24px",
          zIndex: 9999,
          padding: "8px",
          borderRadius: "50%",
          background: "#1f2937",
          border: "1px solid #374151",
          boxShadow: "0 4px 16px rgba(0,0,0,0.4)",
          cursor: "pointer",
          transition: "background 0.2s",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = "#374151";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = "#1f2937";
        }}
      >
        <Settings className="w-6 h-6" style={{ color: "#fbff29" }} />
        <span
          style={{
            position: "absolute",
            top: "4px",
            right: "4px",
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            background: hasKey ? "#22c55e" : "#ef4444",
            border: "1.5px solid #1f2937",
          }}
        />
      </button>

      {/* SKETCH MODE OVERLAY */}
      {sketchOpen && (
        <SketchMode
          theme={theme}
          toggleTheme={toggleTheme}
          onClose={() => setSketchOpen(false)}
          geminiKey={geminiKey}
          onOpenSettings={() => setShowApiSettings(true)}
        />
      )}

      {/* UPLOAD MODE OVERLAY */}
      {uploadOpen && (
        <UploadMode
          theme={theme}
          toggleTheme={toggleTheme}
          onClose={() => setUploadOpen(false)}
          geminiKey={geminiKey}
          onOpenSettings={() => setShowApiSettings(true)}
        />
      )}

      {/* AI SETTINGS BUTTON */}
      <SpotlightCard className="theme-toggle-wrap" style={{ bottom: "80px" }}>
        <button
          type="button"
          className="theme-toggle"
          onClick={() => setShowApiSettings(true)}
          aria-label="AI Settings"
          data-ocid="settings.open_modal_button"
          style={{ position: "relative" }}
        >
          <Settings width={18} height={18} aria-hidden="true" />
          <span
            style={{
              position: "absolute",
              top: "6px",
              right: "6px",
              width: "7px",
              height: "7px",
              borderRadius: "50%",
              background: hasKey ? "#22c55e" : "#ef4444",
              border: "1.5px solid var(--bg, #fff)",
            }}
          />
        </button>
      </SpotlightCard>

      {/* THEME TOGGLE */}
      <SpotlightCard className="theme-toggle-wrap">
        <button
          type="button"
          className="theme-toggle"
          onClick={toggleTheme}
          aria-label={
            theme === "light" ? "Switch to dark mode" : "Switch to light mode"
          }
          data-ocid="theme.toggle"
        >
          {theme === "light" ? (
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          ) : (
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" />
              <line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" />
              <line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
          )}
        </button>
      </SpotlightCard>

      {/* AI SETTINGS MODAL */}
      <SettingsModal
        open={showApiSettings}
        geminiKey={geminiKey}
        onGeminiKeyChange={setGeminiKey}
        onSave={handleSaveKey}
        onClose={handleCloseSettings}
      />

      {/* 1. FLOATING NAV */}
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

      {/* 2. HERO SECTION */}
      <section className="hero-section" ref={heroRef}>
        <div className="hero-liquid-layer">
          {!workspaceOpen && (
            <LiquidEther
              colors={["#fbff29", "#f9ff9e", "#ebf0a3"]}
              mouseForce={20}
              cursorSize={100}
              isViscous
              viscous={30}
              iterationsViscous={32}
              iterationsPoisson={32}
              resolution={0.5}
              isBounce={false}
              autoDemo
              autoSpeed={0.5}
              autoIntensity={2.2}
              takeoverDuration={0.25}
              autoResumeDelay={3000}
              autoRampDuration={0.6}
            />
          )}
        </div>
        <div className="hero-cursor-layer">
          {!workspaceOpen && (
            <TextCursor
              text="duiodle"
              spacing={80}
              followMouseDirection
              randomFloat
              exitDuration={0.3}
              removalInterval={20}
              maxPoints={10}
            />
          )}
        </div>
        <div className="hero-content">
          <h1 className="hero-title">duiodle</h1>
          <p className="hero-subtitle">
            Transform rough sketches into structured digital interfaces.
            <br />
            From intuition to implementation, powered by AI.
          </p>
          <div
            className={`hero-buttons${heroPulse ? " hero-buttons-pulse" : ""}`}
          >
            <SpotlightCard className="btn-spotlight-wrap">
              <button
                type="button"
                className="btn-outline btn-sketch"
                onClick={() => setSketchOpen(true)}
                data-ocid="hero.primary_button"
              >
                Sketch
              </button>
            </SpotlightCard>
            <SpotlightCard className="btn-spotlight-wrap">
              <button
                type="button"
                className="btn-outline btn-upload"
                onClick={() => setUploadOpen(true)}
                data-ocid="hero.secondary_button"
              >
                Upload
              </button>
            </SpotlightCard>
          </div>
          <p className="hero-meta">
            Computer Vision · Structural Hierarchy · AI Refinement · Theme
            Abstraction
          </p>
        </div>
      </section>

      {/* 3. GALLERY SECTION */}
      <section className="gallery-section">
        <div className="gallery-header">
          <div className="section-eyebrow">Capabilities</div>
          <h2 className="section-heading gallery-heading">What Duiodle Sees</h2>
        </div>
        <div className="gallery-inner">
          {!workspaceOpen && (
            <CircularGallery
              items={galleryItems}
              bend={1}
              scrollSpeed={1.5}
              scrollEase={0.07}
              borderRadius={0.05}
              textColor="#ffffff"
              font="bold 28px Montserrat"
            />
          )}
        </div>
      </section>

      {/* 4. SCROLL REVEAL */}
      <section className="about-section">
        <ScrollReveal
          baseOpacity={0.1}
          enableBlur
          baseRotation={2}
          blurStrength={3}
        >
          Duiodle bridges creativity and computation. By analyzing spatial
          hierarchy, structural patterns, and component relationships, it
          converts hand-drawn sketches into structured interface systems ready
          for iteration.
        </ScrollReveal>
        <div className="about-tags">
          <span className="about-tag">
            Computer Vision-based layout detection
          </span>
          <span className="about-tag">Structural hierarchy parsing</span>
          <span className="about-tag">AI-assisted refinement engine</span>
          <span className="about-tag">Theme abstraction layer</span>
        </div>
      </section>

      {/* 5. STEPPER */}
      <section className="stepper-section">
        <div className="stepper-header">
          <div className="section-eyebrow">Behind the Magic</div>
          <h2 className="section-heading">How Duiodle Works</h2>
        </div>
        <Stepper
          initialStep={1}
          backButtonText="Previous"
          nextButtonText="Next"
        >
          <Step>
            <h2>Sketch Input</h2>
            <p>
              Your hand-drawn wireframe is captured and pre-processed for
              structural analysis.
            </p>
          </Step>
          <Step>
            <h2>Layout Recognition</h2>
            <p>
              Computer vision algorithms detect spatial hierarchy and structural
              zones across the canvas.
            </p>
          </Step>
          <Step>
            <h2>Component Detection</h2>
            <p>
              UI primitives — buttons, inputs, containers — are identified and
              mapped to a component schema.
            </p>
          </Step>
          <Step>
            <h2>Theme Intelligence</h2>
            <p>
              Design tokens, spacing systems, and visual language are applied
              intelligently based on vibe selection.
            </p>
          </Step>
          <Step>
            <h2>Interface Output</h2>
            <p>
              A structured, editable digital interface is generated and ready
              for iteration or code export.
            </p>
          </Step>
        </Stepper>
      </section>

      {/* 6. SHOWCASE */}
      <section className="showcase-section">
        <div className="section-eyebrow">Generated with Duiodle</div>
        <h2 className="section-heading">Choose Your Aesthetic</h2>
        <div className="theme-cards" data-ocid="showcase.list">
          {themeCards.map((card, i) => (
            <SpotlightCard
              className="theme-card"
              key={card.themeId}
              data-ocid={`showcase.item.${i + 1}`}
            >
              <div
                className="theme-card-visual"
                style={{ background: card.gradient }}
              >
                <div className="theme-card-ui-hint">
                  <div className="ui-hint-bar" />
                  <div className="ui-hint-bar ui-hint-bar--short" />
                  <div className="ui-hint-grid">
                    <div className="ui-hint-block" />
                    <div className="ui-hint-block" />
                  </div>
                </div>
              </div>
              <div className="theme-card-body">
                <div className="theme-card-tag">{card.tag}</div>
                <h3
                  className="theme-card-title"
                  style={{ display: "flex", alignItems: "center", gap: "2px" }}
                >
                  {card.title}
                  <ThemeTooltip
                    themeId={card.themeId}
                    description={card.description}
                  />
                </h3>
                <p className="theme-card-desc">{card.description}</p>
              </div>
            </SpotlightCard>
          ))}
        </div>
      </section>

      {/* 7. CTA */}
      <section className="cta-section">
        <p className="cta-eyebrow">Ready to begin?</p>
        <h2 className="cta-heading">
          From imagination
          <br />
          to interface.
        </h2>
        <p className="cta-sub">Begin the transformation.</p>
        <SpotlightCard className="cta-btn-wrap">
          <button
            type="button"
            className="btn-primary"
            onClick={handleLaunchDuiodle}
            data-ocid="cta.primary_button"
          >
            Launch Duiodle
          </button>
        </SpotlightCard>
      </section>

      {/* 8. FOOTER */}
      <footer className="footer">
        <div className="footer-loop">
          {!workspaceOpen && (
            <CurvedLoop
              marqueeText="duiodle ✦ duiodle ✦ duiodle ✦ duiodle ✦ duiodle ✦"
              speed={1.5}
              curveAmount={80}
              interactive
            />
          )}
        </div>
        <div className="footer-bottom">
          <div className="footer-credits">
            Made with ♥ by Rishika &amp; Mousumi
          </div>
          <div className="footer-caffeine">
            © {new Date().getFullYear()} ·{" "}
            <a
              href={`https://caffeine.ai?utm_source=caffeine-footer&utm_medium=referral&utm_content=${encodeURIComponent(typeof window !== "undefined" ? window.location.hostname : "")}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              Built with caffeine.ai
            </a>
          </div>
        </div>
      </footer>

      <SystemStatus />
      <Toaster />
    </div>
  );
}
