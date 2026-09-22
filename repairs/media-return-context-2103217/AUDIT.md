# Infinity/Cobra 2103217 — Media Return Context

Protected parent: locked 2103216 Smart Return in Experience & Display.

## Exact bug
Movies/TV Shows landing pages can open deeper **See all** / Genre collection pages. Android Back on those collection pages was not part of the old Smart Return feature and could fall through to Cobra's Live TV/Guide back path.

## Fix
- Before a Movies or TV Shows landing page enters a collection page, Cobra captures the exact parent landing View tree.
- Back from **See all** / Genre collection restores that exact parent View tree instead of falling through to Live TV.
- Because the same View objects are restored, the parent page's vertical scroll position is preserved and focus is restored best-effort.
- Drawer navigation to a different top-level destination intentionally abandons the old media parent context.
- Opening Settings from a collection can still preserve the media parent because Settings remains an overlay-style detour.

## Smart Return correction
- While inside a media collection, Smart Return now classifies the destination as Movies or TV Shows instead of Guide/Live TV.
- The TV Shows landing title **COBRA • TV SHOWS** is now recognized directly (the older code only recognized COBRA • SERIES).
- Smart Return remains in **Cobra Settings → Experience & Display**, default ON unless explicitly disabled.

## Preserved
- locked 2103214 Movies/TV Shows presentation and media-details implementation
- 2103216 Settings top-left drawer and no inline Back row
- Live TV fixed-blue Ambient and Night Cinema/player presentation
- Infinity-native Health Center
- playback/providers/timeshift/Multi-View/PiP/background
- 2103209 Python 3.11 GIL-stability native engine
- signer/resources/assets
