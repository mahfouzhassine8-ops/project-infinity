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
