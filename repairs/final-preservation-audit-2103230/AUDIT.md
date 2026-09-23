# Cobra 2103230 corrective audit — test candidate

## Authority and preservation
Start only from locked-infinity-cobra-2103229-multiview-stability-fill-passed, commit 7fbfc5ade1e96b272b8e7ba584332cb6c81d01bc. The user's complete supplied audit brief remains the scope, with the confirmed substitution of 2103229 as baseline and Multi-View Fill Screen treated as existing functionality. No new user-facing feature or redesign is authorized. The supplied brief ends mid-sentence; no missing requirements have been invented.

Exact rollback (APK, original repository, reconstructed generated shell, native packaging input, source receipts, hashes and restore instructions) was created successfully before app-code changes in run 35820419796. The rollback archive does NOT include device data. Preserve providers, settings and Kodi userdata before testing. Do not clear data/uninstall merely to bypass Android's version downgrade rules.

## Source findings and corrective delta
1. Error fallback captured a global playback epoch. Pausing a different Multi-View tile invalidated this player's pending fallback. The callback now uses its own binding's intent epoch plus current ownership, playback permission, explicit pause and dismissal guards. Pending fallback is distinguished from the selected fallback route.
2. The Live ENDED recovery flag could remain latched when reprepare moved through BUFFERING back to ENDED without READY. The second permitted attempt was consequently suppressed. The flag now clears before external player calls, with state-serial/intent guards. Preview ownership was missing from the eligibility check and is now recognized. The original two-attempt limit is retained; legitimate VOD/catch-up completion is excluded.
3. Multi-View's generic error-first policy could reprepare an ENDED player after the separate live-ended budget was exhausted. ENDED remains solely owned by the bounded live-ended path. The prolonged-buffer watchdog no longer aborts a loader that is actively working or has made recent progress. Recovery budgets reset only on continuing frame progress, not a stale interval followed by one isolated frame. Existing timeshift and surface recovery mechanisms remain their own owners.
4. A promoted Multi-View player still belonged to the tile-player array, so the grid's Fill preference overrode fullscreen Display choices. Fill now applies only to the actual tile TextureView. Configuration/panel layout chooses the visible fullscreen viewport instead of the hidden grid while promoted.
5. Safe-area calculation subtracted root insets even when the parent had already consumed them. Insets now reflect only the actual overlap between the canvas and root safe areas. A non-consuming inset-change listener reflows the existing tiles; Fit/Fill layout fractions and video crop math are unchanged.

## Live-ending diagnostics and unresolved source cause
A bounded 48-event trail per session records state, play requests, media/timeline transitions, loading completion/cancellation/error, decoder initialization/release and recovery attempts. An unexpected live ENDED snapshot includes the session/channel hash, ownership, requested/playing/loading state, buffer and position, window flags and HLS end-tag/type/sequence metadata when available. It is captured from the combined event callback. No URLs, request headers, credentials or arbitrary provider error messages are added to this trail.

Calling prepare() is not proof of recovery. The verified-recovery event requires the same current session/intent, READY/isPlaying, position progression and rendered-frame progression. The actual provider/network/manifest reason for the user's random Live TV termination is NOT established without failure-time device diagnostics. These source corrections must not be presented as a demonstrated cure for every provider or decoder failure.

## Test evidence and limits
The runner records explicit expected/executed test identities, failures, skips, fixture hashes and raw Gradle logs. The seven focused regression tests run unchanged against the exact parent and candidate; six target defects are required to reproduce as assertions on the parent, and all must pass on the candidate. Eight additional candidate tests cover bounded tracing, intent guards, Fill ownership, inset overlap and the actual production tile geometry with non-overlap plus exact area coverage.

Selected inherited suites cover existing audio focus/call/PiP controls, lifecycle, provider boundaries, timeshift startup/transport, network family, MPEG-TS access units/timeline/clock handling, provider pacing, approved branding, file-picker behavior, network and safety policy. This is an explicit selected regression inventory, not a claim that every historical superseded UI fixture was executed. RESULT.json and ACCEPTANCE.json are authoritative; this document does not itself assert tests passed.

## End-to-end coverage matrix
| Brief area | Scope in this candidate | Remaining real-device evidence |
| --- | --- | --- |
| Random Live TV ending | Source ownership/callback/recovery corrections; terminal diagnostics; controlled red/green tests | Failure-time provider/HLS/TS/network/decoder evidence; sustained live playback |
| Player controls / audio / lifecycle | Selected inherited Android suites; actual state transitions with controlled players; unchanged control builders | Audible call behavior, volume/subtitle interaction, navigation under real streams |
| Fold / viewport / system bars | Actual layout policy and inset overlap tests; promoted fullscreen correction | Fold/unfold, cover/inner, cutout/status/gesture bars on hardware |
| Multi-View / enlarge / fullscreen / Fill | Inherited 227/229 tests plus runtime ownership and exact grid union tests | 2/3/4 hardware decoder sessions, real frame continuity, resource pressure |
| Navigation / Smart Return | No source changes to navigation contracts, Main, Splash or Smart Return; byte-preservation gate | Native side/back gesture, process recreation, correct destination restoration |
| Movies / TV / trailers / episode UI | Approved implementation and typography preserved byte-for-byte; VOD completion excluded from new live logic | Provider catalogue, playback/resume/next episode and exact shelf return |
| TV Guide / EPG | Mapping, schedules and provider code preserved; no fabricated data | Providers with/without EPG, actual focus/scroll behavior |
| UI consistency / themes | No redesign or theme/resource changes; approved artwork/picker suites; geometry-only corrections | Complete visual sweep of all screens/dialogs in Light/Dark/OLED |
| Performance / stability | Bounded trace memory; ownership guards; no additional network polling/players | Long-run memory/ANR/crash/decoder/refresh measurements |
| Health Center / diagnostics | Existing UI preserved; bounded structured per-session observations | Failure-time export verification and privacy review of actual device export |
| Integrity | Exact source inventory, unreviewed Activity-byte gate; native/assets/resources/secondary-DEX/signing checks | Installation/update and user-data preservation on the target device |

This remains a TEST CANDIDATE until physical-device checks pass. The locked 2103229 branch is not changed or superseded by a successful build alone.
