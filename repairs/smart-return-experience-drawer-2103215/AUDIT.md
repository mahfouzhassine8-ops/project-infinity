# Infinity/Cobra 2103215 — Smart Return Experience placement + Settings drawer correction

Protected parent: locked 2103214 Media Details Final.

This is a tiny navigation/preferences successor only.

## Smart Return

- Smart Return is removed from the long Cobra Settings list.
- It now appears directly in **Cobra Experience options** beside Remember & launch / Launch once / Ask every time / Cobra Recovery.
- The row displays **Smart Return • ON/OFF** and toggles in place.
- Smart Return defaults to **ON** when the user has never explicitly chosen a value.
- An explicit prior Off choice remains respected.
- The existing Smart Return engine is preserved: Movies returns to Movies, Shows to Shows, Live TV to Live TV, with remembered useful browsing/scroll context and no resurrection of stale timeshift buffers.

## Settings navigation

- The added inline **‹ BACK** row is removed.
- Cobra Settings uses the normal **top-left drawer/hamburger** as requested.
- The Settings header itself opens the Cobra navigation drawer.
- The previously implemented Settings return-state engine is retained internally for safe restoration/navigation, but is no longer exposed as a separate Back control.

## Hard preservation

Unchanged from locked 2103214:
- final Movies/TV Shows experience and media details work
- Live TV fixed-blue Ambient
- Night Cinema/player ambient presentation
- Infinity-native Health Center
- providers, playback, timeshift/rewind, Multi-View, PiP/background
- 2103209 Python 3.11 GIL-stability native engine
- resources/assets and permanent signer
- video pixels are never recolored
