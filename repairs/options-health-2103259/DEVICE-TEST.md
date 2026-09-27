# 2103259 — Options + Health glass finish (phone/Fold test candidate)

Parent is the passed 2103258 at f84a49191b2d47c7b84d280e100eeda62cfe6df7.
Scope: Infinity options, Cobra options, and the existing Health Center submenu/report viewers.
Other entries remain actions; there is no new navigation, toggle, audio or recovery operation.

The options surface now uses a continuous rounded, opaque-backed optical gradient and a
thin reflective bevel. It no longer stitches eight cropped card pieces around a rectangular
center. Underlying chooser letters cannot bleed through the panel. Health shares this finish
in light/dark and its app-owned diagnostic text viewers, including a selectable report body.

Chooser composition/art, player, native engine, diagnostics collection/export/copy code,
options callbacks and fallback UI are preserved. Copy diagnostics retains the original
keep-open behavior. The Android file picker/share UI is system-owned and is not restyled.
The separate TV build is not changed. The earlier intermittent startup hang is NOT fixed
or diagnosed by this visual patch. Startup sound integration remains on hold.

Install as an update; do not uninstall, clear data, Start Fresh, or invoke destructive recovery
for visual testing. Review both gears and Health in Light and Dark. Check that the chooser
background is visible around the dialog but not through its text. Close/Cancel and native
Back must dismiss normally. Ordinary export/copy/report behavior must be unchanged.

CI is not physical-device approval. The screenshots are actual Android Views rendered via
Robolectric native graphics, not AI mockups or device captures. Existing 2103256 stable lock
is not changed; 2103258 source/APK and rollback branch are retained. Do not uninstall to
bypass Android downgrade protection; a forward-version rollback can be prepared if needed.
