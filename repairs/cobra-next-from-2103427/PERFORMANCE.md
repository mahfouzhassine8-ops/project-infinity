# Measured performance scope

Same CI runner, actual baseline/candidate DEX translated for Robolectric API35; final run40818193096. No physical Fold or Android frame/CPU/thermal claim.

| Selected fixture | Signed2103427 | Candidate2103429 | Evidence scope |
|---|---:|---:|---|
| Identical position calls |7,000|7,000|Actual Activity method|
| Repeated setLayoutParams calls |7,000|0|Changed bounds still request layout|
| Median time per1,000 position calls |4.600ms|1.103ms|Seven host samples; not UI frame timing|
| Cold same-URL logo requests |100|100|Actual entry; recording existing executor|
| Executor submissions |100|1|No HTTP in this count fixture|
| Images updated after one controlled completion |1|100|Actual publication path; same bitmap instance|
| Distinct logo admissions before completion |12|4|Deferred attached requests drain on completion|

The separate loopback test runs the unchanged downloader and protected executor wrapper:9 distinct successful URLs cause9 HTTP requests, duplicates share a bitmap, at most4 jobs remain admitted, failures do not automatically retry, and unattached requests wait for attachment. It does not measure external provider latency.

First populated real Guide/EPG, provider tune/PiP/fold transitions, frame timing, CPU, battery and thermal changes have no accepted before/after physical measurement. Existing EPG identity/generation/in-flight suppression and bounded32-VOD/48-logo caches were inspected and retained. No speculative codec, lifecycle, global job or provider policy changes were made.

Retained-image regression check (actual API35 views and original callback): same pending view remove/add -> completion passes on27, fails on28, passes on29. This is restoration correctness, not a latency benchmark.

## Actual Android17 observations

Same configured API37.1 x86_64/ARM64-bridge/16KB fresh emulator; independent CI instances, sparse samples. Android Activity timings come from `am start -W`; the separate observer includes accessibility-dump overhead.

| APK / run | Cold Activity TotalTime | WaitTime | First-screen observer | Welcome PSS | Welcome RSS |
|---|---:|---:|---:|---:|---:|
| Baseline27 /40810969947 |8.252s|8.254s|13.505s|49,167KiB|180,244KiB|
| Final29 /40819347774 |4.973s|5.009s|9.686s|48,170KiB|178,052KiB|
| Final29 /40820333003 |6.836s|6.966s|12.564s|48,991KiB|177,236KiB|

One baseline and two final observations are insufficient to establish p50/p95, a causal startup gain or stable memory reduction. All are empty welcome screens before adding a provider. The first29 run later failed at a clipped menu observer; its honest welcome measurement is retained, not substituted for a functional PASS. Superseded28 samples remain archived separately and are not the final candidate comparison.

Final29 run40820333003 additionally imports four synthetic loopback video channels through normal UI, renders all eleven Mobile arrangements and passes an actual rendered-color pane swap. Visible counters advance before/after; four app-player Init records and no Release records corroborate no recreation in this finite recorded journey. Final four-stream PSS119,462KiB and RSS277,276KiB are one snapshot with no matched four-stream baseline: they do not prove absence of leaks, CPU/thermal efficiency or physical acceptance. No FPS/CPU/battery/temperature data was captured; no improvement is claimed for those metrics. All five modes have host integration coverage, not Android rendering acceptance.

[Raw measurement records and frame evidence](results/runtime/candidate29-final/EVIDENCE.json). The previous Infinity libkodi constructor failure is independent: Cobra's exported Java Activity runs on this emulator. Infinity was not launched, and no shutdown tests were run.

## Consolidated2103430 follow-up

The prior position/logo implementation and its signed29 measurements above remain unchanged. No new device-speed, frame, CPU, memory, battery or thermal improvement is inferred from the button/icon correction. Producer40965184656 verifies correctness through the actual signed29 DEX and corrected production DEX: visible Fullscreen/PiP/More presses yield `[PiP, PiP, Fullscreen]` before and `[Fullscreen, PiP, More]` after. The old test has one genuine assertion failure with zero errors; all six corrected interaction tests and three adjacent regressions pass. These are host routing results with explicit terminal spies, not physical Fold measurements.

Launcher changes select two existing resource IDs by normal Android configuration and add seven files; they introduce no background job, polling, activity alias, component enable/disable or startup hook. Nine focused icon checks and independent Android resource parsing pass. The signed30 observations remain archived; 430 is superseded and is not the delivery candidate. Samsung/Fold acceptance remains user-only.

The unaccepted430 icon background failed actual density-override inflation and is superseded before delivery. Final431 uses a nested white drawable, verified with native framework day/night/default/420-density rendering against signed27 and the430 negative case. Its button, layout and logo source remain unchanged; only resource XML and genuine version metadata change. These checks establish rendering correctness on the host, not device speed or Samsung acceptance.

## Signed 2103431 focused Android observation

The signed source remains `9ccc4c362a65118eeba38a8e7e4b0de5723c69af`, signing run40971769136, APK SHA256 `3fbf5abebdbdd9f96f30a69a213f086c617d2a9395f892dd1ce0142bf1b64471`. No new performance benchmark or production rebuild follows from the QA observations below.

Exact signed-APK run [40973858059](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40973858059) observed a visible Fullscreen coordinate press opening native fullscreen with Return to preview and Multi-View, outside system PiP. After Back and strip scrolling, the observer measured More, then tapped the Hero to reveal controls before pressing the old coordinate. No intervening frame or hierarchy establishes the final target after that layout-triggering reveal. Actual system PiP followed and the wait for the More menu failed. The run remains **FAILED**; it establishes neither a complete button-journey PASS nor a proven More dispatch defect. Later dedicated PiP/return and menu-reopen checks did not run. [Evidence and reviewed limits](results/runtime/candidate31-first-actions/REVIEW.md).

The same run's reviewed native Settings App Info frames show the intended white/black icon in light mode and original navy/cyan in dark mode. Pixel Launcher All Apps shows the correct light icon, then retains the light bitmap after the dark-mode switch. Resource inflation is corrected, while this observed launcher caching prevents a claim that every icon surface refreshes automatically. Samsung launcher, Finder, suggestions and monochrome palettes remain unverified. No cache reset, component toggle or unsafe workaround was introduced.

Focused run [40975572601](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40975572601), QA-only source `835f08814190767816a1ec3c14d8698745811c70`, **FAILED** when a fresh More target was unavailable; it issued no More press. Actual Fullscreen passed. After the extra reveal, the recorded geometry leaves More only five visible pixels at x=1011..1016 and places PiP at x=853..1011. The old `[937,827]` coordinate lies inside that PiP view. This explains why the old coordinate is unsafe after revealing, without establishing a More callback defect. [Fresh-target evidence](results/runtime/candidate31-fresh-target/).

Focused run [40976739449](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40976739449), QA-only source `8146d518eedecb22cd417785f88aa10ce2a9d608`, **FAILED before the first Fullscreen press**. The host-driven compressed `uiautomator dump` and separate `cat` exceeded the unchanged 3.5-second target-freshness guard. No Fullscreen, More or PiP press was issued. This observation-overhead failure neither proves nor disproves production routing. Earlier native Fullscreen passes and the six plus three host checks remain separate evidence. [Host-timing record](results/runtime/candidate31-host-timing/REVIEW.md).

The QA-only native UI Automator DEX JAR compiled to two QA classes and passed inspection plus peer review. Run [40979186412](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40979186412), QA source `0ed6848b3031ae512705e81804fe58538232de19`, **FAILED before Activity launch, icons or native-helper execution**. `install.txt` records `PerformingIncrementalInstall` and `Success` at 22,401ms. Hashing the installed 778MB APK then exceeded the unchanged 30-second ADB timeout. This is not an application failure or a helper-runtime result. [Incremental-install/hash evidence](results/runtime/candidate31-incremental-hash/).

The narrow QA correction used `--no-incremental -r` with the identical APK. Official AOSP behavior and peer review confirmed full transfer before install success; that correction added no installation retry, timeout increase or installed-byte hash-guard weakening. Run [40980338717](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40980338717), QA source `f0cc061cedd9fedb6e04bbf03dbd6c1d9ea97649`, **FAILED before launch** when the 30-second full-stream install truncated after 541,530,240 of 778,358,062 bytes. The compiled native helper, icons and button actions never ran. [Stream-truncation evidence](results/runtime/candidate31-stream-truncation/).

Explicit management clarification subsequently authorized an appropriate QA infrastructure budget only for nonincremental installation and full installed-file SHA256: APK size at 10MiB/s plus 45 seconds, capped at 120 seconds (120 for this APK). Generic ADB remains 30 seconds. The application control timer stays four seconds, native coordinate freshness 3,500ms and attempts seven; the full installed-byte hash guard remains intact. CI uses no compressed or staged APK transport. A separate host-only zstd preflight produced 325,147,942 bytes and verified a real round trip; it was not used for CI device installation and demonstrates no device performance gain.

Run [40981874553](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40981874553), QA source `62d265519f9fdf7678e79038425eca8dab1419f7`, is **IN PROGRESS** against the identical original-key signed431 APK. The compiled two-class native helper queries fresh public bounds and injects actual coordinates in one process, with post-action hierarchy/PNG capture and independent outcome recording. It never executed during the earlier prelaunch failures, and no current runtime result is presumed. Production source and the signed APK remain unchanged. Cancelled run40975410956 had an invalid source checkout; no emulator or APK installation ran there. These finite emulator observations do not measure physical Fold responsiveness, frame pacing, CPU, memory growth, battery or thermals.
