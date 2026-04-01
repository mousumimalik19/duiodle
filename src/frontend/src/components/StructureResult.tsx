import {
  Check,
  ChevronLeft,
  ChevronRight,
  Code2,
  Columns2,
  Copy,
  Download,
  ExternalLink,
  Eye,
  Loader2,
  Maximize2,
  Monitor,
  PanelLeftClose,
  PanelLeftOpen,
  RefreshCw,
  RotateCcw,
  Smartphone,
  Tablet,
  Wand2,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type {
  DetectedElement,
  ParsedAnalysis,
} from "../hooks/useSketchAnalysis";

interface StructureResultProps {
  theme: "light" | "dark";
  panels: {
    bg: string;
    toolbar: string;
    border: string;
    text: string;
    textMuted: string;
  };
  onBack?: () => void;
  analysisData?: ParsedAnalysis | null;
  isAnalyzing?: boolean;
  analysisError?: string | null;
  isEdgeMode?: boolean;
}

type Variant = 0 | 1 | 2 | 3 | 4 | 5 | 6;
type CenterTab = "structure" | "code" | "preview" | "split";
type DeviceMode = "desktop" | "tablet" | "mobile";
type ThemeKey =
  | "Minimal"
  | "Brutalist"
  | "Glass"
  | "Modern SaaS"
  | "Playful"
  | "Monochrome"
  | "Animated";

// ── Theme Configs ─────────────────────────────────────────────

const THEME_CONFIGS: Record<
  ThemeKey,
  { label: string; css: string; description: string }
> = {
  Minimal: {
    label: "Minimal",
    css: "body { font-family: Inter, sans-serif; } * { border-radius: 6px; }",
    description: "Clean & neutral",
  },
  Brutalist: {
    label: "Brutalist",
    css: "* { border-radius: 0 !important; border: 2px solid #000 !important; box-shadow: none !important; } body { font-family: monospace; font-weight: 700; } button { background: #000 !important; color: #fff !important; }",
    description: "Bold & raw",
  },
  Glass: {
    label: "Glass",
    css: "body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); } .card, div[class*='bg-white'] { background: rgba(255,255,255,0.15) !important; backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.3) !important; }",
    description: "Translucent & airy",
  },
  "Modern SaaS": {
    label: "Modern SaaS",
    css: "* { border-radius: 12px; } body { font-family: Inter, sans-serif; } button { box-shadow: 0 2px 8px rgba(0,0,0,0.12); }",
    description: "Polished & scalable",
  },
  Playful: {
    label: "Playful",
    css: "body { font-family: 'Comic Sans MS', cursive; background: #fffbeb; } button { background: #f97316 !important; border-radius: 999px !important; } h1,h2,h3 { color: #7c3aed; }",
    description: "Fun & expressive",
  },
  Monochrome: {
    label: "Monochrome",
    css: "body { filter: grayscale(1); font-family: Georgia, serif; } * { border-color: #555 !important; }",
    description: "Single-tone focus",
  },
  Animated: {
    label: "Animated",
    css: `
      @keyframes fadeSlideUp {
        from { opacity: 0; transform: translateY(18px); }
        to   { opacity: 1; transform: translateY(0); }
      }
      @keyframes slideDown {
        from { opacity: 0; transform: translateY(-14px); }
        to   { opacity: 1; transform: translateY(0); }
      }
      @keyframes staggerReveal {
        from { opacity: 0; transform: translateY(10px) scale(0.98); }
        to   { opacity: 1; transform: translateY(0) scale(1); }
      }
      @keyframes scaleFade {
        from { opacity: 0; transform: scale(0.94); }
        to   { opacity: 1; transform: scale(1); }
      }
      nav { animation: slideDown 0.4s cubic-bezier(0.4,0,0.2,1) both; }
      section, main > * { animation: fadeSlideUp 0.5s cubic-bezier(0.4,0,0.2,1) both; }
      .card, [class*="rounded"] { animation: staggerReveal 0.4s cubic-bezier(0.4,0,0.2,1) both; }
      button { transition: transform 0.2s cubic-bezier(0.4,0,0.2,1), box-shadow 0.2s ease; }
      button:hover { transform: scale(1.03); box-shadow: 0 4px 14px rgba(0,0,0,0.12); }
      input:focus { transform: scaleX(1.01); transition: all 0.2s ease; outline: 2px solid #fbff29; }
    `,
    description: "Framer Motion — premium motion",
  },
};

// ── Motion System ─────────────────────────────────────────────

const MOTION_TOKENS: Record<string, string> = {
  motion_duration_fast: "0.2s",
  motion_duration_normal: "0.4s",
  motion_ease: "cubic-bezier(0.4, 0, 0.2, 1)",
  stagger_delay: "0.08s",
};

const ANIMATION_INTENSITY_MAP: Record<
  string,
  { scale: number; duration: number; blur: number }
> = {
  low: { scale: 1.01, duration: 0.6, blur: 0 },
  medium: { scale: 1.03, duration: 0.4, blur: 0 },
  high: { scale: 1.06, duration: 0.25, blur: 2 },
};

const SMART_ANIMATION_MAP: Record<string, string> = {
  navbar: "slide-down",
  card: "stagger-reveal",
  button: "hover-micro-scale",
  modal: "scale-fade",
  hero: "fade-slide-up",
  grid: "stagger-reveal",
  container: "fade-in",
  input: "focus-ring",
  form: "fade-slide-up",
  text: "fade-in",
  sidebar: "slide-right",
  section: "scroll-reveal",
};

// ── Mock Data ────────────────────────────────────────────────

interface VariantShape {
  label: string;
  editable_tree: object;
  design_tokens: Record<string, string>;
  motion_tokens?: Record<string, string>;
  analysis: {
    detected_components: string[];
    layout_type: string;
    auto_improvements: string[];
    confidence_score: number;
  };
  preview_html: string;
  code: string;
}

const VARIANTS: VariantShape[] = [
  // 0 — Dashboard card layout
  {
    label: "Dashboard Cards",
    design_tokens: {
      background: "#ffffff",
      text: "#111111",
      primary: "#fbff29",
      border_radius: "12px",
      font_family: "Inter, sans-serif",
      shadow: "0 1px 3px rgba(0,0,0,0.08)",
    },
    analysis: {
      detected_components: ["card", "navbar", "grid", "button", "badge"],
      layout_type: "grid-3col",
      auto_improvements: [
        "Added responsive 3-column grid",
        "Improved card spacing hierarchy",
        "Enhanced typography contrast",
      ],
      confidence_score: 0.92,
    },
    editable_tree: {
      type: "container",
      id: "root",
      confidence: 0.92,
      layout: { direction: "column", gap: 24, padding: 0 },
      theme: {
        variant: "minimal",
        tokens: { background: "#ffffff", text: "#111" },
      },
      children: [
        {
          type: "navbar",
          id: "nav-001",
          props: { label: "AppDash", style: "minimal" },
          layout: { direction: "row", gap: 16, padding: "0 24px" },
          children: [],
        },
        {
          type: "grid",
          id: "grid-001",
          props: { columns: 3 },
          layout: { direction: "row", gap: 16, padding: "24px" },
          children: [
            {
              type: "card",
              id: "card-001",
              props: { label: "Total Revenue", value: "$48,200" },
              children: [],
            },
            {
              type: "card",
              id: "card-002",
              props: { label: "Active Users", value: "1,340" },
              children: [],
            },
            {
              type: "card",
              id: "card-003",
              props: { label: "Conversion", value: "3.8%" },
              children: [],
            },
          ],
        },
      ],
    },
    preview_html: `<html><head><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-gray-50 font-sans">
<nav class="flex items-center justify-between px-8 py-4 bg-white border-b border-gray-200">
  <span class="font-bold text-lg tracking-tight">AppDash</span>
  <div class="flex gap-3">
    <a href="#" class="text-sm text-gray-500 hover:text-black">Overview</a>
    <a href="#" class="text-sm text-gray-500 hover:text-black">Reports</a>
    <a href="#" class="text-sm text-gray-500 hover:text-black">Settings</a>
  </div>
  <button class="bg-black text-white text-sm px-4 py-1.5 rounded-md">New Report</button>
</nav>
<div class="p-8">
  <h1 class="text-2xl font-bold mb-6">Dashboard</h1>
  <div class="grid grid-cols-3 gap-5 mb-8">
    <div class="bg-white rounded-xl border border-gray-200 p-6">
      <p class="text-xs text-gray-400 mb-1 uppercase tracking-wide">Total Revenue</p>
      <p class="text-3xl font-bold">$48,200</p>
      <p class="text-sm text-green-500 mt-1">▲ 12% this month</p>
    </div>
    <div class="bg-white rounded-xl border border-gray-200 p-6">
      <p class="text-xs text-gray-400 mb-1 uppercase tracking-wide">Active Users</p>
      <p class="text-3xl font-bold">1,340</p>
      <p class="text-sm text-blue-500 mt-1">▲ 5% this week</p>
    </div>
    <div class="bg-white rounded-xl border border-gray-200 p-6">
      <p class="text-xs text-gray-400 mb-1 uppercase tracking-wide">Conversion</p>
      <p class="text-3xl font-bold">3.8%</p>
      <p class="text-sm text-gray-400 mt-1">— Stable</p>
    </div>
  </div>
  <div class="bg-white rounded-xl border border-gray-200 p-6">
    <h2 class="font-semibold mb-4">Recent Activity</h2>
    <div class="space-y-3">
      <div class="flex justify-between text-sm border-b border-gray-100 pb-2"><span>User signed up</span><span class="text-gray-400">2 min ago</span></div>
      <div class="flex justify-between text-sm border-b border-gray-100 pb-2"><span>Report generated</span><span class="text-gray-400">15 min ago</span></div>
      <div class="flex justify-between text-sm"><span>Payment received</span><span class="text-gray-400">1 hr ago</span></div>
    </div>
  </div>
</div></body></html>`,
    code: `import React from 'react';

const DashboardCards = () => {
  const stats = [
    { label: 'Total Revenue', value: '$48,200', change: '▲ 12%', color: 'text-green-500' },
    { label: 'Active Users', value: '1,340', change: '▲ 5%', color: 'text-blue-500' },
    { label: 'Conversion', value: '3.8%', change: '— Stable', color: 'text-gray-400' },
  ];
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="flex items-center justify-between px-8 py-4 bg-white border-b border-gray-200">
        <span className="font-bold text-lg tracking-tight">AppDash</span>
        <div className="flex gap-3">
          {['Overview', 'Reports', 'Settings'].map(item => (
            <a key={item} href="#" className="text-sm text-gray-500 hover:text-black">{item}</a>
          ))}
        </div>
        <button className="bg-black text-white text-sm px-4 py-1.5 rounded-md">
          New Report
        </button>
      </nav>
      <div className="p-8">
        <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
        <div className="grid grid-cols-3 gap-5 mb-8">
          {stats.map(stat => (
            <div key={stat.label} className="bg-white rounded-xl border border-gray-200 p-6">
              <p className="text-xs text-gray-400 mb-1 uppercase tracking-wide">{stat.label}</p>
              <p className="text-3xl font-bold">{stat.value}</p>
              <p className={\`text-sm mt-1 \${stat.color}\`}>{stat.change}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DashboardCards;`,
  },
  // 1 — Login form
  {
    label: "Login Form",
    design_tokens: {
      background: "#f9f9f9",
      text: "#111111",
      primary: "#000000",
      border_radius: "8px",
      font_family: "Inter, sans-serif",
      shadow: "0 2px 8px rgba(0,0,0,0.06)",
    },
    analysis: {
      detected_components: ["form", "input", "button", "container", "label"],
      layout_type: "flex-column",
      auto_improvements: [
        "Centered card layout for focus",
        "Added accessible label hierarchy",
        "Improved input spacing",
      ],
      confidence_score: 0.88,
    },
    editable_tree: {
      type: "container",
      id: "root",
      children: [],
    },
    preview_html: `<html><head><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-gray-100 min-h-screen flex items-center justify-center font-sans">
<div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-10 w-full max-w-sm">
  <h2 class="text-2xl font-bold mb-1">Welcome back</h2>
  <p class="text-sm text-gray-400 mb-8">Sign in to your Duiodle workspace.</p>
  <div class="space-y-5">
    <div>
      <label class="block text-xs font-medium text-gray-500 mb-1.5">Email</label>
      <input type="email" placeholder="hello@duiodle.ai" class="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm outline-none focus:border-black" />
    </div>
    <div>
      <label class="block text-xs font-medium text-gray-500 mb-1.5">Password</label>
      <input type="password" placeholder="••••••••" class="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm outline-none focus:border-black" />
    </div>
    <button class="w-full bg-black text-white rounded-lg py-2.5 text-sm font-medium hover:bg-gray-900 transition">Sign In</button>
  </div>
  <p class="text-center text-xs text-gray-400 mt-6">Don't have an account? <a href="#" class="text-black underline">Sign up</a></p>
</div></body></html>`,
    code: `import React, { useState } from 'react';

const LoginForm = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-10 w-full max-w-sm">
        <h2 className="text-2xl font-bold mb-1">Welcome back</h2>
        <p className="text-sm text-gray-400 mb-8">Sign in to your workspace.</p>
        <div className="space-y-5">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="hello@duiodle.ai" className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm outline-none focus:border-black" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm outline-none focus:border-black" />
          </div>
          <button className="w-full bg-black text-white rounded-lg py-2.5 text-sm font-medium">Sign In</button>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;`,
  },
  // 2 — Navbar + Hero
  {
    label: "Navbar + Hero",
    design_tokens: {
      background: "#ffffff",
      text: "#111111",
      primary: "#fbff29",
      border_radius: "9999px",
      font_family: "Inter, sans-serif",
      shadow: "none",
    },
    analysis: {
      detected_components: ["navbar", "hero", "button", "text", "container"],
      layout_type: "flex-column",
      auto_improvements: [
        "Full-bleed hero section",
        "Pill-style CTA buttons",
        "Improved typographic scale",
      ],
      confidence_score: 0.85,
    },
    editable_tree: {
      type: "container",
      id: "root",
      children: [],
    },
    preview_html: `<html><head><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-white font-sans">
<nav class="flex items-center justify-between px-10 py-5 border-b border-gray-100">
  <span class="font-black text-xl tracking-tight">Duiodle</span>
  <div class="flex gap-6 text-sm text-gray-500">
    <a href="#">Product</a><a href="#">Docs</a><a href="#">Pricing</a>
  </div>
  <button class="bg-black text-white px-5 py-2 text-sm rounded-full">Get started →</button>
</nav>
<section class="px-10 pt-24 pb-16 max-w-3xl">
  <p class="text-xs text-gray-400 uppercase tracking-widest mb-4">AI-Powered Design Tool</p>
  <h1 class="text-6xl font-black leading-none mb-6">Doodles become<br/>interfaces.</h1>
  <p class="text-lg text-gray-400 max-w-lg mb-10">Sketch your UI by hand. Watch it transform into production-ready React code in seconds.</p>
  <div class="flex gap-4">
    <button class="bg-black text-white px-7 py-3 rounded-full text-sm font-medium">Start for free</button>
    <button class="border border-gray-200 text-sm px-7 py-3 rounded-full text-gray-600">See it in action</button>
  </div>
</section>
</body></html>`,
    code: `import React from 'react';

const NavHero = () => (
  <div className="min-h-screen bg-white">
    <nav className="flex items-center justify-between px-10 py-5 border-b border-gray-100">
      <span className="font-black text-xl tracking-tight">Duiodle</span>
      <div className="flex gap-6 text-sm text-gray-500">
        {['Product', 'Docs', 'Pricing'].map(link => (
          <a key={link} href="#" className="hover:text-black transition">{link}</a>
        ))}
      </div>
      <button className="bg-black text-white px-5 py-2 text-sm rounded-full">Get started →</button>
    </nav>
    <section className="px-10 pt-24 pb-16 max-w-3xl">
      <p className="text-xs text-gray-400 uppercase tracking-widest mb-4">AI-Powered Design Tool</p>
      <h1 className="text-6xl font-black leading-none mb-6">Doodles become<br/>interfaces.</h1>
      <p className="text-lg text-gray-400 max-w-lg mb-10">Sketch your UI by hand. Watch it transform.</p>
      <div className="flex gap-4">
        <button className="bg-black text-white px-7 py-3 rounded-full text-sm font-medium">Start for free</button>
        <button className="border border-gray-200 text-sm px-7 py-3 rounded-full text-gray-600">See it in action</button>
      </div>
    </section>
  </div>
);

export default NavHero;`,
  },
  // 3 — Settings panel
  {
    label: "Settings Panel",
    design_tokens: {
      background: "#fafafa",
      text: "#111111",
      primary: "#000000",
      border_radius: "8px",
      font_family: "Inter, sans-serif",
      shadow: "none",
    },
    analysis: {
      detected_components: [
        "sidebar",
        "input",
        "switch",
        "select",
        "button",
        "section",
      ],
      layout_type: "flex-row",
      auto_improvements: [
        "Sidebar navigation with active state",
        "Form field label consistency",
        "Structured section headers",
      ],
      confidence_score: 0.79,
    },
    editable_tree: {
      type: "container",
      id: "root",
      children: [],
    },
    preview_html: `<html><head><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-gray-50 font-sans flex h-screen">
<aside class="w-52 border-r border-gray-200 bg-white pt-8 flex-shrink-0">
  <p class="text-xs text-gray-400 uppercase tracking-widest px-5 mb-3">Settings</p>
  <ul>
    <li class="px-5 py-2 text-sm font-medium bg-gray-100 rounded-r-full text-black">General</li>
    <li class="px-5 py-2 text-sm text-gray-500">Appearance</li>
    <li class="px-5 py-2 text-sm text-gray-500">Notifications</li>
    <li class="px-5 py-2 text-sm text-gray-500">Security</li>
  </ul>
</aside>
<main class="flex-1 p-10">
  <h2 class="text-xl font-bold mb-8">General</h2>
  <div class="max-w-md space-y-6">
    <div>
      <label class="block text-xs font-medium text-gray-500 mb-1.5">Display Name</label>
      <input value="Alex Mercer" class="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm bg-white outline-none" />
    </div>
    <div>
      <label class="block text-xs font-medium text-gray-500 mb-1.5">Email</label>
      <input value="alex@duiodle.ai" class="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm bg-white outline-none" />
    </div>
    <button class="bg-black text-white rounded-lg px-5 py-2.5 text-sm">Save Changes</button>
  </div>
</main></body></html>`,
    code: `import React from 'react';

const SettingsPanel = () => (
  <div className="flex h-screen bg-gray-50">
    <aside className="w-52 border-r border-gray-200 bg-white pt-8">
      <p className="text-xs text-gray-400 uppercase tracking-widest px-5 mb-3">Settings</p>
      <ul>
        {['General', 'Appearance', 'Notifications', 'Security'].map((item, i) => (
          <li key={item} className={\`px-5 py-2 text-sm \${i === 0 ? 'font-medium bg-gray-100 text-black' : 'text-gray-500'}\`}>{item}</li>
        ))}
      </ul>
    </aside>
    <main className="flex-1 p-10">
      <h2 className="text-xl font-bold mb-8">General</h2>
      <div className="max-w-md space-y-6">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1.5">Display Name</label>
          <input defaultValue="Alex Mercer" className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm outline-none" />
        </div>
        <button className="bg-black text-white rounded-lg px-5 py-2.5 text-sm">Save Changes</button>
      </div>
    </main>
  </div>
);

export default SettingsPanel;`,
  },
  // 4 — Pricing table
  {
    label: "Pricing Table",
    design_tokens: {
      background: "#ffffff",
      text: "#111111",
      primary: "#fbff29",
      border_radius: "16px",
      font_family: "Inter, sans-serif",
      shadow: "0 4px 16px rgba(0,0,0,0.06)",
    },
    analysis: {
      detected_components: [
        "card",
        "button",
        "list",
        "badge",
        "container",
        "text",
      ],
      layout_type: "grid-3col",
      auto_improvements: [
        "Featured tier visual highlight",
        "Clear pricing hierarchy",
        "CTA button contrast optimized",
      ],
      confidence_score: 0.94,
    },
    editable_tree: {
      type: "container",
      id: "root",
      children: [],
    },
    preview_html: `<html><head><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-white font-sans">
<div class="py-20 px-10">
  <div class="text-center mb-14">
    <h1 class="text-5xl font-black mb-3">Simple pricing.</h1>
    <p class="text-gray-400">No surprises. Cancel anytime.</p>
  </div>
  <div class="grid grid-cols-3 gap-6 max-w-4xl mx-auto">
    <div class="border border-gray-200 rounded-2xl p-8">
      <p class="text-sm text-gray-400 mb-2">Free</p>
      <p class="text-4xl font-black mb-6">$0<span class="text-lg font-normal text-gray-400">/mo</span></p>
      <ul class="space-y-2 text-sm text-gray-600 mb-8"><li>✓ 5 projects</li><li>✓ PNG export</li></ul>
      <button class="w-full border border-gray-300 rounded-lg py-2.5 text-sm">Get started</button>
    </div>
    <div class="border-2 border-black rounded-2xl p-8 relative">
      <span class="absolute -top-3 left-1/2 -translate-x-1/2 bg-black text-white text-xs px-3 py-1 rounded-full">Popular</span>
      <p class="text-sm text-gray-400 mb-2">Pro</p>
      <p class="text-4xl font-black mb-6">$19<span class="text-lg font-normal text-gray-400">/mo</span></p>
      <ul class="space-y-2 text-sm text-gray-600 mb-8"><li>✓ Unlimited projects</li><li>✓ Code export</li><li>✓ Theme engine</li></ul>
      <button class="w-full bg-black text-white rounded-lg py-2.5 text-sm">Start free trial</button>
    </div>
    <div class="border border-gray-200 rounded-2xl p-8">
      <p class="text-sm text-gray-400 mb-2">Team</p>
      <p class="text-4xl font-black mb-6">$49<span class="text-lg font-normal text-gray-400">/mo</span></p>
      <ul class="space-y-2 text-sm text-gray-600 mb-8"><li>✓ Everything in Pro</li><li>✓ Collaboration</li></ul>
      <button class="w-full border border-gray-300 rounded-lg py-2.5 text-sm">Contact us</button>
    </div>
  </div>
</div></body></html>`,
    code: `import React from 'react';

const tiers = [
  { name: 'Free', price: '$0', features: ['5 projects', 'PNG export'], featured: false, cta: 'Get started' },
  { name: 'Pro', price: '$19', features: ['Unlimited projects', 'Code export', 'Theme engine'], featured: true, cta: 'Start free trial' },
  { name: 'Team', price: '$49', features: ['Everything in Pro', 'Collaboration', 'Priority support'], featured: false, cta: 'Contact us' },
];

const PricingTable = () => (
  <div className="min-h-screen bg-white py-20 px-10">
    <div className="text-center mb-14">
      <h1 className="text-5xl font-black mb-3">Simple pricing.</h1>
      <p className="text-gray-400">No surprises. Cancel anytime.</p>
    </div>
    <div className="grid grid-cols-3 gap-6 max-w-4xl mx-auto">
      {tiers.map(tier => (
        <div key={tier.name} className={\`rounded-2xl p-8 relative \${tier.featured ? 'border-2 border-black' : 'border border-gray-200'}\`}>
          {tier.featured && <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-black text-white text-xs px-3 py-1 rounded-full">Popular</span>}
          <p className="text-sm text-gray-400 mb-2">{tier.name}</p>
          <p className="text-4xl font-black mb-6">{tier.price}<span className="text-lg font-normal text-gray-400">/mo</span></p>
          <ul className="space-y-2 text-sm text-gray-600 mb-8">{tier.features.map(f => <li key={f}>✓ {f}</li>)}</ul>
          <button className={\`w-full rounded-lg py-2.5 text-sm \${tier.featured ? 'bg-black text-white' : 'border border-gray-300'}\`}>{tier.cta}</button>
        </div>
      ))}
    </div>
  </div>
);

export default PricingTable;`,
  },
  // 5 — Blog article card
  {
    label: "Blog Article Card",
    design_tokens: {
      background: "#f8f8f8",
      text: "#111111",
      primary: "#fbff29",
      border_radius: "16px",
      font_family: "Karla, sans-serif",
      shadow: "0 2px 6px rgba(0,0,0,0.05)",
    },
    analysis: {
      detected_components: [
        "card",
        "image",
        "text",
        "badge",
        "button",
        "avatar",
      ],
      layout_type: "stacked",
      auto_improvements: [
        "Article card with image region",
        "Category badge styling",
        "Author metadata section added",
      ],
      confidence_score: 0.81,
    },
    editable_tree: {
      type: "container",
      id: "root",
      children: [],
    },
    preview_html: `<html><head><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-gray-50 font-sans p-10">
<div class="max-w-2xl mx-auto space-y-6">
  <h2 class="text-xl font-bold">Latest Articles</h2>
  <article class="bg-white rounded-2xl border border-gray-200 overflow-hidden">
    <div class="h-48 bg-gradient-to-br from-yellow-200 to-yellow-50 flex items-center justify-center">
      <span class="text-4xl">✏️</span>
    </div>
    <div class="p-6">
      <span class="text-xs bg-yellow-100 text-yellow-700 px-2.5 py-1 rounded-full font-medium">Design Systems</span>
      <h3 class="text-lg font-bold mt-3 mb-2">Turning Doodles into Interfaces</h3>
      <p class="text-sm text-gray-500 leading-relaxed mb-4">How Duiodle uses computer vision to produce component hierarchies from hand-drawn sketches.</p>
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-full bg-black text-white flex items-center justify-center text-xs font-bold">AM</div>
          <span class="text-xs text-gray-400">Alex Mercer · Mar 24, 2026</span>
        </div>
        <a href="#" class="text-xs font-medium text-black">Read more →</a>
      </div>
    </div>
  </article>
</div></body></html>`,
    code: `import React from 'react';

const BlogCards = () => (
  <div className="min-h-screen bg-gray-50 p-10">
    <div className="max-w-2xl mx-auto space-y-6">
      <h2 className="text-xl font-bold">Latest Articles</h2>
      <article className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
        <div className="h-48 bg-gradient-to-br from-yellow-200 to-yellow-50 flex items-center justify-center">
          <span className="text-4xl">✏️</span>
        </div>
        <div className="p-6">
          <span className="text-xs bg-yellow-100 text-yellow-700 px-2.5 py-1 rounded-full font-medium">Design Systems</span>
          <h3 className="text-lg font-bold mt-3 mb-2">Turning Doodles into Interfaces</h3>
          <p className="text-sm text-gray-500 leading-relaxed mb-4">How Duiodle uses computer vision to produce component hierarchies from sketches.</p>
        </div>
      </article>
    </div>
  </div>
);

export default BlogCards;`,
  },
  {
    label: "Animated SaaS",
    design_tokens: {
      background: "#0f0f0f",
      text: "#ffffff",
      primary: "#fbff29",
      border_radius: "14px",
      font_family: "Inter, sans-serif",
      shadow: "0 8px 32px rgba(0,0,0,0.3)",
    },
    motion_tokens: MOTION_TOKENS,
    analysis: {
      detected_components: ["navbar", "hero", "card", "button", "section"],
      layout_type: "flex-column",
      auto_improvements: [
        "Entry animations on all sections",
        "Stagger reveal for card grid",
        "Hover micro-scale on buttons",
        "Slide-down navbar choreography",
      ],
      confidence_score: 0.96,
    },
    editable_tree: {
      type: "container",
      id: "root",
      confidence: 0.96,
      layout: { direction: "column", gap: 0, padding: 0 },
      theme: {
        variant: "animated",
        tokens: { background: "#0f0f0f", text: "#fff", accent: "#fbff29" },
      },
      children: [],
    },
    preview_html: `<html><head><script src="https://cdn.tailwindcss.com"><\/script><style>
@keyframes fadeSlideUp { from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)} }
@keyframes slideDown   { from{opacity:0;transform:translateY(-16px)}to{opacity:1;transform:translateY(0)} }
@keyframes stagger0    { from{opacity:0;transform:translateY(12px) scale(0.97)}to{opacity:1;transform:translateY(0) scale(1)} }
nav{animation:slideDown .45s cubic-bezier(.4,0,.2,1) both}
.hero{animation:fadeSlideUp .55s cubic-bezier(.4,0,.2,1) .1s both}
.card1{animation:stagger0 .4s cubic-bezier(.4,0,.2,1) .2s both}
.card2{animation:stagger0 .4s cubic-bezier(.4,0,.2,1) .3s both}
.card3{animation:stagger0 .4s cubic-bezier(.4,0,.2,1) .4s both}
button{transition:transform .2s ease,box-shadow .2s ease}
button:hover{transform:scale(1.04);box-shadow:0 6px 20px rgba(0,0,0,.3)}
input:focus{outline:2px solid #fbff29;outline-offset:2px;transform:scaleX(1.01);transition:all .2s ease}
<\/style><\/head><body style="background:#0f0f0f;color:#fff;font-family:Inter,sans-serif;margin:0">
<nav style="display:flex;align-items:center;justify-content:space-between;padding:20px 40px;border-bottom:1px solid rgba(255,255,255,.08)">
  <span style="font-weight:900;font-size:1.1rem;letter-spacing:-.02em">Duiodle<\/span>
  <div style="display:flex;gap:24px;font-size:.85rem;color:rgba(255,255,255,.5)">
    <a href="#" style="color:inherit;text-decoration:none">Product<\/a>
    <a href="#" style="color:inherit;text-decoration:none">Docs<\/a>
    <a href="#" style="color:inherit;text-decoration:none">Pricing<\/a>
  <\/div>
  <button style="background:#fbff29;color:#111;border:none;padding:8px 20px;border-radius:999px;font-size:.82rem;font-weight:700;cursor:pointer">Get started<\/button>
<\/nav>
<div class="hero" style="padding:90px 40px 60px;max-width:760px">
  <p style="font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:rgba(255,255,255,.35);margin-bottom:16px">Motion-first design<\/p>
  <h1 style="font-size:3.8rem;font-weight:900;line-height:1.05;margin:0 0 20px;letter-spacing:-.03em">Doodles become<br\/><span style="color:#fbff29">interfaces.<\/span><\/h1>
  <p style="color:rgba(255,255,255,.5);max-width:480px;line-height:1.7;margin:0 0 36px;font-size:1rem">Sketch your UI by hand. Watch it transform into a production-ready animated interface.<\/p>
  <div style="display:flex;gap:12px">
    <button style="background:#fbff29;color:#111;border:none;padding:14px 32px;border-radius:999px;font-size:.88rem;font-weight:700;cursor:pointer">Start for free<\/button>
    <button style="background:transparent;color:#fff;border:1px solid rgba(255,255,255,.2);padding:14px 32px;border-radius:999px;font-size:.88rem;cursor:pointer">See it in action<\/button>
  <\/div>
<\/div>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;padding:0 40px 60px">
  <div class="card1" style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:24px">
    <p style="font-size:.7rem;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.1em;margin:0 0 8px">Total Revenue<\/p>
    <p style="font-size:2rem;font-weight:900;margin:0 0 4px">$48,200<\/p>
    <p style="font-size:.8rem;color:#4ade80;margin:0">12% this month<\/p>
  <\/div>
  <div class="card2" style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:24px">
    <p style="font-size:.7rem;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.1em;margin:0 0 8px">Active Users<\/p>
    <p style="font-size:2rem;font-weight:900;margin:0 0 4px">1,340<\/p>
    <p style="font-size:.8rem;color:#60a5fa;margin:0">5% this week<\/p>
  <\/div>
  <div class="card3" style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:24px">
    <p style="font-size:.7rem;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.1em;margin:0 0 8px">Conversion<\/p>
    <p style="font-size:2rem;font-weight:900;margin:0 0 4px">3.8%<\/p>
    <p style="font-size:.8rem;color:rgba(255,255,255,.35);margin:0">Stable<\/p>
  <\/div>
<\/div>
<\/body><\/html>`,
    code: `import React from 'react';

const motionTokens = {
  durationFast: '0.2s',
  durationNormal: '0.4s',
  ease: 'cubic-bezier(0.4, 0, 0.2, 1)',
  staggerDelay: '0.08s',
};

const stats = [
  { label: 'Total Revenue', value: '$48,200', change: '+12%', color: '#4ade80', delay: '0.2s' },
  { label: 'Active Users',  value: '1,340',   change: '+5%',  color: '#60a5fa', delay: '0.3s' },
  { label: 'Conversion',    value: '3.8%',    change: 'Stable', color: 'rgba(255,255,255,0.35)', delay: '0.4s' },
];

const AnimatedSaaS = () => (
  <div style={{ minHeight: '100vh', background: '#0f0f0f', color: '#fff', fontFamily: 'Inter, sans-serif' }}>
    <style>{\`
      @keyframes fadeSlideUp { from { opacity:0;transform:translateY(18px) } to { opacity:1;transform:translateY(0) } }
      @keyframes slideDown { from { opacity:0;transform:translateY(-14px) } to { opacity:1;transform:translateY(0) } }
      @keyframes staggerCard { from { opacity:0;transform:translateY(10px) scale(0.97) } to { opacity:1;transform:translateY(0) scale(1) } }
      .animated-btn { transition: transform 0.2s ease, box-shadow 0.2s ease; }
      .animated-btn:hover { transform: scale(1.04); box-shadow: 0 6px 20px rgba(0,0,0,0.4); }
    \`}<\/style>
    <nav style={{ display:'flex',alignItems:'center',justifyContent:'space-between',padding:'20px 40px',borderBottom:'1px solid rgba(255,255,255,0.08)',animation:\`slideDown \${motionTokens.durationNormal} \${motionTokens.ease} both\` }}>
      <span style={{ fontWeight:900 }}>Duiodle<\/span>
      <button className="animated-btn" style={{ background:'#fbff29',color:'#111',border:'none',padding:'8px 20px',borderRadius:999,fontWeight:700,cursor:'pointer' }}>Get started<\/button>
    <\/nav>
    <section style={{ padding:'90px 40px 60px',maxWidth:760,animation:\`fadeSlideUp 0.55s \${motionTokens.ease} 0.1s both\` }}>
      <h1 style={{ fontSize:'3.8rem',fontWeight:900,lineHeight:1.05,margin:'0 0 20px' }}>Doodles become<br\/><span style={{ color:'#fbff29' }}>interfaces.<\/span><\/h1>
      <div style={{ display:'flex',gap:12 }}>
        <button className="animated-btn" style={{ background:'#fbff29',color:'#111',border:'none',padding:'14px 32px',borderRadius:999,fontWeight:700,cursor:'pointer' }}>Start for free<\/button>
        <button className="animated-btn" style={{ background:'transparent',color:'#fff',border:'1px solid rgba(255,255,255,0.2)',padding:'14px 32px',borderRadius:999,cursor:'pointer' }}>See it in action<\/button>
      <\/div>
    <\/section>
    <div style={{ display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:16,padding:'0 40px 60px' }}>
      {stats.map(s => (
        <div key={s.label} style={{ background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.08)',borderRadius:16,padding:24,animation:\`staggerCard 0.4s \${motionTokens.ease} \${s.delay} both\` }}>
          <p style={{ fontSize:'0.7rem',color:'rgba(255,255,255,0.4)',textTransform:'uppercase',margin:'0 0 8px' }}>{s.label}<\/p>
          <p style={{ fontSize:'2rem',fontWeight:900,margin:'0 0 4px' }}>{s.value}<\/p>
          <p style={{ fontSize:'0.8rem',color:s.color,margin:0 }}>{s.change}<\/p>
        <\/div>
      ))}
    <\/div>
  <\/div>
);

export default AnimatedSaaS;`,
  },
];

// ── JSON Syntax Highlighter ───────────────────────────────────

function JsonHighlight({
  json,
  theme,
}: { json: string; theme: "light" | "dark" }) {
  const isDark = theme === "dark";
  const parts = json.split(
    /("[^"]*"(?=\s*:)|"[^"]*"|\b\d+\.?\d*\b|\btrue\b|\bfalse\b|\bnull\b)/g,
  );
  return (
    <>
      {parts.map((part, i) => {
        if (/^"[^"]*"$/.test(part) && i > 0) {
          const isKey = /"[^"]*"(?=\s*:)/.test(part);
          return (
            <span
              key={String(i)}
              style={{
                color: isKey
                  ? isDark
                    ? "#9cdcfe"
                    : "#0070c1"
                  : isDark
                    ? "#ce9178"
                    : "#a31515",
              }}
            >
              {part}
            </span>
          );
        }
        if (/^\d/.test(part))
          return (
            <span
              key={String(i)}
              style={{ color: isDark ? "#b5cea8" : "#098658" }}
            >
              {part}
            </span>
          );
        if (part === "true" || part === "false" || part === "null")
          return (
            <span
              key={String(i)}
              style={{ color: isDark ? "#569cd6" : "#0000ff" }}
            >
              {part}
            </span>
          );
        return <span key={String(i)}>{part}</span>;
      })}
    </>
  );
}

// ── JSX Syntax Highlighter ────────────────────────────────────

function JsxHighlight({
  code,
  theme,
}: { code: string; theme: "light" | "dark" }) {
  const isDark = theme === "dark";
  const parts = code.split(
    /(\/\/[^\n]*|\/\*[\s\S]*?\*\/|`[^`]*`|'[^']*'|"[^"]*"|<\/?[A-Za-z][A-Za-z0-9.]*|\b(?:import|export|default|const|let|var|function|return|if|else|for|while|class|extends|new|this|from|of|in|typeof|null|undefined|true|false)\b)/g,
  );
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith("//") || part.startsWith("/*"))
          return (
            <span
              key={String(i)}
              style={{ color: isDark ? "#6a9955" : "#008000" }}
            >
              {part}
            </span>
          );
        if (/^[`'"]/.test(part))
          return (
            <span
              key={String(i)}
              style={{ color: isDark ? "#ce9178" : "#a31515" }}
            >
              {part}
            </span>
          );
        if (/^<\/?[A-Za-z]/.test(part))
          return (
            <span
              key={String(i)}
              style={{ color: isDark ? "#4ec9b0" : "#267f99" }}
            >
              {part}
            </span>
          );
        if (
          /^\b(?:import|export|default|const|let|var|function|return|if|else|for|while|class|extends|new|this|from|of|in|typeof)\b/.test(
            part,
          )
        )
          return (
            <span
              key={String(i)}
              style={{ color: isDark ? "#569cd6" : "#0000ff" }}
            >
              {part}
            </span>
          );
        if (
          part === "null" ||
          part === "undefined" ||
          part === "true" ||
          part === "false"
        )
          return (
            <span
              key={String(i)}
              style={{ color: isDark ? "#569cd6" : "#0070c1" }}
            >
              {part}
            </span>
          );
        return <span key={String(i)}>{part}</span>;
      })}
    </>
  );
}

// ── Helpers ───────────────────────────────────────────────────

function buildIframeHtml(html: string, themeCss: string): string {
  if (!themeCss) return html;
  const injected = `<style id="duiodle-theme">${themeCss}</style>`;
  if (html.includes("</head>"))
    return html.replace("</head>", `${injected}</head>`);
  return injected + html;
}

// ── Main Component ────────────────────────────────────────────

// ── Color map for component types in the preview ────────────
const COMPONENT_COLORS: Record<string, string> = {
  nav: "#3b82f6",
  navbar: "#3b82f6",
  button: "#fbff29",
  input: "#22c55e",
  card: "#9ca3af",
  heading: "#a855f7",
  text: "#d1d5db",
  image: "#f97316",
  icon: "#ec4899",
  container: "#e5e7eb",
};

function buildAnalysisPreviewHtml(elements: DetectedElement[]): string {
  const boxes = elements
    .map((el) => {
      const color = COMPONENT_COLORS[el.component] ?? "#9ca3af";
      const safeLabel = (
        el.content ? `${el.component}: ${el.content}` : el.component
      )
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
      return (
        `<div style="position:absolute;left:${el.bounds.x / 10}%;top:${el.bounds.y / 10}%;` +
        `width:${el.bounds.w / 10}%;height:${el.bounds.h / 10}%;background:${color}22;border:2px solid ${color};` +
        `border-radius:4px;display:flex;align-items:center;justify-content:center;overflow:hidden;" title="${safeLabel}">` +
        `<span style="font-size:11px;font-weight:600;color:${color};padding:2px 4px;text-align:center;word-break:break-all;">${safeLabel}</span></div>`
      );
    })
    .join("");
  return `<html><head><style>body{margin:0;padding:12px;background:#fff;font-family:sans-serif;}.canvas{position:relative;width:100%;padding-top:100%;}</style></head><body><div class="canvas">${boxes}</div></body></html>`;
}

function buildAnalysisReactCode(elements: DetectedElement[]): string {
  const components = elements
    .map((el, i) => {
      const content = el.content ?? el.component;
      if (el.component === "input") {
        return `  <input key={${i}} placeholder="${content}" className="border rounded px-3 py-2 w-full" />`;
      }
      if (el.component === "button") {
        return `  <button key={${i}} className="bg-yellow-300 hover:bg-yellow-400 font-semibold px-4 py-2 rounded">${content}</button>`;
      }
      return `  <div key={${i}} className="p-4 border rounded">${content}</div>`;
    })
    .join("\n");
  return `import React from "react";

export default function GeneratedUI() {
  return (
    <div className="flex flex-col gap-4 p-6">
${components}
    </div>
  );
}
`;
}

export default function StructureResult({
  theme,
  panels,
  onBack,
  analysisData,
  isAnalyzing,
  analysisError,
  isEdgeMode,
}: StructureResultProps) {
  const [variantIdx, setVariantIdx] = useState<Variant>(0);
  const [centerTab, setCenterTab] = useState<CenterTab>("split");
  const [deviceMode, setDeviceMode] = useState<DeviceMode>("desktop");
  const [selectedTheme, setSelectedTheme] = useState<ThemeKey>("Minimal");
  const [regenerating, setRegenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [refinePrompt, setRefinePrompt] = useState("");
  const [applying, setApplying] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [toastMsg, setToastMsg] = useState("UI Updated");
  const [iframeKey, setIframeKey] = useState(0);
  const [themeChanging, setThemeChanging] = useState(false);
  const [iframeOpacity, setIframeOpacity] = useState(1);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [uiTreeOpen, setUiTreeOpen] = useState(false);
  const [projectName, setProjectName] = useState("My Project");
  const [editingName, setEditingName] = useState(false);
  const [generatedTime] = useState(() =>
    (Math.random() * 1.2 + 1.2).toFixed(1),
  );
  const [animationIntensity, setAnimationIntensity] = useState<
    "low" | "medium" | "high"
  >("medium");
  const [prototypeMode, setPrototypeMode] = useState(false);
  const [animationMode, setAnimationMode] = useState<"static" | "animated">(
    "static",
  );
  const [exportDropdownOpen, setExportDropdownOpen] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement | null>(null);
  const nameInputRef = useRef<HTMLInputElement | null>(null);

  const variant = VARIANTS[variantIdx];

  // Override variant with real analysis data when available
  const effectiveVariant: VariantShape = analysisData
    ? {
        ...variant,
        editable_tree: {
          type: "container",
          id: "root",
          children: analysisData.detected_elements.map((el) => ({
            type: el.component,
            id: `${el.component}_${el.bounds.x}_${el.bounds.y}`,
            content: el.content ?? "",
            bounds: el.bounds,
            children: el.children ?? [],
          })),
        },
        analysis: {
          detected_components: analysisData.analysis.detected_components,
          layout_type: analysisData.analysis.layout_type,
          auto_improvements: analysisData.analysis.auto_improvements,
          confidence_score: analysisData.analysis.confidence,
        },
        preview_html: buildAnalysisPreviewHtml(analysisData.detected_elements),
        code: buildAnalysisReactCode(analysisData.detected_elements),
      }
    : variant;

  const col = panels;
  const yellow = "#fbff29";
  const mono = "'Fira Code', 'Courier New', monospace";

  const deviceWidth: Record<DeviceMode, string> = {
    desktop: "100%",
    tablet: "768px",
    mobile: "375px",
  };

  const nextVariant = useCallback(() => {
    setVariantIdx((prev) => ((prev + 1) % VARIANTS.length) as Variant);
    setIframeKey((k) => k + 1);
  }, []);

  const fireToast = useCallback((msg: string) => {
    setToastMsg(msg);
    setShowToast(true);
    setTimeout(() => setShowToast(false), 2500);
  }, []);

  const handleRegenerate = useCallback(() => {
    setRegenerating(true);
    setTimeout(() => {
      nextVariant();
      setRegenerating(false);
      fireToast("UI Updated");
    }, 1200);
  }, [nextVariant, fireToast]);

  const handleApply = useCallback(() => {
    if (!refinePrompt.trim()) return;
    setApplying(true);
    setTimeout(() => {
      nextVariant();
      setApplying(false);
      setRefinePrompt("");
      fireToast("Prompt Applied");
    }, 1500);
  }, [refinePrompt, nextVariant, fireToast]);

  const handleCopy = useCallback(() => {
    const text =
      centerTab === "structure"
        ? JSON.stringify(effectiveVariant.editable_tree, null, 2)
        : effectiveVariant.code;
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [centerTab, effectiveVariant]);

  const handleDownload = useCallback(() => {
    const content =
      centerTab === "structure"
        ? JSON.stringify(effectiveVariant.editable_tree, null, 2)
        : effectiveVariant.code;
    const ext = centerTab === "structure" ? ".json" : ".tsx";
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${effectiveVariant.label.replace(/\s+/g, "_").toLowerCase()}${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  }, [effectiveVariant, centerTab]);

  const openInNewTab = useCallback(() => {
    const win = window.open();
    if (win) {
      win.document.write(effectiveVariant.preview_html);
      win.document.close();
    }
  }, [effectiveVariant.preview_html]);

  const handleFullscreen = useCallback(() => {
    iframeRef.current?.requestFullscreen?.();
  }, []);

  const handleThemeChange = useCallback(
    (newTheme: ThemeKey) => {
      if (newTheme === selectedTheme) return;
      setThemeChanging(true);
      setIframeOpacity(0);
      setTimeout(() => {
        setSelectedTheme(newTheme);
        setIframeKey((k) => k + 1);
        if (newTheme === "Animated") {
          setAnimationMode("animated");
        } else {
          setAnimationMode("static");
        }
        setTimeout(() => {
          setIframeOpacity(1);
          setThemeChanging(false);
          fireToast(
            newTheme === "Animated"
              ? "Animated Theme Applied \u2726"
              : `Theme Applied: ${newTheme}`,
          );
        }, 300);
      }, 300);
    },
    [selectedTheme, fireToast],
  );

  const jsonString = useMemo(
    () => JSON.stringify(effectiveVariant.editable_tree, null, 2),
    [effectiveVariant.editable_tree],
  );
  const codeLines = useMemo(
    () => effectiveVariant.code.split("\n"),
    [effectiveVariant.code],
  );
  const jsonLines = useMemo(() => jsonString.split("\n"), [jsonString]);

  const layoutType = effectiveVariant.analysis.layout_type;

  // Derive panel visibility from centerTab
  const showSidebar =
    sidebarOpen && (centerTab === "structure" || centerTab === "split");
  const showCode =
    centerTab === "structure" || centerTab === "code" || centerTab === "split";
  const showPreview = centerTab === "preview" || centerTab === "split";
  const showCodeLabel =
    centerTab === "structure" ? "Editable UI Tree" : "Generated Interface Code";
  const codeContent = centerTab === "structure" ? "json" : "jsx";

  const iframeHtml = useMemo(
    () =>
      buildIframeHtml(
        effectiveVariant.preview_html,
        THEME_CONFIGS[selectedTheme].css,
      ),
    [effectiveVariant.preview_html, selectedTheme],
  );

  // Close export dropdown on outside click
  useEffect(() => {
    if (!exportDropdownOpen) return;
    const handler = () => setExportDropdownOpen(false);
    document.addEventListener("click", handler, { capture: true });
    return () =>
      document.removeEventListener("click", handler, { capture: true });
  }, [exportDropdownOpen]);

  // UI Tree flattener for sidebar
  const flatNodes = useMemo(() => {
    const nodes: Array<{ id: string; type: string; depth: number }> = [];
    const walk = (node: Record<string, unknown>, depth: number) => {
      nodes.push({
        id: String(node.id ?? ""),
        type: String(node.type ?? ""),
        depth,
      });
      const children = node.children as Record<string, unknown>[] | undefined;
      if (Array.isArray(children)) for (const c of children) walk(c, depth + 1);
    };
    walk(effectiveVariant.editable_tree as Record<string, unknown>, 0);
    return nodes;
  }, [effectiveVariant.editable_tree]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        flex: 1,
        overflow: "hidden",
        background: col.bg,
        color: col.text,
        fontFamily: "Karla, sans-serif",
        position: "relative",
      }}
      data-ocid="structure.panel"
    >
      {/* ══ ANALYSIS ERROR BANNER ══ */}
      {analysisError && (
        <div
          style={{
            background: "#fee2e2",
            borderBottom: "1px solid #fca5a5",
            color: "#991b1b",
            padding: "8px 16px",
            fontSize: "13px",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
          data-ocid="structure.error_state"
        >
          <span style={{ fontWeight: 600 }}>Analysis error:</span>{" "}
          {analysisError}
        </div>
      )}

      {/* ══ GEMINI ANALYZING OVERLAY ══ */}
      {isAnalyzing && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            zIndex: 50,
            background:
              theme === "dark"
                ? "rgba(20,20,20,0.88)"
                : "rgba(255,255,255,0.88)",
            backdropFilter: "blur(4px)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: 16,
          }}
          data-ocid="structure.loading_state"
        >
          <svg
            width="40"
            height="40"
            viewBox="0 0 40 40"
            aria-label="Analyzing"
            role="img"
            style={{ animation: "spin 1s linear infinite" }}
          >
            <title>Analyzing</title>
            <circle
              cx="20"
              cy="20"
              r="16"
              fill="none"
              stroke="#fbff29"
              strokeWidth="3"
              strokeDasharray="60 40"
            />
          </svg>
          <p
            style={{
              fontFamily: "Karla, sans-serif",
              fontSize: "15px",
              color: col.text,
              fontWeight: 600,
            }}
          >
            Analyzing with Gemini Vision...
          </p>
          <style>
            {
              "@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }"
            }
          </style>
        </div>
      )}

      {/* ══ TOP TOOLBAR ══ */}
      <div
        style={{
          height: 56,
          minHeight: 56,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 14px",
          borderBottom: `1px solid ${col.border}`,
          background: col.toolbar,
          flexShrink: 0,
          gap: 10,
        }}
      >
        {/* LEFT */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            flex: "0 0 auto",
          }}
        >
          {/* Sidebar toggle */}
          <button
            type="button"
            onClick={() => setSidebarOpen((s) => !s)}
            title={sidebarOpen ? "Hide sidebar" : "Show sidebar"}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 28,
              height: 28,
              borderRadius: 6,
              border: `1px solid ${col.border}`,
              background: sidebarOpen ? "rgba(251,255,41,0.12)" : "transparent",
              cursor: "pointer",
              color: sidebarOpen ? yellow : col.textMuted,
            }}
            data-ocid="structure.toggle"
          >
            {sidebarOpen ? (
              <PanelLeftClose size={13} />
            ) : (
              <PanelLeftOpen size={13} />
            )}
          </button>

          {/* Back button */}
          <button
            type="button"
            onClick={onBack}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 4,
              background: "none",
              border: `1px solid ${col.border}`,
              borderRadius: 6,
              padding: "5px 10px",
              cursor: "pointer",
              color: col.textMuted,
              fontSize: "0.75rem",
              fontFamily: "Karla, sans-serif",
            }}
            data-ocid="structure.close_button"
          >
            <ChevronLeft size={13} />
            Back
          </button>

          {/* Editable project name */}
          {editingName ? (
            <input
              ref={nameInputRef}
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              onBlur={() => setEditingName(false)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === "Escape")
                  setEditingName(false);
              }}
              style={{
                fontFamily: "Montserrat, sans-serif",
                fontWeight: 600,
                fontSize: "0.82rem",
                color: col.text,
                background: col.bg,
                border: `1px solid ${yellow}`,
                borderRadius: 4,
                padding: "2px 7px",
                outline: "none",
                letterSpacing: "0.01em",
                minWidth: 80,
                maxWidth: 160,
              }}
              data-ocid="structure.input"
            />
          ) : (
            <button
              type="button"
              onClick={() => setEditingName(true)}
              title="Click to rename"
              style={{
                fontFamily: "Montserrat, sans-serif",
                fontWeight: 600,
                fontSize: "0.82rem",
                color: col.text,
                background: "none",
                border: "none",
                cursor: "text",
                letterSpacing: "0.01em",
                padding: "2px 4px",
                borderRadius: 4,
              }}
            >
              {projectName}
            </button>
          )}
        </div>

        {/* Edge Mode badge */}
        {isEdgeMode && (
          <span
            style={{
              background: "rgba(251, 255, 41, 0.12)",
              border: "1px solid rgba(251, 255, 41, 0.35)",
              color: "#fbff29",
              fontSize: "10px",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              borderRadius: "4px",
              padding: "2px 7px",
              fontFamily: "Karla, sans-serif",
              flexShrink: 0,
            }}
          >
            ⚡ Edge Mode
          </span>
        )}

        {/* CENTER: 4 Tabs */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 2,
            background: col.bg,
            border: `1px solid ${col.border}`,
            borderRadius: 8,
            padding: "3px",
            flex: "0 0 auto",
          }}
        >
          {(["structure", "code", "preview", "split"] as CenterTab[]).map(
            (tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setCenterTab(tab)}
                style={{
                  padding: "4px 13px",
                  borderRadius: 6,
                  border: "none",
                  cursor: "pointer",
                  fontFamily: "Montserrat, sans-serif",
                  fontWeight: centerTab === tab ? 700 : 400,
                  fontSize: "0.71rem",
                  letterSpacing: "0.03em",
                  background: centerTab === tab ? yellow : "transparent",
                  color: centerTab === tab ? "#111" : col.textMuted,
                  transition: "all 0.15s",
                  whiteSpace: "nowrap",
                }}
                data-ocid={`structure.${tab}.tab`}
              >
                {tab === "split"
                  ? "Split View"
                  : tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ),
          )}
        </div>

        {/* RIGHT */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            flex: "0 0 auto",
          }}
        >
          {/* Theme Selector */}
          <div style={{ position: "relative" }}>
            <select
              value={selectedTheme}
              onChange={(e) => handleThemeChange(e.target.value as ThemeKey)}
              disabled={themeChanging}
              style={{
                appearance: "none",
                background: col.bg,
                border: `1px solid ${col.border}`,
                borderRadius: 6,
                padding: "5px 28px 5px 10px",
                cursor: "pointer",
                color: col.text,
                fontSize: "0.72rem",
                fontFamily: "Montserrat, sans-serif",
                fontWeight: 600,
                outline: "none",
                height: 30,
                opacity: themeChanging ? 0.5 : 1,
              }}
              data-ocid="structure.select"
            >
              {(Object.keys(THEME_CONFIGS) as ThemeKey[]).map((k) => (
                <option key={k} value={k}>
                  {THEME_CONFIGS[k].label}
                </option>
              ))}
            </select>
            <ChevronRight
              size={11}
              style={{
                position: "absolute",
                right: 8,
                top: "50%",
                transform: "translateY(-50%) rotate(90deg)",
                color: col.textMuted,
                pointerEvents: "none",
              }}
            />
          </div>

          {/* Regenerate */}
          <button
            type="button"
            onClick={handleRegenerate}
            disabled={regenerating}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 5,
              padding: "5px 11px",
              borderRadius: 6,
              border: `1px solid ${yellow}`,
              background: regenerating
                ? "rgba(251,255,41,0.12)"
                : "rgba(251,255,41,0.08)",
              cursor: regenerating ? "not-allowed" : "pointer",
              color: theme === "dark" ? yellow : "#5a5500",
              fontSize: "0.72rem",
              fontFamily: "Montserrat, sans-serif",
              fontWeight: 600,
              letterSpacing: "0.03em",
              whiteSpace: "nowrap",
            }}
            data-ocid="structure.regenerate.button"
          >
            <Wand2
              size={11}
              style={{
                animation: regenerating ? "spin 0.7s linear infinite" : "none",
              }}
            />
            {regenerating ? "Generating…" : "Regenerate"}
          </button>

          {/* Animation Intensity — only when Animated theme */}
          {selectedTheme === "Animated" && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 2,
                background: col.bg,
                border: `1px solid ${col.border}`,
                borderRadius: 8,
                padding: "3px",
                flexShrink: 0,
              }}
            >
              {(["low", "medium", "high"] as const).map((level) => (
                <button
                  key={level}
                  type="button"
                  onClick={() => setAnimationIntensity(level)}
                  style={{
                    padding: "3px 9px",
                    borderRadius: 6,
                    border: "none",
                    cursor: "pointer",
                    fontFamily: "Montserrat, sans-serif",
                    fontWeight: animationIntensity === level ? 700 : 400,
                    fontSize: "0.65rem",
                    letterSpacing: "0.03em",
                    background:
                      animationIntensity === level ? yellow : "transparent",
                    color:
                      animationIntensity === level ? "#111" : col.textMuted,
                    transition: "all 0.15s",
                    whiteSpace: "nowrap",
                    textTransform: "capitalize",
                  }}
                  data-ocid={`structure.intensity.${level}.toggle`}
                >
                  {level}
                </button>
              ))}
            </div>
          )}

          {/* Prototype Mode — only when Animated theme */}
          {selectedTheme === "Animated" && (
            <button
              type="button"
              onClick={() => setPrototypeMode((p) => !p)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 5,
                background: prototypeMode
                  ? "rgba(251,255,41,0.15)"
                  : "transparent",
                border: `1px solid ${prototypeMode ? yellow : col.border}`,
                borderRadius: 6,
                padding: "5px 10px",
                cursor: "pointer",
                color: prototypeMode
                  ? theme === "dark"
                    ? yellow
                    : "#5a5500"
                  : col.textMuted,
                fontSize: "0.7rem",
                fontFamily: "Montserrat, sans-serif",
                fontWeight: 600,
                transition: "all 0.15s",
                whiteSpace: "nowrap",
              }}
              title="Prototype Mode: simulate navigation, focus states, hover"
              data-ocid="structure.prototype.toggle"
            >
              ◆ Prototype {prototypeMode ? "ON" : "OFF"}
            </button>
          )}

          {/* Export Dropdown */}
          <div style={{ position: "relative" }}>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setExportDropdownOpen((o) => !o);
              }}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 5,
                background: yellow,
                color: "#111",
                border: "none",
                borderRadius: 6,
                padding: "5px 12px",
                cursor: "pointer",
                fontFamily: "Montserrat, sans-serif",
                fontWeight: 700,
                fontSize: "0.72rem",
                whiteSpace: "nowrap",
              }}
              data-ocid="structure.download.button"
            >
              <Download size={11} />
              Export
              <ChevronRight size={9} style={{ transform: "rotate(90deg)" }} />
            </button>
            {exportDropdownOpen && (
              <div
                style={{
                  position: "absolute",
                  top: "100%",
                  right: 0,
                  marginTop: 4,
                  background: theme === "dark" ? "#1a1a1a" : "#fff",
                  border: `1px solid ${col.border}`,
                  borderRadius: 8,
                  padding: 6,
                  minWidth: 200,
                  zIndex: 100,
                  boxShadow: "0 4px 16px rgba(0,0,0,0.15)",
                }}
                data-ocid="structure.export.dropdown_menu"
              >
                {[
                  { label: "Static HTML", desc: "No motion", disabled: false },
                  {
                    label: "React + Tailwind",
                    desc: "Static components",
                    disabled: false,
                  },
                  {
                    label: "React + Framer Motion",
                    desc: "Animated",
                    disabled: selectedTheme !== "Animated",
                  },
                ].map((opt) => (
                  <button
                    key={opt.label}
                    type="button"
                    disabled={opt.disabled}
                    onClick={() => {
                      handleDownload();
                      setExportDropdownOpen(false);
                    }}
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "flex-start",
                      width: "100%",
                      background: "transparent",
                      border: "none",
                      padding: "7px 10px",
                      cursor: opt.disabled ? "not-allowed" : "pointer",
                      borderRadius: 5,
                      opacity: opt.disabled ? 0.4 : 1,
                      textAlign: "left",
                    }}
                    onMouseEnter={(e) => {
                      if (!opt.disabled)
                        (e.currentTarget as HTMLElement).style.background =
                          theme === "dark"
                            ? "rgba(255,255,255,0.06)"
                            : "rgba(0,0,0,0.04)";
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLElement).style.background =
                        "transparent";
                    }}
                  >
                    <span
                      style={{
                        fontFamily: "Montserrat, sans-serif",
                        fontWeight: 600,
                        fontSize: "0.72rem",
                        color: col.text,
                      }}
                    >
                      {opt.label}
                    </span>
                    <span
                      style={{
                        fontFamily: "Karla, sans-serif",
                        fontSize: "0.62rem",
                        color: col.textMuted,
                      }}
                    >
                      {opt.desc}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ══ MAIN CONTENT AREA ══ */}
      <div
        style={{
          display: "flex",
          flex: 1,
          overflow: "hidden",
          position: "relative",
        }}
      >
        {/* ── LEFT SIDEBAR: Design Intelligence Panel ── */}
        {showSidebar && (
          <div
            style={{
              width: 220,
              minWidth: 220,
              flexShrink: 0,
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
              borderRight: `1px solid ${col.border}`,
              background: col.toolbar,
            }}
            data-ocid="structure.panel"
          >
            <div style={{ flex: 1, overflowY: "auto", padding: "14px 0" }}>
              {/* Detected Components */}
              <div style={{ padding: "0 14px 14px" }}>
                <p
                  style={{
                    fontFamily: "Montserrat, sans-serif",
                    fontWeight: 700,
                    fontSize: "0.62rem",
                    letterSpacing: "0.1em",
                    textTransform: "uppercase",
                    color: col.textMuted,
                    marginBottom: 8,
                  }}
                >
                  Detected Components
                </p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                  {effectiveVariant.analysis.detected_components.map((c) => (
                    <span
                      key={c}
                      style={{
                        fontFamily: "Karla, sans-serif",
                        fontSize: "0.67rem",
                        padding: "2px 8px",
                        borderRadius: 4,
                        background:
                          theme === "dark"
                            ? "rgba(251,255,41,0.1)"
                            : "rgba(251,255,41,0.25)",
                        border: `1px solid ${theme === "dark" ? "rgba(251,255,41,0.25)" : "rgba(180,170,0,0.3)"}`,
                        color: theme === "dark" ? yellow : "#5a5500",
                      }}
                    >
                      {c}
                    </span>
                  ))}
                </div>
              </div>

              <div
                style={{
                  height: 1,
                  background: col.border,
                  margin: "0 14px 14px",
                }}
              />

              {/* Layout Type */}
              <div style={{ padding: "0 14px 14px" }}>
                <p
                  style={{
                    fontFamily: "Montserrat, sans-serif",
                    fontWeight: 700,
                    fontSize: "0.62rem",
                    letterSpacing: "0.1em",
                    textTransform: "uppercase",
                    color: col.textMuted,
                    marginBottom: 6,
                  }}
                >
                  Layout Type
                </p>
                <span
                  style={{
                    fontFamily: "Karla, sans-serif",
                    fontSize: "0.78rem",
                    color: col.text,
                  }}
                >
                  {layoutType}
                </span>
              </div>

              <div
                style={{
                  height: 1,
                  background: col.border,
                  margin: "0 14px 14px",
                }}
              />

              {/* Confidence Score */}
              <div style={{ padding: "0 14px 14px" }}>
                <p
                  style={{
                    fontFamily: "Montserrat, sans-serif",
                    fontWeight: 700,
                    fontSize: "0.62rem",
                    letterSpacing: "0.1em",
                    textTransform: "uppercase",
                    color: col.textMuted,
                    marginBottom: 8,
                  }}
                >
                  Confidence Score
                </p>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div
                    style={{
                      flex: 1,
                      height: 4,
                      borderRadius: 2,
                      background:
                        theme === "dark"
                          ? "rgba(255,255,255,0.1)"
                          : "rgba(0,0,0,0.08)",
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        height: "100%",
                        width: `${Math.round(effectiveVariant.analysis.confidence_score * 100)}%`,
                        background: yellow,
                        borderRadius: 2,
                        transition: "width 0.6s ease",
                      }}
                    />
                  </div>
                  <span
                    style={{
                      fontFamily: mono,
                      fontSize: "0.7rem",
                      color: col.text,
                      flexShrink: 0,
                      minWidth: 36,
                      textAlign: "right",
                    }}
                  >
                    {Math.round(
                      effectiveVariant.analysis.confidence_score * 100,
                    )}
                    %
                  </span>
                </div>
              </div>

              <div
                style={{
                  height: 1,
                  background: col.border,
                  margin: "0 14px 14px",
                }}
              />

              {/* Design Tokens */}
              <div style={{ padding: "0 14px 14px" }}>
                <p
                  style={{
                    fontFamily: "Montserrat, sans-serif",
                    fontWeight: 700,
                    fontSize: "0.62rem",
                    letterSpacing: "0.1em",
                    textTransform: "uppercase",
                    color: col.textMuted,
                    marginBottom: 8,
                  }}
                >
                  Design Tokens
                </p>
                <div
                  style={{ display: "flex", flexDirection: "column", gap: 3 }}
                >
                  {Object.entries(effectiveVariant.design_tokens).map(
                    ([key, value]) => (
                      <div
                        key={key}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 6,
                        }}
                      >
                        <span
                          style={{
                            fontFamily: mono,
                            fontSize: "0.63rem",
                            color: col.textMuted,
                            minWidth: 80,
                          }}
                        >
                          {key}:
                        </span>
                        <span
                          style={{
                            fontFamily: mono,
                            fontSize: "0.63rem",
                            color: col.text,
                          }}
                        >
                          {value}
                        </span>
                      </div>
                    ),
                  )}
                </div>
              </div>

              <div
                style={{
                  height: 1,
                  background: col.border,
                  margin: "0 14px 14px",
                }}
              />

              {/* Auto Improvements */}
              <div style={{ padding: "0 14px 14px" }}>
                <p
                  style={{
                    fontFamily: "Montserrat, sans-serif",
                    fontWeight: 700,
                    fontSize: "0.62rem",
                    letterSpacing: "0.1em",
                    textTransform: "uppercase",
                    color: col.textMuted,
                    marginBottom: 8,
                  }}
                >
                  Auto Improvements
                </p>
                <div
                  style={{ display: "flex", flexDirection: "column", gap: 4 }}
                >
                  {effectiveVariant.analysis.auto_improvements.map(
                    (improvement, i) => (
                      <div
                        key={String(i)}
                        style={{
                          display: "flex",
                          alignItems: "flex-start",
                          gap: 6,
                        }}
                      >
                        <span
                          style={{
                            color: "#fbff29",
                            fontSize: "0.63rem",
                            lineHeight: "1.4",
                            flexShrink: 0,
                          }}
                        >
                          •
                        </span>
                        <span
                          style={{
                            fontFamily: "Karla, sans-serif",
                            fontSize: "0.67rem",
                            color: col.textMuted,
                            lineHeight: "1.4",
                          }}
                        >
                          {improvement}
                        </span>
                      </div>
                    ),
                  )}
                </div>
              </div>

              <div
                style={{
                  height: 1,
                  background: col.border,
                  margin: "0 14px 14px",
                }}
              />

              {/* UI Tree */}
              <div style={{ padding: "0 14px" }}>
                <button
                  type="button"
                  onClick={() => setUiTreeOpen((o) => !o)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    width: "100%",
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    padding: 0,
                    marginBottom: 8,
                  }}
                >
                  <p
                    style={{
                      fontFamily: "Montserrat, sans-serif",
                      fontWeight: 700,
                      fontSize: "0.62rem",
                      letterSpacing: "0.1em",
                      textTransform: "uppercase",
                      color: col.textMuted,
                      margin: 0,
                    }}
                  >
                    UI Tree
                  </p>
                  <ChevronRight
                    size={10}
                    style={{
                      color: col.textMuted,
                      marginLeft: "auto",
                      transform: uiTreeOpen ? "rotate(90deg)" : "rotate(0deg)",
                      transition: "transform 0.2s",
                    }}
                  />
                </button>
                {uiTreeOpen && (
                  <div style={{ paddingLeft: 4 }}>
                    {flatNodes.map((node, i) => (
                      <div
                        key={`${node.id}-${String(i)}`}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 4,
                          paddingLeft: node.depth * 12,
                          paddingTop: 2,
                          paddingBottom: 2,
                        }}
                      >
                        <span
                          style={{
                            width: 4,
                            height: 4,
                            borderRadius: "50%",
                            background: col.textMuted,
                            flexShrink: 0,
                            opacity: 0.5,
                          }}
                        />
                        <span
                          style={{
                            fontFamily: mono,
                            fontSize: "0.63rem",
                            color: col.textMuted,
                          }}
                        >
                          {node.type}
                        </span>
                        {node.id && (
                          <span
                            style={{
                              fontFamily: mono,
                              fontSize: "0.58rem",
                              color: col.textMuted,
                              opacity: 0.5,
                            }}
                          >
                            #{node.id}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div
                style={{
                  height: 1,
                  background: col.border,
                  margin: "14px 14px 14px",
                }}
              />

              {/* Theme applied */}
              <div style={{ padding: "0 14px" }}>
                <p
                  style={{
                    fontFamily: "Montserrat, sans-serif",
                    fontWeight: 700,
                    fontSize: "0.62rem",
                    letterSpacing: "0.1em",
                    textTransform: "uppercase",
                    color: col.textMuted,
                    marginBottom: 6,
                  }}
                >
                  Active Theme
                </p>
                <span
                  style={{
                    fontFamily: "Karla, sans-serif",
                    fontSize: "0.78rem",
                    color: col.text,
                  }}
                >
                  {selectedTheme}
                </span>
                <p
                  style={{
                    fontFamily: "Karla, sans-serif",
                    fontSize: "0.67rem",
                    color: col.textMuted,
                    marginTop: 2,
                  }}
                >
                  {THEME_CONFIGS[selectedTheme].description}
                </p>
              </div>

              {/* Motion Tokens — Animated theme only */}
              {selectedTheme === "Animated" && (
                <>
                  <div
                    style={{
                      height: 1,
                      background: col.border,
                      margin: "14px 14px",
                    }}
                  />
                  <div style={{ padding: "0 14px 14px" }}>
                    <p
                      style={{
                        fontFamily: "Montserrat, sans-serif",
                        fontWeight: 700,
                        fontSize: "0.62rem",
                        letterSpacing: "0.1em",
                        textTransform: "uppercase",
                        color: col.textMuted,
                        marginBottom: 8,
                      }}
                    >
                      Motion Tokens
                    </p>
                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: 3,
                      }}
                    >
                      {Object.entries(MOTION_TOKENS).map(([key, value]) => (
                        <div
                          key={key}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: 6,
                          }}
                        >
                          <span
                            style={{
                              fontFamily: mono,
                              fontSize: "0.63rem",
                              color: col.textMuted,
                              minWidth: 90,
                            }}
                          >
                            {key}:
                          </span>
                          <span
                            style={{
                              fontFamily: mono,
                              fontSize: "0.63rem",
                              color: yellow,
                            }}
                          >
                            {value}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div
                    style={{
                      height: 1,
                      background: col.border,
                      margin: "0 14px 14px",
                    }}
                  />
                  <div style={{ padding: "0 14px 14px" }}>
                    <p
                      style={{
                        fontFamily: "Montserrat, sans-serif",
                        fontWeight: 700,
                        fontSize: "0.62rem",
                        letterSpacing: "0.1em",
                        textTransform: "uppercase",
                        color: col.textMuted,
                        marginBottom: 8,
                      }}
                    >
                      Smart Animation Map
                    </p>
                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: 4,
                      }}
                    >
                      {effectiveVariant.analysis.detected_components.map(
                        (comp) => (
                          <div
                            key={comp}
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: 6,
                            }}
                          >
                            <span
                              style={{
                                fontFamily: "Karla, sans-serif",
                                fontSize: "0.67rem",
                                color: col.text,
                                minWidth: 52,
                              }}
                            >
                              {comp}
                            </span>
                            <span
                              style={{
                                fontSize: "0.6rem",
                                color: col.textMuted,
                              }}
                            >
                              →
                            </span>
                            <span
                              style={{
                                fontFamily: "Karla, sans-serif",
                                fontSize: "0.63rem",
                                padding: "1px 7px",
                                borderRadius: 4,
                                background: "rgba(251,255,41,0.1)",
                                border: "1px solid rgba(251,255,41,0.2)",
                                color: theme === "dark" ? yellow : "#5a5500",
                              }}
                            >
                              {SMART_ANIMATION_MAP[comp] ?? "fade-in"}
                            </span>
                          </div>
                        ),
                      )}
                    </div>
                  </div>

                  <div
                    style={{
                      height: 1,
                      background: col.border,
                      margin: "0 14px 14px",
                    }}
                  />
                  <div style={{ padding: "0 14px 14px" }}>
                    <p
                      style={{
                        fontFamily: "Montserrat, sans-serif",
                        fontWeight: 700,
                        fontSize: "0.62rem",
                        letterSpacing: "0.1em",
                        textTransform: "uppercase",
                        color: col.textMuted,
                        marginBottom: 8,
                      }}
                    >
                      Motion Intensity
                    </p>
                    <div style={{ display: "flex", gap: 3 }}>
                      {(["low", "medium", "high"] as const).map((level) => (
                        <button
                          key={level}
                          type="button"
                          onClick={() => setAnimationIntensity(level)}
                          style={{
                            flex: 1,
                            padding: "4px 0",
                            borderRadius: 5,
                            border: `1px solid ${animationIntensity === level ? yellow : col.border}`,
                            background:
                              animationIntensity === level
                                ? "rgba(251,255,41,0.12)"
                                : "transparent",
                            color:
                              animationIntensity === level
                                ? theme === "dark"
                                  ? yellow
                                  : "#5a5500"
                                : col.textMuted,
                            cursor: "pointer",
                            fontFamily: "Montserrat, sans-serif",
                            fontWeight: 600,
                            fontSize: "0.6rem",
                            textTransform: "capitalize",
                            transition: "all 0.15s",
                          }}
                        >
                          {level}
                        </button>
                      ))}
                    </div>
                    <p
                      style={{
                        fontFamily: "Karla, sans-serif",
                        fontSize: "0.63rem",
                        color: col.textMuted,
                        marginTop: 6,
                      }}
                    >
                      Scale: {ANIMATION_INTENSITY_MAP[animationIntensity].scale}
                      x · Duration:{" "}
                      {ANIMATION_INTENSITY_MAP[animationIntensity].duration}s
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* ── CODE PANEL ── */}
        {showCode && (
          <div
            style={{
              flex: showPreview ? (centerTab === "split" ? "0 0 50%" : 1) : 1,
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
              borderRight: showPreview ? `1px solid ${col.border}` : "none",
            }}
          >
            {/* Code header */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "8px 14px",
                borderBottom: `1px solid ${col.border}`,
                flexShrink: 0,
                background: col.toolbar,
              }}
            >
              <span
                style={{
                  fontFamily: "Montserrat, sans-serif",
                  fontWeight: 700,
                  fontSize: "0.68rem",
                  letterSpacing: "0.05em",
                  color: col.textMuted,
                  textTransform: "uppercase",
                }}
              >
                {showCodeLabel}
              </span>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <button
                  type="button"
                  onClick={handleCopy}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 5,
                    background: copied
                      ? "rgba(251,255,41,0.15)"
                      : "transparent",
                    border: `1px solid ${col.border}`,
                    borderRadius: 5,
                    padding: "3px 9px",
                    cursor: "pointer",
                    color: copied
                      ? theme === "dark"
                        ? yellow
                        : "#5a5500"
                      : col.textMuted,
                    fontSize: "0.7rem",
                    fontFamily: "Karla, sans-serif",
                    transition: "all 0.15s",
                  }}
                  data-ocid="structure.copy.button"
                >
                  {copied ? <Check size={11} /> : <Copy size={11} />}
                  {copied ? "Copied!" : "Copy"}
                </button>
                <button
                  type="button"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 5,
                    background: "transparent",
                    border: `1px solid ${col.border}`,
                    borderRadius: 5,
                    padding: "3px 9px",
                    cursor: "pointer",
                    color: col.textMuted,
                    fontSize: "0.7rem",
                    fontFamily: "Karla, sans-serif",
                  }}
                >
                  <Code2 size={11} />
                  Format
                </button>
              </div>
            </div>

            {/* Code body */}
            <div
              style={{
                flex: 1,
                overflow: "auto",
                display: "flex",
                background: col.bg,
              }}
              data-ocid="structure.editor"
            >
              {/* Line numbers */}
              <div
                style={{
                  flexShrink: 0,
                  padding: "14px 0",
                  background: col.toolbar,
                  borderRight: `1px solid ${col.border}`,
                  userSelect: "none",
                  minWidth: 44,
                  textAlign: "right",
                }}
              >
                {(codeContent === "json" ? jsonLines : codeLines).map(
                  (_, i) => (
                    <div
                      key={String(i)}
                      style={{
                        fontFamily: mono,
                        fontSize: "0.65rem",
                        lineHeight: 1.7,
                        color: col.textMuted,
                        paddingRight: 10,
                        opacity: 0.5,
                      }}
                    >
                      {i + 1}
                    </div>
                  ),
                )}
              </div>
              {/* Code body */}
              <pre
                style={{
                  margin: 0,
                  padding: "14px 16px",
                  fontFamily: mono,
                  fontSize: "0.68rem",
                  lineHeight: 1.7,
                  color: col.text,
                  whiteSpace: "pre",
                  flex: 1,
                  minWidth: 0,
                }}
              >
                <code>
                  {codeContent === "json" ? (
                    <JsonHighlight json={jsonString} theme={theme} />
                  ) : (
                    <JsxHighlight code={effectiveVariant.code} theme={theme} />
                  )}
                </code>
              </pre>
            </div>
          </div>
        )}

        {/* ── LIVE PREVIEW PANEL ── */}
        {showPreview && (
          <LivePreviewPanel
            iframeHtml={iframeHtml}
            theme={theme}
            col={col}
            yellow={yellow}
            deviceMode={deviceMode}
            setDeviceMode={setDeviceMode}
            deviceWidth={deviceWidth}
            regenerating={regenerating}
            applying={applying}
            themeChanging={themeChanging}
            iframeOpacity={iframeOpacity}
            iframeRef={iframeRef}
            iframeKey={iframeKey}
            openInNewTab={openInNewTab}
            handleFullscreen={handleFullscreen}
            setIframeKey={setIframeKey}
            flex={centerTab === "preview" ? 1 : "0 0 50%"}
          />
        )}
      </div>

      {/* ══ BOTTOM INSIGHT STRIP ══ */}
      <div
        style={{
          flexShrink: 0,
          height: 36,
          borderTop: `1px solid ${col.border}`,
          background: col.toolbar,
          display: "flex",
          alignItems: "center",
          padding: "0 16px",
          gap: 0,
          overflow: "hidden",
        }}
      >
        {/* Left insight items */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 0,
            flex: 1,
            minWidth: 0,
          }}
        >
          {[
            { label: "Generated in", value: `${generatedTime}s` },
            { label: "Theme", value: selectedTheme },
            {
              label: "Components",
              value: String(
                effectiveVariant.analysis.detected_components.length,
              ),
            },
            {
              label: "Confidence",
              value: `${Math.round(effectiveVariant.analysis.confidence_score * 100)}%`,
            },
            {
              label: "Framework",
              value: animationMode === "animated" ? "react-motion" : "react",
            },
          ].map((item, i) => (
            <div
              key={item.label}
              style={{ display: "flex", alignItems: "center", gap: 0 }}
            >
              {i > 0 && (
                <span
                  style={{
                    color: col.border,
                    marginLeft: 10,
                    marginRight: 10,
                    fontSize: "0.75rem",
                  }}
                >
                  |
                </span>
              )}
              <span
                style={{
                  fontFamily: "Karla, sans-serif",
                  fontSize: "0.67rem",
                  color: col.textMuted,
                }}
              >
                {item.label}:&nbsp;
              </span>
              <span
                style={{
                  fontFamily: mono,
                  fontSize: "0.67rem",
                  color: col.text,
                  fontWeight: 600,
                }}
              >
                {item.value}
              </span>
            </div>
          ))}
        </div>

        {/* Right: Refine prompt */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            flexShrink: 0,
            marginLeft: 12,
          }}
        >
          <Wand2 size={11} color={col.textMuted} />
          <input
            type="text"
            value={refinePrompt}
            onChange={(e) => setRefinePrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleApply();
            }}
            placeholder="Refine… e.g. add dark mode"
            style={{
              resize: "none",
              background: col.bg,
              border: `1px solid ${col.border}`,
              borderRadius: 5,
              color: col.text,
              fontSize: "0.67rem",
              fontFamily: "Karla, sans-serif",
              padding: "3px 8px",
              outline: "none",
              lineHeight: 1.5,
              width: 170,
              height: 22,
            }}
            data-ocid="structure.input"
          />
          <button
            type="button"
            onClick={handleApply}
            disabled={applying || !refinePrompt.trim()}
            style={{
              padding: "3px 10px",
              borderRadius: 5,
              border: "none",
              background:
                applying || !refinePrompt.trim() ? col.border : yellow,
              color: applying || !refinePrompt.trim() ? col.textMuted : "#111",
              cursor:
                applying || !refinePrompt.trim() ? "not-allowed" : "pointer",
              fontSize: "0.67rem",
              fontFamily: "Montserrat, sans-serif",
              fontWeight: 700,
              display: "flex",
              alignItems: "center",
              gap: 4,
              transition: "all 0.15s",
              whiteSpace: "nowrap",
              height: 22,
            }}
            data-ocid="structure.apply.button"
          >
            {applying && (
              <Loader2
                size={9}
                style={{ animation: "spin 1s linear infinite" }}
              />
            )}
            Apply
          </button>
        </div>
      </div>

      {/* ══ TOAST ══ */}
      <div
        style={{
          position: "absolute",
          bottom: 52,
          right: 20,
          background: theme === "dark" ? "#1a1a1a" : "#fff",
          border: `1px solid ${col.border}`,
          borderRadius: 8,
          padding: "8px 14px",
          display: "flex",
          alignItems: "center",
          gap: 7,
          fontSize: "0.75rem",
          fontFamily: "Montserrat, sans-serif",
          fontWeight: 600,
          color: col.text,
          boxShadow: "0 2px 12px rgba(0,0,0,0.1)",
          opacity: showToast ? 1 : 0,
          transform: showToast ? "translateY(0)" : "translateY(8px)",
          transition: "opacity 0.25s ease, transform 0.25s ease",
          pointerEvents: "none",
          zIndex: 50,
        }}
        data-ocid="structure.toast"
      >
        <Check size={13} color={theme === "dark" ? yellow : "#5a5500"} />
        {toastMsg}
      </div>

      {/* ══ SCANNING OVERLAY ══ */}
      {(regenerating || applying) && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            pointerEvents: "none",
            zIndex: 5,
          }}
          data-ocid="structure.loading_state"
        >
          {[0, 1, 2, 3, 4].map((i) => (
            <div
              key={String(i)}
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                height: 1,
                background: `rgba(251,255,41,${0.06 + i * 0.02})`,
                top: `${15 + i * 18}%`,
                animation: `scan-sweep 1.4s ease-in-out ${i * 0.12}s infinite`,
              }}
            />
          ))}
        </div>
      )}

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes scan-sweep {
          0% { opacity: 0; transform: translateX(-100%); }
          50% { opacity: 1; }
          100% { opacity: 0; transform: translateX(100%); }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
      `}</style>
    </div>
  );
}

// ── Live Preview Panel ─────────────────────────────────────────

interface LivePreviewPanelProps {
  iframeHtml: string;
  theme: "light" | "dark";
  col: StructureResultProps["panels"];
  yellow: string;
  deviceMode: DeviceMode;
  setDeviceMode: (d: DeviceMode) => void;
  deviceWidth: Record<DeviceMode, string>;
  regenerating: boolean;
  applying: boolean;
  themeChanging: boolean;
  iframeOpacity: number;
  iframeRef: React.RefObject<HTMLIFrameElement | null>;
  iframeKey: number;
  openInNewTab: () => void;
  handleFullscreen: () => void;
  setIframeKey: React.Dispatch<React.SetStateAction<number>>;
  flex: string | number;
}

function LivePreviewPanel({
  iframeHtml,
  theme,
  col,
  yellow,
  deviceMode,
  setDeviceMode,
  deviceWidth,
  regenerating,
  applying,
  themeChanging,
  iframeOpacity,
  iframeRef,
  iframeKey,
  openInNewTab,
  handleFullscreen,
  setIframeKey,
  flex,
}: LivePreviewPanelProps) {
  const [iframeLoaded, setIframeLoaded] = useState(false);

  return (
    <div
      style={{
        flex,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        background: col.bg,
      }}
    >
      {/* Preview header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "7px 14px",
          borderBottom: `1px solid ${col.border}`,
          flexShrink: 0,
          background: col.toolbar,
        }}
      >
        {/* Device toggles */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 2,
            background: col.bg,
            border: `1px solid ${col.border}`,
            borderRadius: 7,
            padding: "2px",
          }}
        >
          {[
            {
              mode: "desktop" as DeviceMode,
              icon: <Monitor size={12} />,
              label: "Desktop",
            },
            {
              mode: "tablet" as DeviceMode,
              icon: <Tablet size={12} />,
              label: "Tablet",
            },
            {
              mode: "mobile" as DeviceMode,
              icon: <Smartphone size={12} />,
              label: "Mobile",
            },
          ].map(({ mode, icon, label }) => (
            <button
              key={mode}
              type="button"
              onClick={() => setDeviceMode(mode)}
              title={label}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 4,
                padding: "3px 9px",
                borderRadius: 5,
                border: "none",
                cursor: "pointer",
                background: deviceMode === mode ? yellow : "transparent",
                color: deviceMode === mode ? "#111" : col.textMuted,
                fontSize: "0.67rem",
                fontFamily: "Karla, sans-serif",
                transition: "all 0.15s",
              }}
              data-ocid={`structure.${mode}.toggle`}
            >
              {icon}
              {deviceMode === mode && <span>{label}</span>}
            </button>
          ))}
        </div>

        {/* Action icons */}
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <button
            type="button"
            onClick={() => setIframeKey((k) => k + 1)}
            title="Refresh preview"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 28,
              height: 28,
              borderRadius: 6,
              border: `1px solid ${col.border}`,
              background: "transparent",
              cursor: "pointer",
              color: col.textMuted,
            }}
          >
            <RotateCcw size={12} />
          </button>
          <button
            type="button"
            onClick={openInNewTab}
            title="Open in new window"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 28,
              height: 28,
              borderRadius: 6,
              border: `1px solid ${col.border}`,
              background: "transparent",
              cursor: "pointer",
              color: col.textMuted,
            }}
            data-ocid="structure.open_modal_button"
          >
            <ExternalLink size={12} />
          </button>
          <button
            type="button"
            onClick={handleFullscreen}
            title="Fullscreen"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 28,
              height: 28,
              borderRadius: 6,
              border: `1px solid ${col.border}`,
              background: "transparent",
              cursor: "pointer",
              color: col.textMuted,
            }}
          >
            <Maximize2 size={12} />
          </button>
        </div>
      </div>

      {/* Preview container */}
      <div
        style={{
          flex: 1,
          overflow: "auto",
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "center",
          padding: deviceMode === "desktop" ? 0 : "16px",
          background: theme === "dark" ? "#111" : "#f0f0f0",
          position: "relative",
        }}
      >
        {/* Loader overlay */}
        {(regenerating || applying || themeChanging) && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              background:
                theme === "dark"
                  ? "rgba(15,15,15,0.82)"
                  : "rgba(240,240,240,0.82)",
              zIndex: 10,
              gap: 12,
              backdropFilter: "blur(4px)",
            }}
          >
            <Loader2
              size={24}
              style={{ color: yellow, animation: "spin 1s linear infinite" }}
            />
            <span
              style={{
                fontFamily: "Montserrat, sans-serif",
                fontSize: "0.78rem",
                color: theme === "dark" ? "#fff" : "#333",
                letterSpacing: "0.04em",
              }}
            >
              {themeChanging ? "Applying Theme…" : "Structuring Interface…"}
            </span>
          </div>
        )}

        <div
          style={{
            maxWidth: deviceWidth[deviceMode],
            width: "100%",
            height: deviceMode === "desktop" ? "100%" : "auto",
            minHeight: deviceMode !== "desktop" ? 500 : "100%",
            transition: "max-width 0.3s ease",
            borderRadius: deviceMode === "desktop" ? 0 : 12,
            overflow: "hidden",
            border:
              deviceMode === "desktop" ? "none" : `1px solid ${col.border}`,
            boxShadow:
              deviceMode === "desktop" ? "none" : "0 2px 12px rgba(0,0,0,0.06)",
            flexShrink: 0,
            position: "relative",
          }}
          data-ocid="structure.canvas_target"
        >
          <iframe
            ref={iframeRef}
            key={iframeKey}
            srcDoc={iframeHtml}
            style={{
              width: "100%",
              height: "100%",
              minHeight: deviceMode !== "desktop" ? 500 : "100%",
              border: "none",
              display: "block",
              opacity: iframeLoaded ? iframeOpacity : 0,
              transition: "opacity 0.3s ease",
            }}
            title="Live Preview"
            sandbox="allow-scripts"
            onLoad={() => setIframeLoaded(true)}
          />
          {!iframeLoaded && !regenerating && !applying && !themeChanging && (
            <div
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                background: col.bg,
              }}
            >
              <Loader2
                size={18}
                style={{ color: yellow, animation: "spin 1s linear infinite" }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
