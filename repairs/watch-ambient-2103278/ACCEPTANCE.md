# Cobra 2103278 — Watch controls ambient candidate

Exact parent locked 2103277 source commit 8e8b55b6e3c2bb731359e2d52aa11cdf07327729.
Rollback Git bundle and reconstructed source snapshot are made before mutation.

Extend the one existing engine with a controls-only Watch mode. The renderer draws
nothing onto the fullscreen background/video. Four video-edge colors illuminate
existing glass backgrounds, submenu material, played timeline and original seek thumbs.
White glyphs, text, focus/selection, seek values and the distinct live marker remain native.

Crop capture to the actual transformed picture inside the TextureView; avoid sampling
player-generated letterbox/pillarbox areas. Working capture width 144, height <=512,
normalized working frame <=144x144, palette 24x16, cadence <=12fps. Cached buffers,
canvases, shader and arrays; no per-frame Bitmap creation, native engine or networking changes.
Pause/buffer retains colors, resumes cadence; hidden controls, PiP, background and actual
Multi-View suspend. Rebind/session guards wait for current channel pixels. Failure closes
ambient without touching playback. Night Cinema retains precedence for its existing chrome.

Off/Subtle and inactive protected renders remain exact. Mini-player field and fill remain
locked behavior. Source verification permits only bounded Activity/ambient/version updates.
274 locked tests plus 23 controls/crop/UI tests; protected renders and native/resources preserved.
Actual Fold visual/stress acceptance required. Mockup menu illustrates materials only;
existing real Display options and all settings/actions are preserved, no redesigned menus.
