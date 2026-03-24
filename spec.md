# Duiodle – Upload Mode + Navigation Flow

## Current State
- Sketch Mode is fully implemented as SketchMode.tsx with toolbar, canvas, color wheel, and scan overlay.
- Upload button in hero exists but does nothing.
- "Launch Duiodle" CTA button has no behavior.
- Logo/nav has no back-to-hero behavior from workspace.

## Requested Changes (Diff)

### Add
- `UploadMode.tsx`: Full-screen Upload workspace mirroring SketchMode layout (top toolbar, left panel, center dropzone, right info panel).
  - Center: Large dashed dropzone for PNG/JPG/JPEG/PDF with drag-and-drop + browse button.
  - After upload: image appears centered with zoom-in animation.
  - Right panel switches to "Image Analysis" with Detect Edges, Adjust Contrast, Crop Tool, and "Start Structuring" button.
  - "Start Structuring" shows "Interpreting layout structure…" scanning overlay animation.
  - Theme-aware: respects dark/light, dashed border adjusts color, maintains yellow accent.
  - Fade + upward slide 20px entry transition (same as SketchMode).
- Custom CSS cursor: hovering Sketch button shows pencil cursor, Upload button shows n-resize (upward arrow) cursor.

### Modify
- `App.tsx`:
  - Add `uploadOpen` state, wire Upload button to open UploadMode.
  - Add `heroRef` to the hero section.
  - "Launch Duiodle" CTA button: if on landing page, smooth-scroll to hero section; if hero already visible, pulse animation on Sketch+Upload buttons.
  - Logo click in SketchMode/UploadMode toolbars (Back button) already returns to landing -- confirm consistent.
  - The SketchMode and UploadMode Back buttons should call onClose which hides the workspace overlay (already implemented for Sketch, extend to Upload).
- Custom cursor styles on Sketch/Upload hero buttons via CSS.

### Remove
- Nothing removed.

## Implementation Plan
1. Create `UploadMode.tsx` with full layout, dropzone, post-upload image view, right panel analysis tools, scan overlay.
2. Update `App.tsx`: add uploadOpen state, wire Upload button, add heroRef, implement Launch Duiodle scroll/pulse logic.
3. Add CSS for upload mode, cursor styles (pencil SVG data URL on Sketch button, upward arrow on Upload button), pulse animation on hero buttons.
