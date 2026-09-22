# Infinity/Cobra 2103212 — Health Center + ambient media trim

Protected parent: locked successful 2103211 Library + Native Health. Native engine remains the exact 2103209 Python 3.11 GIL-stability engine.

This is a presentation-only successor.

Authorized changes:
- Restyle Infinity Health Center from a stock Android alert into an Infinity-native responsive diagnostics/recovery sheet: rounded surfaces, Infinity mark, hierarchy, descriptive diagnostic rows, proper Light/Dark/OLED palette, focus states and an integrated Close action.
- Restyle the Health Center text/detail viewer to match the same Infinity surface language.
- Add restrained trim to Cobra Movies and TV Shows without changing their locked structure or data behavior.
- Media trim follows Cobra Ambient Mode:
  - Off: restrained neutral edge trim.
  - Subtle: light ambient tint in edges/focus.
  - Immersive: stronger atmospheric edge/focus trim.
  Ambient changes refresh the visible trim. Video content is never recolored.

Preserved exactly:
- Movies/TV Shows information architecture, rows, Genres placement, See All, details-first poster action, Continue Watching and personalization behavior.
- Infinity Health Center collection/export/copy/crash-recovery logic.
- Live TV, Guide, Quick Peek, playback, timeshift/rewind, Multi-View, PiP/background, provider/network behavior.
- 2103209 libkodi.so and Python 3.11 GIL fix.
- APK assets/resources and permanent signer.

2103211 remains locked and untouched.
