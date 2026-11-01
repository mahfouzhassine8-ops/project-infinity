# Cobra quality refresh from accepted 2103442

Three measured Cobra presentation hot paths changed. Layout calculations,
themes, player callbacks, providers, lifecycle, persistence and background jobs
retain their accepted behavior. The final candidate is2103444; internally signed
2103443 is withheld after the additional layout finding below.

1. `InfinityLiveActivity.formatTime` now uses `CobraGuidePresentation.time`.
   A per-thread formatter and Date replace construction per label. The original
   US pattern is exact; each call checks the current default timezone. There is
   no cached formatted text, timer, worker or activity reference.
2. `cobraNextProgram` uses a private copy of its original directory lookup,
   `cobraNextProgramList`. Only its full-plus-short-EPG merge is reused. A weak
   activity-owned LRU keeps at most32 projections /16384 input programmes and
   bypasses inputs larger than4096. Every use compares list identity, size,
   order, each programme identity, start, stop and title. Same-size mutations
   invalidate correctly. Other metadata remains live on the original objects.
   The original merge routine remains the sole precedence/deduplication/sort
   implementation. The next programme is still selected against the clock on
   every query. Cached lists are private to this read path; all other callers
   receive the original independent list behavior.
3. `CobraSix.smallPreviewPip` routes its existing `setLayoutParams` operation
   through an equality guard. Android baseline logs showed repeated layout
   requests; an actual-owner host check reproduced32 requests for32 identical
   rectangles. The guard produces zero. Native placement, obstacle avoidance,
   visibility, touch and PiP callbacks are unchanged. Genuine resizing and
   visibility transitions, Pro exclusion and player/texture identity pass.

Source/class proof:7171 of7174 original Cobra classes are identical. Two original
activity methods, one added private lookup, the one PiP placement call and Cobra
version metadata change; seven helper/nested classes implement the presentation
work. All1801 other activity methods, all46 other CobraSix methods, original
fields/annotations and the second Cobra DEX remain exact. Cards LIVE/Preview
callbacks, layout calculations, themes, Pro/Sports, Multi-View, display transforms,
provider execution and shutdown remain exact.

## Measured host outcome

Actual owner DEX translated to JVM, API35 native-graphics fixture;21 warmups and
42 samples per measurement. Same synthetic EPG, same host. These are not Fold or
Android decoder latency measurements.

| Operation |442 p50 / p95|candidate p50 / p95|allocated bytes per batch, before → after|
|---|---:|---:|---:|
|500 programme time labels|1.253 /3.158ms|0.265 /0.336ms|1,580,000 →780,000|
|100 next-programme queries,168 full +14 short entries|4.667 /12.731ms|0.620 /1.050ms|9,136,800 →36,000|

The layout observation measures32 identical placement calls:32 layout requests
before, zero after, with the same final rectangle. This is not an Android FPS claim.

No claim is made that these microbenchmarks predict whole-app speedups, battery,
thermal behavior or decoder throughput. Existing432 profile/cache gains are retained,
not counted as new improvements. No native crash repair is claimed.

## Verification and historical fixtures

39 current focused host checks pass, including75 mode/screen/theme combinations,
90 font/screen/theme combinations, generation-safe publication,120 mutable-guide
edits,100 replacement publications, cache bounds, original Cards LIVE state/touch,
approved Pro geometry/touch, all11 Multi-View arrangements, profile/filter freshness,
Cards reuse/scroll/focus and all14 existing display-size modes/custom controls.
Actual full rendered Cards/Pro images were visually inspected; native image/video
decoding and Samsung rendering remain distinct from these host results.
Six matching full Pro renders have zero changed pixels against accepted442.

The fresh444 host directory initially omitted the existing baseline geometry
fixture and two evidence-output properties. Seven checks ended in those setup/
output errors, with no assertion failures; the other32 passed. After restoring
the exact fixture and output configuration, only those seven were rerun and
passed. Both runs and the configuration correction are retained in
`final-evidence444`; no production code was changed to address these errors.

The old439 Display fixture tapped the small preview and expected immediate
fullscreen. Accepted440/442 opens the preview menu first. QA now presses the actual
Fullscreen menu row through decor input; all7 Display checks pass unchanged beyond
that setup route. No production callback was modified to satisfy the fixture.

Historical440 Preview tests refer to an absent diagnostic-only helper and expect
a synthetic timeline to produce the old preview-emblem LIVE state. After removing
only that nonexistent diagnostic field, all6 stop in the same setup assertion.
The identical assertion was reproduced on the exact accepted442 owner. These tests
are not counted as passes. Current442 Cards/Pro tests verify real Preview/menu
presses and sole LIVE-dot playback behavior successfully. The historical failure
and the accepted-owner control are retained; no speculative pulse change was made.

## Android evidence and targeted harness correction

Run41280005762 installed the exact original-key442 APK and loaded20,226 synthetic
channels. Actual screenshots show all five front modes and decoded loopback video.
It stopped before inner-display tests because the reused drawer harness correctly
requires density to stay constant, while the new caller passed240 after setup480.
The exception is in `qa.CobraDrawerDriver.resize`, not the app. No application ANR,
SIGBUS or SIGSEGV was found in this run. First-screen observation14.251s includes
the informational Android compatibility notice and UI-dump overhead, not just app
startup. It is not a device-performance benchmark.

The correction uses one320dpi emulator density for both1080x2520 and1600x1800
window sizes. Existing native size/readiness guards remain; no deadline increase.
The generic legacy workflow job also incorrectly admitted the new feature and
rejected its name; its exclusion now matches the dedicated job. Final verification
will compare accepted442 and the sole signed candidate by install-over, without
diagnostic APKs. Both prior failures remain failures in their original run.

Artifact: https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41280005762/artifacts/13073182144

Run41281620906 then reached accepted442 TV Grid. The injected test swipe began
too close to Android's bottom system-gesture area; InputDispatcher explicitly
records Home taking that gesture. Cobra remained alive; the fatal exception was
in the QA process. The correction uses the measured list's interior and retains
strict package/input assertions.

Run41282442794 stopped on accepted442's visibly open View menu because the old QA
helper assumed exactly one ScrollView anywhere on screen. It did not distinguish
the menu from a scrollable page beneath it or wait for its layout readiness. The
corrected helper follows the actual mode row's parent chain, requires one stable
ancestor scroller within the existing12-second window, and records observations.
The old assertion did not record its count; none is inferred as a measured result.
Neither run installed the candidate, and neither is counted as a candidate PASS.
The final444 check will use the same corrected harness and original-key APK.

Run41284441609 completed all five accepted442 front modes and their interior
scroll gestures, then stopped at the QA stable-density assertion before resizing
or installing444. The captured Android configuration is correctly320dpi. The QA
UiAutomation command route produced an empty graphics dump and did not return
the expected density text; its original raw density response was not retained.
QA PID5969 threw the assertion while Cobra PID5400 remained active with decoded
loopback video. The evidence is in `android-qa/evidence-41284441609`.
`android-qa/OS-COMMAND-CORRECTION.md` records the narrow command-output correction
and strict preflight before the next installation. Signed444 production bytes
remain unchanged. This failed baseline run is not a candidate PASS.

Run41285455894 passed the OS-command preflight and the full accepted442 public
mode/scroll/drawer/resize/cover-return journey. It failed later in the legacy
warm-return observer because CLI UIAutomator produced no XML file. The successful
journey is retained separately from that failed overall workflow. The existing
reviewed live-root observer is now connected through the original notice-capture
callback for all relaunch paths; its source, strict preflight, root budget and
target-age guard are unchanged. The completed baseline matrix is reused with
exact APK, outcome and journey-source hashes. The remaining candidate run does
normal baseline setup, warm return, original-key install-over and the complete
candidate matrix; it does not repeat the passing baseline journey. See
`android-qa/WARM-OBSERVER-CORRECTION.md` and `android-qa/evidence-41285455894`.

Run41286787645 closed baseline warm observation and verified actual original-key
444-over442 installation, exact installed APK bytes and unchanged UID. Candidate
launch reached the existing Android compatibility notice; its exact informational
OK was pressed once. The post-notice root query completed at2084ms against the
unchanged2000ms observer budget, so its late result was discarded and the run
failed before the candidate journey. The app was resumed in the retained activity
dump; that is not a passing functional matrix. No further native attempt, timeout
change or APK rebuild followed. `delivery444/android-41286787645` preserves the
exact failure and install-over evidence. The testing candidate is delivered with
this limitation; full native interaction and physical Fold acceptance remain open.

## Release boundary

The sole original signer is retained. Only its authorized branch/version/baseline
binding changes, plus registration of the new Cobra helper root. All existing
source, signature, ownership, field/default and payload gates remain. The approved
442 lock is checked in addition to every older protected lock. Infinity/shared ZIPs
are copied exactly; only truthful Cobra last-updated metadata changes in the shell.
No candidate lock or acceptance is performed.
