# Cobra all-layout reflow — implementation checkpoint

The actual signed 2103421 Cobra module supports one player and Multi-View counts
2–4; `openMultiView` and `CobraTileStore.reconcile` reject larger counts.

The shipped `cobraLayoutPlayerPanels` replaces MATCH_PARENT video/canvas parameters
with current pixel dimensions. Its configuration callback can run before the
new parent size is measured. The Multi-View canvas listener only lays out tiles:
it cannot recover a canvas that remains pinned to its prior parent size.
A focused test using the shipped method reproduces a 480-pixel canvas under an
1800-pixel parent without any failed stream.

`CobraWindowReflow` observes the measured window before rendering. On a changed
surface, display, dimensions, insets, padding or density, it invokes the existing
panel, tile and guide layout methods, then requests one further traversal. It
uses no player or persistence API. Attach/detach manages its single observer;
unchanged geometry does not schedule a resize loop. Existing Fit/Fill, enlarged
layout and player lifecycle algorithms remain intact.

Only Cobra-owned definitions change: Activity initialization installs the observer;
two narrow Activity methods expose the current presentation and existing layout
operations; a new Cobra helper observes geometry; Cobra's component version is
advanced. The existing player/retune/seek/audio/shutdown methods are unchanged.

The selected checks are recorded in TEST-SCOPE.json. Initial Android view tests
reproduced the original defect and passed cover/inner/rotation measurement for
single-player and all 2–4 tile counts, Fit/Fill, and enlargement. These are
Robolectric view tests using shipped bytecode; they do not claim real decoded
stream continuity or physical Fold acceptance. Further production-DEX integration
and preservation checks are in progress.

The original-key release gate remains binding. The linked brief records 2103421
as an unaccepted candidate and explicitly forbids silently advancing acceptance.
Implementation proceeds now; acceptance and any dependent signing remain pending.
