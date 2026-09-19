# Cobra Liquid Glass · HM — SAFE v1.1

**Do not use the original v1.0.0 package.** It passed static non-interference checks but was reported on-device as visually unusable because global `all.*` styles cascaded through Cobra's view trees.

SAFE v1.1 removes that failure mode.

## Safety changes

- No `all.*`, `widget.*`, `font.*`, `tag.*`, or other global style rules.
- Only explicitly named Cobra surfaces are themed.
- Ordinary buttons, text, panels, and navigation controls keep Cobra's proven built-in rendering.
- No layout dimensions, margins, padding, weights, scenes, guide geometry, or layout-specific variants.
- No image/font assets.
- No player/provider/native code changes.
- Light, Dark, and True OLED use explicit scoped surface treatments.
- The audit now fails if a global cascade is introduced again.

## Protected playback

The package cannot own or alter TextureView/SurfaceView playback surfaces, PiP, mini-player handoff, timeshift/rewind, provider behavior, rotation, 120 Hz policy, or the native Kodi engine. Those protected runtime/test sources are pinned by the safety audit.

## Build

```bash
python3 themes/cobra-liquid-glass-v1/build.py --out dist
python3 themes/cobra-liquid-glass-v1/adversarial_audit.py
```

Installable package:

`dist/Cobra-Liquid-Glass-HM-SAFE-v1.1.0.zip`

The ZIP contains only:

`script.infinity.cobra.theme/resources/visual-theme.json`

## Certification rule

Automated checks are not allowed to call this physically certified. The final acceptance criterion is simple: **the real device must remain visibly readable and navigable after installation.**
