# 2103222 onn. 4K Pro TV Player / Multi-View / Full-Screen Fit Audit

Protected parent: 2103221 — Infinity/Cobra onn. 4K Pro TV Remote UI RC4.

This pass is strictly for the 32-bit onn./Google TV variant. The regular ARM64 phone/Fold line is not modified.

## Physical-device findings from 2103221

1. Player D-pad graph is incomplete. The center transport row is reachable, but the header controls and footer controls (Channels, Display, Multi-View, More) do not have deterministic vertical D-pad routes.
2. Preview/fullscreen transitions can expose a long black frame. The current path adds an opaque fullscreen overlay with a new TextureView before the already-playing preview session has a ready destination surface; return removes fullscreen while the preview surface is still being rebound.
3. TV browse still inherits phone-oriented system-bar and safe-area behavior. The root already owns insets, while the guide layout subtracts system insets again; the dedicated TV target can therefore waste canvas and look slightly offset.
4. Channel Groups now work and must remain working, but the overlay/guide need a final 10-foot fit pass after full-canvas correction.
5. TV Multi-View is behind the newly approved phone Multi-View behavior. In 2103221, Watch fullscreen still collapses Multi-View to a single player and releases the other screens.

## Approved phone Multi-View contract to port

Source reference: locked-infinity-cobra-2103227-device-live-fold-multiview-passed.

- Preserve existing Use audio here, Change channel, Add screen, Retry this screen, Playback details, Remove screen and Close Multi-View.
- Add Search and add.
- Add per-screen Pause / Resume.
- Add Enlarge screen / Restore grid while every other player remains alive.
- Add Full screen that temporarily promotes one existing tile without releasing or rebuilding the other Multi-View players.
- Back and an explicit Return to Multi-View player action restore the same Multi-View session, channels, selected/audio tile and layout.
- Do not retune, recreate players, reset position/timeshift, or restart audio sessions just because a tile is promoted.

## 2103222 correction contract

- Explicit three-zone player focus graph: header <-> transport <-> footer. Left/Right moves within a row; Up/Down moves between rows; Select activates focused controls.
- Every top header control and every bottom player tool is reachable by the onn. remote.
- Seamless preview <-> fullscreen handoff keeps the previous surface visible until the destination TextureView is ready; the existing ExoPlayer is reused.
- Returning to the guide does not rebuild an already-mounted guide shell and restores the previous guide focus.
- Dedicated TV surfaces use the full display canvas instead of reserving phone navigation/status-bar space.
- Guide geometry is clamped to the real TV viewport so themed/custom geometry cannot extend offscreen.
- Channel Groups keep immediate current-group focus and receive only TV-fit/polish changes.
- Port the approved 2103227 Multi-View interaction delta with TV remote focus behavior.
- Preserve 2103221 package/signer/native engine, Live TV providers, rewind/timeshift, recordings, Movies/Shows, Smart Return and Health Center.

2103221 remains the rollback baseline until 2103222 passes source compilation, APK verification, and physical onn. remote testing.
