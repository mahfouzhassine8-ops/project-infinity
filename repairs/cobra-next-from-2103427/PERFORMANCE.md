# Measured performance scope

Same CI runner, actual baseline/candidate DEX translated for Robolectric API35; run40809094407. No physical Fold or Android frame/CPU/thermal claim.

| Selected fixture | Signed2103427 | Candidate2103428 | Evidence scope |
|---|---:|---:|---|
| Identical position calls |7,000|7,000|Actual Activity method|
| Repeated setLayoutParams calls |7,000|0|Changed bounds still request layout|
| Median time per1,000 position calls |5.472ms|1.748ms|Seven host samples; not UI frame timing|
| Cold same-URL logo requests |100|100|Actual entry; recording existing executor|
| Executor submissions |100|1|No HTTP in this count fixture|
| Images updated after one controlled completion |1|100|Actual publication path; same bitmap instance|
| Distinct logo admissions before completion |12|4|Deferred attached requests drain on completion|

The separate loopback test runs the unchanged downloader and protected executor wrapper:9 distinct successful URLs cause9 HTTP requests, duplicates share a bitmap, at most4 jobs remain admitted, failures do not automatically retry, and unattached requests wait for attachment. It does not measure external provider latency.

Startup, first populated Guide/EPG, real tune/PiP/fold transitions, frame timing, RSS/CPU, battery and thermal changes have no accepted before/after device measurement. Existing EPG identity/generation/in-flight suppression and bounded32-VOD/48-logo caches were inspected and retained. No speculative codec, lifecycle, global job or provider policy changes were made.
