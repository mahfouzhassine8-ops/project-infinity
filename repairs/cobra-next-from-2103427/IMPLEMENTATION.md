# Cobra continuation 2103428

The complete 188-line user brief was read before implementation. Continue from signed2103427; Infinity and the minimal Android contract remain exact ZIPs. All new behavior is Cobra-owned.

- Added eleven presentation arrangements to the native Fit/Fill picker for Mobile, Compact, Cards, TV Grid and Pro. The existing measured-window reflow, Fit/Fill crop, insets and player binding paths remain intact. Preferences are separated by existing active profile and screen count.
- Deliberate hold plus movement enables pane swaps, promote-to-main, valid corner/overlay/columns/grid targets and a live preview. Move/Arrange native rows provide a remote equivalent. The same tile/player/texture objects remain owned by their original channel; selected audio follows its key. No tune, seek, prepare, pause, release or volume change is performed by arrangement code.
- Stationary long-hold invokes the original context menu on release, allowing hold-then-move to be distinguished. This timing requires physical acceptance. Ordinary taps retain the original tile click callback.
- Snapshot validation rejects changed profile, player/binding/texture identity, stopped stream, changed bounds/insets/density/mode, background/PiP, multiple pointers and canceled/invalid drops. New menu callbacks validate the actual menu owner before closing, then validate session identity before applying. Detach cancels the single hold timer and removes listeners. At most four pane listeners and one preview exist.
- More alone moves to the end of non-Pro preview controls, including retained-view mode transitions. Original Pro preview ordering is restored. Existing full-player controls and the entire CobraSix/Pro/Sports class families remain unchanged.
- Additional demonstrated defect D1: cobraPosition always allocated parameters and requested layout, even with equal bounds. It now returns early only for exactly equivalent default FrameLayout parameters. Resize, clamping, relative/gravity/non-default parameter behavior keeps the original semantics.
- Chooser: one literal replacement from Last updated in to Version. Only Cobra authenticated offline version metadata advances; Infinity stays2103427. All other chooser classes/resources/preferences remain exact.

## Local focused evidence

21 actual-production-DEX host tests pass, plus14 release-gate negative controls. All11 options are selected through the actual picker in5 modes, with resized bounds; all pane pairs are swapped for2–4 screens in5 modes. Tests cover transforms, remote actions, cancellation/stale sessions, profile-specific reuse, tiny windows, original context menu, More/Pro/Sports order and six existing measured-window bridge tests. Players are explicitly inert proxies: this proves object/call/geometry behavior, not live decoders.

Matched host position fixture: baseline7,000 repeated calls ->7,000 setLayoutParams; candidate ->0. Seven samples of1,000 calls: baseline median2.981ms, candidate1.126ms. These are host method observations, not startup, FPS, CPU, thermal or battery results. Full outputs and input hashes: results/local/HOST.json.

No shutdown tests, user-device operations or accepted-lock changes. CI source-bound verification, final owner packaging, original-key signing and physical acceptance remain pending at this checkpoint.
