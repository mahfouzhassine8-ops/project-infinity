# Cobra 2103277 candidate scope
Exact parent: locked 2103276 source commit 2359c77ef104cc9421da5afd9ec648579ae0f681.
Rollback source archive and Git bundle created before mutation.

One existing preview TextureView scaling path now uses aspect-preserving center crop,
ignoring saved channel aspect adjustments only for embedded single-player presentation.
Fullscreen, PiP, Multi-View scaling and all playback ownership remain locked behavior.
Existing video-size/layout listeners handle resizing without prepare, seek or surface replacement.
TextureView.getBitmap applies the texture transform before copying its layer (Android framework
TextureView.java); no second crop or full-resolution capture is added.
Paused ambient refreshes its geometry once on scaling/layout changes, with no frame ticker.
Existing control layout, captions, corners and glass drawables preserved.
Source verifier enforces exact bounded transformations and byte equality of every other shell file.
Protected inactive-state screenshots remain exact. All locked 261 tests plus new crop/UI tests required.
Encoded borders in the stream need content detection; this candidate does not silently trim actual picture.
Physical Fold stress and visual acceptance remain required; green CI alone is candidate status.
