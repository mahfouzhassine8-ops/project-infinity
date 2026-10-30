# Fixed ABBA projection comparison against accepted 2103431

All four fixed runs passed the same two selected tests. Each entry received 21 warmups and 21 timed samples in every run; pooled N=42 per variant/entry. Order: signed431 → unsignedV2 → unsignedV2 → signed431. The V1 regression remains preserved separately.

| Actual entry | Signed431 p50 / p95 | UnsignedV2 p50 / p95 | Observation |
|---|---:|---:|---|
| `cobraChannelsForCurrentView` | 15.785469 / 22.978989ms | 16.661656 / 21.425022ms | p50 +5.55%; p95 -6.76% |
| `cobraGuideChannels` | 17.169660 / 30.035034ms | 15.543834 / 21.164019ms | p50 -9.47%; p95 -29.54% |

The result is mixed: current-view median latency remains higher, while Guide median and tail samples are lower. This does not establish a general speed improvement. Percentiles describe these finite host samples (p50 midpoint for even N; p95 nearest rank); two JVM runs per variant remain subject to JIT, GC and process variation.

Every separate work-count call observed hidden preference reads and distinct default sets fall from20,226 to1. Profile JSON reads and active-profile reads remain40,452, with assertions retaining the existing authorization checks. The measured timing case is ALL channels with empty search, no hidden/custom filter and two synthetic sources. Other filter/profile states have correctness coverage, not large-inventory latency measurements.

The semantic scenarios, input inventory size/order/object identities and next-call freshness passed in every run. The V2 Activity overlay changes exactly two methods; all4,989 other translated production classes and support dependencies remain exact. The unsigned prototype is not an APK release.

No Android startup, frame timing, physical Fold, CPU, memory-growth, battery, thermal or user-data acceptance claim. No APK build, signing, emulator, CI or shutdown test occurred.
