# Combined profile-data reuse versus accepted signed2103431

The fixed comparison completed in the selected order B431 → combined prototype → combined prototype → B431. Every run used the same actual-method fixture,21warmups and21timed samples per entry. All8 selected test executions passed with0failures/errors/skips. PooledN=42 per variant/entry.

| Actual projection entry | Accepted431 p50 / p95 | Combined prototype p50 / p95 | Observed change p50 / p95 |
|---|---:|---:|---:|
| `cobraChannelsForCurrentView` | 16.108250 / 18.689908ms | 2.167379 / 3.203121ms | -86.54% / -82.86% |
| `cobraGuideChannels` | 17.179647 / 22.652607ms | 2.129261 / 2.408302ms | -87.61% / -89.37% |

Both baseline runs and both combined-prototype runs show the same direction. Raw per-run samples and class/input hashes remain attached. Percentiles describe finite host samples (p50 midpoint for evenN, p95 nearest rank), not a physical device distribution.

The policy is evaluated on every call. Each separate20226-channel work-count call still performs40452 active-profile reads and40452 raw profiles-string reads. Only parsing identical private JSON data is reused. Hidden preference reads and distinct default-set identities fall20226→1 through the independently guarded projection correction.

Before timing, the same six new profile/API parity cases passed on the exact signed431 classpath and on the prototype. Two projection count/semantic cases also passed, without timing. They cover mutable public profiles copies, raw edits/ID switches/lock-unlock, malformed/wrongtype/null values, first duplicate/missing fields/optBoolean/null-ID exception semantics, the64Ki admission boundary and uncached valid oversize data, thread separation, no helper preference writes, input inventory identity/order and next-call filter state.

This unsigned host prototype contains Activity projectionV2 plus one FeatureRuntime method wrapper and exactly two Cobra helper classes. Public `profiles()`, PIN/unlock/source/profile getters, existing fields and all other54 FeatureRuntime methods remain byte-identical. All4988 other existing translated production classes and support dependencies remain exact. Private cache entries hold only raw String and private JSONArray, one per thread; no authorization result, Activity/Context/preference owner, timer or service is cached or added.

The prior V1 regression and V2 mixed timings remain preserved under the earlier QA results. This materially new parsed-data correction follows source diagnosis and successful parity checks; no old failure was relabeled.

The measurements cover ALL channels with empty search, no hidden/custom filter and two synthetic sources on Robolectric API35. Other filters/profiles have correctness coverage, not large-inventory latency measurements. No APK build, signing, CI, emulator, Android startup/frame/FPS, physical Fold, CPU, memory-growth, battery or thermal improvement is claimed.
