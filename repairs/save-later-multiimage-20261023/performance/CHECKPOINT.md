# Infinity 2103401 performance and responsive continuation

This addendum continues the complete original assignment and shared-selection
contract. It does not replace Universal Search, Option B, full synopses, saved
state synchronization, the retained clock correction or stability work.

The coordinated source checkpoint is `c0dba465e6b74af7bd82ea0c16755d5bf7508f1e`,
signed successfully by build `40086558043`. Its actual APK and four ZIPs were
retrieved through the authenticated GitHub connector. Independent verification
confirmed original certificate/signing schemes, unchanged manifest/package,
ARM64 and exact ZIP/APK membership. See `SIGNED34-VERIFICATION.json`.
The immutable CC34 overlay and its passing evidence remain intact.

The next coordinated candidate uses CC0.3.5.35, WB1.0.16, UI0.1.18 and skin242.
The extra source layer retains the exact CC34 admission, adding the new complete
source contracts. No user databases, provider binaries or TrackIt route-memory
functions are changed. No authentication or workflow authorization is bypassed.

## Independently implemented improvements

- Search discovery reads each manifest once and reuses source bytes, hashes and
  canonical syntax across alternative adapter checks within the same verified
  operation. Actual provider execution still validates before and after dispatch.
  Installation, enable/disable, update and removal invalidation remains intact.
- Saved lists prepare watched membership for at most 100 visible cards from the
  same fresh snapshot, instead of rescanning the history for every card. Full
  identity-conflict checks remain authoritative. No persistent cache or writer
  changes were introduced. Home uses the same preparation function.
- The resident service avoids entering its persistence wrapper for settled idle
  ticks. All preexisting persistence/startup methods are byte-preserved. Live
  policy changes and incomplete startup stages still enter the original tick.
- Option B no longer reads native viewport geometry on every action, focus and
  click. Initial display and exact-owned native resize callbacks perform reflow.
- Infinity quick-action/selection dialogs now fit the actual available viewport,
  and use an unreserved backdrop control ID. Reflow preserves the list instance,
  selected row, focus and scroll state. Their original options/actions remain.
- The two Home Continue panels now fit their actual available height instead of
  drawing 410-unit cards into as little as 157 units. Native axis/layout code was
  compiled to verify the actual bounds. Original tall-layout geometry remains.
- Ten owned Home poster templates use Kodi's existing asynchronous path for
  nonbundled local artwork. Remote artwork was already asynchronous; no remote
  decode or frame-rate improvement is claimed.
- A read-only API37 metrics helper can observe an already-running app. It does
  not launch, navigate, reset, stop or alter refresh settings. HWUI samples are
  kept separate from native SurfaceView data; elapsed capture time is never
  substituted for loading or touch latency.

## Focused host measurements

Identical capability/data fixtures compare the signed CC34 source with the new
source. These are actual Python function timings with mocked Kodi interfaces,
not phone screen-load or frame-pacing measurements.

| Path / fixture | CC34 | Optimized |
|---|---:|---:|
| Cold discovery, same four provider fixtures | 74.292 ms | 63.211 ms |
| Cold Search submission, same fixtures | 82.210 ms | 62.266 ms |
| Source reads in that submission | 62 | 32 |
| Warm inventory refresh | 2.048 ms | 1.176 ms |
| 100 visible cards / 100 watched records | 30.079 ms | 9.086 ms |
| 100 visible cards / 1,000 watched records | 238.127 ms | 25.928 ms |
| 100 visible cards / 4,000 watched records | 804.396 ms | 61.774 ms |
| Stable service minute, persistence admissions / writes | 120 / 0 | 0 / 0 |
| Modeled Option B input cycles, 1,000 action/focus/click groups | 12,000 geometry reads | 0 geometry reads |

Popup cancellation remains snapshot-dominated; small-profile latency showed no
clear improvement and is not presented as a speed gain. CC33 measurements have
fewer provider capabilities and are explicitly not an equivalent Search speed
comparison. Original failure receipts and previous passing evidence are retained.

## Not accepted or physically verified

Actual Android17/API37 feature execution remains NOT RUN because manual workflow
dispatch is unavailable through the connector and the user cannot sign in.
No more credential/browser sign-in requests are authorized in this continuation.

Physical Fold cold/warm screen loading, touch/menu latency, scrolling, animation,
frame pacing, sustained CPU/RSS, fold/rotation/split/popup rendering and refresh
propagation remain NOT RUN. Source improvements do not establish Infinity-wide
smoothness, loading completion or responsive acceptance.

The physical Search Enter -> Home freeze remains unresolved. The original fault
stacks for pure-virtual and Scudo failures are absent; no speculative native
lifetime repair is claimed. Previously supported repairs and diagnostics remain.

Shutdown verification remains independent and NOT RUN. No final lock or release
acceptance is asserted. Install-over signing/package identity remains mandatory.
