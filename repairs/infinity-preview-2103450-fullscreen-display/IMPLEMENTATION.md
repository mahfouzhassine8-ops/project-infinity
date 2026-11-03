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

The crop Android attempt41553789436 is retained as FAIL, not acceptance. Real
frames advanced and the cropped picture covered the viewport, but Android's
first-use ImmersiveModeConfirmation tutorial covered the upper edge during the
pixel assertion. Its screenshot and exact OS window dump are retained. The
active-window accessibility root stayed Preview, so the initial helper could not
see the non-focusable SystemUI window. QA now requests interactive windows and
queries only that exact OS tutorial, uses two fresh matching Got it bounds, then
observes dismissal before the unchanged edge-pixel assertion. Observer compilation
and Python syntax pass; no production code, app timers or native behavior changed.

API37's non-focusable tutorial was also absent from interactive accessibility
windows (attempt41554934790, retained FAIL with its empty root and visible OS
screenshot). The QA-only fallback now verifies the live ImmersiveModeConfirmation
window/touchable region, measures the blue button from current screenshot pixels,
and requires OCR text Got it plus two fresh equal bounds. It sends ordinary touch
input and observes dismissal; no settings, app timers or assertions are changed.
On both retained real screenshots it located [836,436,1018,562] in about0.14s; a
negative red frame was rejected. The QA image installs Ubuntu's tesseract-ocr;
production and original-key signing have no such dependency. Runtime remains
pending until all remaining selected checks actually pass.

Attempt41556201704 proves the measured tutorial handling works and records actual
Light/Dark fullscreen entry/reveal/exit, 16/16 video edge samples each and decoder
continuity. It remains FAIL overall: on the third entry, the immediate hierarchy
was a partially updated old frame while the failure screenshot and OS dump show
completed fullscreen. QA now observes two complete hidden-chrome trees within the
existing3.5-second input deadline before continuing. This is bounded observation
of asynchronous public input, no app timing change and no weakened assertion.

Attempt41557296965 confirms stable hidden chrome in0.599s, but the first-use OS
tutorial arrived after its initial check. The captured WMS touch region was still
animating from top-252 to0. QA now checks that exact overlay after screenshot,
waits for a stable measured current target within the same eight-second OS
observation limit, and recaptures once after genuine acknowledgement. Actual
video assertions remain unchanged. Three selected capture-protocol checks pass:
late arrival recaptures, no overlay uses one capture, repeated overlays fail.
This addresses the observed asynchronous platform setup, not production behavior.

Attempt41558303016 stopped in the auxiliary Tesseract process after its bounded
three seconds. The actual timeout screenshot contains the same measured target;
this is not a player failure. QA limits that small OCR task to one OpenMP thread
instead of competing with the two-core emulator, retains the same subprocess
bound, and preflights actual retained images before emulator setup. Three actual
captures resolve locally in0.20–0.22s with the negative frame rejected. OCR crop,
text, duration and thread count are retained for the next runtime observation.
No production or app-response deadline changed.

Attempt41559319998 passes native OCR preflight/runtime acknowledgement, both
themes, Back-first-exits-mode, all four actual viewport/orientation sizes and
16/16 edge points on every entry. Decoded square-marker ratios are BestFit0.96 and
Fill1.00465, both prior choices restored. Overall FAIL is retained because QA
tried Stretch below the visible short-landscape ScrollView without scrolling.
The actual tree shows its row clipped below791px while footer remains reachable.
QA now swipes that measured native scroll owner and observes a reachable target,
including the later restored Stretch radio. Two scroll-protocol checks pass:
reveal then final observation; unavailable choice rejects after four swipes.
The existing production scrolling panel and14 host checks remain unchanged.
