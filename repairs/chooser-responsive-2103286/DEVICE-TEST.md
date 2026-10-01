# Infinity 2103286 — Chooser Responsive / Long-Press Repair RC1

Install as an **update over 2103285**. Do not uninstall, clear data, or run Start Fresh.

This candidate is intentionally narrow:
- preserves the 2103285 native FD crash repair unchanged
- removes the hidden whole-surface long-press that opened "Cobra theme controls"
- keeps theme controls explicitly under **Cobra gear → Cobra Theme controls**
- switches chooser sizing to the current Android window, not the physical display
- reflows Fold-inner, square/tablet, landscape, split-screen and resized windows
- preserves portrait/cover master composition, Light/Dark/OLED behavior, user data, providers and playback

Physical-device acceptance:
1. Open Choose Your Experience on the Fold inner screen.
2. Hold unused background space for 2+ seconds — **nothing should open**.
3. Tap Cobra gear; confirm Cobra Theme controls is available explicitly.
4. Fold closed/open and rotate both directions. The chooser should immediately use the available window with no narrow centered strip or huge gray side bars.
5. Try split screen / resized window if available. Controls must remain visible and tappable.
6. Enter Infinity and leave it open two minutes, then close/reopen twice to reconfirm the 2103285 FD crash repair is still intact.

Do not lock from CI alone. Galaxy Fold acceptance is required.
