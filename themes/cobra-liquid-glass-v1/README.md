# Cobra Liquid Glass · HM v1

This is a **data-only Cobra Visual Theme Runtime v2 package**. It is intentionally presentation-only and branches from Cobra build lineage head `0560b18c497e9861864126d96f9b784e488ebe32` (`infinity-cobra-2103179-buffer-resilience-rc1`).

## Visual direction

- Liquid Glass-inspired translucent surfaces using alpha gradients, edge highlights, rounded depth, and Cobra blue focus light.
- Coordinated Light, Dark, and True OLED Black appearance variants.
- Applied across the existing Cobra visual slots: shell/header/status, rail, drawer, settings, sheets, dialogs, guide chrome, player chrome/channel drawer, and experience chooser.
- HM personalization is retained in the chooser copy.
- Geometry is deliberately left unchanged in v1 so Fold/cover/tablet/TV use their already-tested layouts.

## Protected contracts

The theme does **not** contain executable code, native libraries, player logic, provider logic, video surfaces, actions, new view ownership, or guide geometry. It must not change playback, rewind/timeshift, PiP, mini-player handoff, surface ownership, background playback, rotation, channel switching, or the native Kodi engine.

Runtime v2 already refuses to style/reparent `TextureView`, `SurfaceView`, or `WebView`, and the theme manager provides reset/rollback.

## Build

```bash
python3 themes/cobra-liquid-glass-v1/build.py --out dist
```

Expected package:

`dist/Cobra-Liquid-Glass-HM-v1.0.0.zip`

The ZIP contains exactly:

`script.infinity.cobra.theme/resources/visual-theme.json`

No binary assets are bundled in v1. The “glass” effect is implemented with supported native translucent gradients/strokes/elevation; this does **not** claim real-time blur where the runtime does not provide it.

Validation is intentionally performed on a draft PR before any merge into the protected playback branch.
