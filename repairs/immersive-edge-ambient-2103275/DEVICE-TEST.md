# Cobra 2103275 Immersive Edge Ambient RC1 — Fold acceptance

Start from locked 2103274 data/settings.

1. Install 2103275 over 2103274 and confirm update-over-install.
2. Cobra → Visual settings → Ambient Mode. Confirm only **Off / Subtle / Immersive** exist; no new clutter/toggle was added.
3. Play a channel in the embedded mini-player and choose Immersive.
4. Use colorful video with visibly different edges. Confirm top/left/right/bottom scene colors spill in their own directions instead of becoming one flat tint.
5. Confirm the result looks close to x-ambient: broad soft field, strong but controlled saturation, smooth live motion, no hard rectangles or flicker.
6. Confirm the actual video remains pristine—no colored veil, blur, dimming or crop change over the mini-player.
7. Camera cuts should morph smoothly rather than flash.
8. Pause the mini-player: the last atmosphere may remain, but it should stop visibly chasing frames. Resume and confirm motion returns.
9. Repeat in **Mobile, TV Grid, Compact, Cards and Pro**. The effect must follow the mini-player position in each layout.
10. Repeat in OLED/dark and Light.
11. Enter fullscreen: ambient must fade/suspend immediately. Fullscreen video and controls remain normal.
12. Return from fullscreen: ambient fades back in around the embedded player from the current scene.
13. Enter PiP: ambient is suspended. Return to Cobra: ambient resumes only after the embedded player is visible again.
14. Enable mini-player background playback and leave the app: no ambient sampling/rendering continues in background.
15. Enter Multi-View: the single mini-player ambient renderer is suspended; Multi-View behavior is unchanged.
16. Toggle Immersive → Subtle → Off and back. Subtle/Off must match locked behavior, with no stale frame colors left behind.
17. Fold/unfold, rotate, Samsung split screen, pop-up window and live resize. Projection must re-anchor to the actual current mini-player bounds.
18. Regression-test channel change, Pro Sports, Sports Hub, timeshift/rewind, subtitles, player controls, recordings, Smart Multi-View, Movies/Shows, drawer and Settings.
19. Watch performance/thermal behavior for several minutes. Playback must stay smooth and the effect must not cause runaway heat or memory growth.

Do not lock until the physical Fold visual result and playback regression matrix pass.
