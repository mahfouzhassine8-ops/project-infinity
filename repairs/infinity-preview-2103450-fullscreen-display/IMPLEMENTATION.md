# Preview Fullscreen and Display refinement over locked2103450

The current user-approved functional baseline is exact signed2103450, source
f372d25e5e3b23634895ef2e9c9ed60e5246d123. Its lock and all recovery artifacts are
retained. The implementation branch starts at that lock plus its frozen design
document. No Cobra, native/shared, Kodi, Splash/routing, provider, data or shutdown
code changes are authorized or implemented.

Latest user clarification supersedes the initial independent-scaling entry rule:
Fullscreen temporarily selects proportion-preserving Fill/crop. It stores the
previous Display choice and restores it on exit. Rotation remains independent.
The header/rail are hidden and Android system bars are hidden through private
Activity WindowInsetsController APIs (legacy private-window flags on older API).
A video tap reveals controls as overlays, preserving the full video viewport.
Back first exits fullscreen, then retains normal source-app return semantics.
The normal450 rounded frame/geometry is restored on exit. Caption placement
accounts for revealed overlay controls. No decoder restart, provider execution,
orientation forcing or timeline reset is added.

Display is a private native Dialog with rounded cinematic surfaces, cyan radio
selection, line icons, exact prescribed descriptions, and reachable Appearance
and Done actions. Normal Best Fit/Fill calculations are retained; Stretch is an
explicit option with the aspect-ratio warning. Appearance uses the same existing
System/Light/Dark preference. Dialog resizing follows the real root viewport;
its dismissal callback checks ownership so an old window cannot clear a new one.
New UI flags persist through ordinary saved-instance restoration, independently
of existing per-video resume identity/progress and call/audio state.

Fourteen focused host tests pass on the latest temporary-crop implementation.
They exercise actual View input, native Canvas, fullscreen entry/reveal/exit/Back,
mode restoration (including prior Stretch), state save/resize, retained controls,
call/focus behavior, and Light/Dark cover/inner/landscape/short-window dialogs.
These use a decoder terminal spy, not real media decoding. The panel render test
uses fresh correctly sized host windows because changing resource qualifiers
alone left its native visibility clip at1280px while views were2520px. That was a
fixture mismatch. A completed single-method JVM also needed the standard explicit
JUnit exit to avoid a non-daemon queued-work looper; no production workaround.

The source/class guard confirms630 unrelated complete class definitions remain
exact. Engine, resume store, request state and routing sources/classes are exact;
protected Activity playback/lifecycle/call/focus methods are independently checked.
Only Preview Activity UI/window state, the Fullscreen glyph in Chrome.Control,
and the new private Display Dialog are changed. Its sole new ownership root is
explicitly registered INFINITY. The original signer/assembler/security code is
frozen except the exact authorized engineering-branch admission literal.

Actual Android verification is selected independently and remains pending until
its evidence is retained. The first run decoded video and entered immersive mode,
then failed because the harness queried the intentionally hidden clock. That
FAIL is preserved. The corrected observation reads actual owned NuPlayer video
frame counters and connection identity while chrome is hidden. The next run was
cancelled when the user changed fullscreen entry to temporary crop. No failed or
cancelled run is relabeled PASS. The current run checks the latest crop rule,
actual edge pixels, normal fit/fill/stretch via a decoded square marker, mode
restoration, OS window state, viewport changes, themes and resume choices.

Reference access remains limited: the frozen approved GitHub design description
was read in full; current tools expose no actual approved PNG or cover-recording
bytes. The known accessible reference Page contains older Cobra material, which
is not used as a Preview reference. An existing path/link was requested and the
user instructed proceeding. Implementation follows the written frozen design
and latest explicit crop behavior. Do not claim actual PNG/video inspection or
exact image parity. The supplied recording is explicitly COVER-display evidence,
not an inner-display observation. Final visual comparison and physical Fold
acceptance remain the user's. No new candidate lock is automatic.
