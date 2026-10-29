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

## Integrated resource correction D2

Actual signed baseline cold-logo test:100 views requesting the same URL submit100 existing-executor jobs. A controlled old completion also overwrites an ImageView rebound to another URL. New CobraLogoRequests coalesces same-URL requests, admits at most4 distinct logo jobs on the existing executor, and matches weak view bindings before publishing. It uses the existing bounded48-image cache and the exact unchanged original downloader, byte limit,4s connection/5s read limits and protected task wrapper. It introduces no executor, service, periodic polling or failure-retry loop. Detach removes binding/waiter listeners. At most4 active requests retain an original callback view; the remainder are weakly held and only admitted when attached. Reflection caches use concurrent maps because the existing downloader runs on its worker.

Final local25 tests pass, including a real unchanged downloader over loopback PNGs:9 distinct URLs produce9 fetches with at most4 unfinished admissions, one shared URL fans out one bitmap, HTTP failure finishes without automatic retry, and unattached requests wait for attachment. The controlled100-view fixture changes submissions100→1 and delivery after one completion1→100. These are host work/ownership observations, not live provider or physical performance.

CI40807697956 passed the earlier21-test source and exact owner packaging. API37 launch CI40807700925 failed before emulator/application execution because pinned cmdline-tools22.0 was absent; the Cobra lane now includes the existing setup-android15859902 step before the unchanged SDK gate. No app failure was inferred. Final integrated CI/signing follows.

## Final-review correction R1 —29 supersedes unaccepted28

The additional same-view reparent case passes on signed27 and fails on28: removing the view also removed its new logo URI binding, so a completion arriving after reattachment had no waiter to update.29 removes offscreen waiters on detach, while retaining only the view-owned, weakly indexed binding. Attachment reuses the existing bitmap cache or joins the still-running URL request; it never starts a duplicate request for an active URL. The static Activity map uses weak keys/values, and the per-view maps use weak keys, so this does not create a global strong view/Activity root or a polling observer. No player, native, shared or shutdown code changes. CobraLogoReattachTest is added to both baseline/candidate selection before execution. Failed28 evidence is retained.28 is superseded and must not be the final install candidate.
