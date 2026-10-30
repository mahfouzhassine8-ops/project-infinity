# Finite accepted-431 Cards Android baseline

This separate QA entry point measures the exact accepted, original-key signed
2103431 APK. It creates no application build and changes no production source.
The selected scope is recorded in [SCOPE.json](SCOPE.json). The approved Cards
image is not required to measure the old Cards implementation; this harness
makes no visual-parity claim.

The root task must explicitly select its manual Android workflow before use.
The author performed source/offline checks only, never Android or CI execution.
Use a fresh disposable API37 emulator, not the user's phone. Existing
`android_probe.probe` verifies that environment and the exact installed APK,
uses the established complete-file installation/hash budget, and preserves the
known Android compatibility notice before selecting OK once. Signature output
from the parent's actual `apksigner verify --verbose --print-certs` is mandatory;
the expected original certificate and v1/v2/v3 verification must match.

## Fixture preparation in the later selected CI job

Use the existing synthetic-video generator once, then generate the finite
inventory alongside its four clips:

```sh
python3 repairs/cobra-next-from-2103427/android_candidate_journey.py --generate-media runtime-media
python3 repairs/cobra-next-from-2103427/cards-from-2103431/android-qa/generate_fixture.py --out runtime-media --require-media
python3 -m http.server 8765 --bind 0.0.0.0 --directory runtime-media
```

The HTTP server must remain available while the independently selected emulator
script runs. It is local QA infrastructure. The generator writes exactly 20,226
unique channel names/IDs/URL queries across twelve groups. Those URLs reuse four
explicitly synthetic local video files. Only the first 32 channels have current
and next XMLTV programmes; the remaining 20,194 channels honestly have no guide.
Logos are omitted, so provider-logo latency, image decoding and visual parity
are not measured. No approved-reference or broadcaster imagery is used.

`FIXTURE.json` records the anchor, valid schedule windows, text/media hashes and
all counts. Explicit `--anchor-epoch` reproduces identical text bytes. The default
anchor is the generation minute minus five minutes, providing a bounded current
programme window. The runner refuses an already-expired initial current window.
Retain the same fixture bytes/anchor for a comparable candidate run, or disclose
any intentional timeline adjustment. Nonempty media files are hashed; the text
generator does not claim to validate their format or playback.

## Later selected emulator entry point

```sh
python3 repairs/cobra-next-from-2103427/cards-from-2103431/android-qa/baseline.py \
  --signed runtime-signed \
  --signature runtime-results/SIGNATURE.txt \
  --fixtures runtime-media \
  --out runtime-results/cards-baseline \
  --observer-jar runtime-observer/CobraImmediateHierarchy.jar \
  --observer-receipt runtime-observer/BUILD-RECEIPT.json
```

The result directory must be fresh. The signed directory must contain the
existing accepted APK plus its matching `BUILD-RECEIPT.json`. Baseline/source,
version, original signer, fixture hashes and schedule validity are checked before
installation. A changed APK cannot silently become the baseline.

The normal source form receives name, local M3U URL and local XMLTV URL. If
source validation itself opens the existing fullscreen player, one observed Back
returns to browsing; no Fullscreen/PiP/More button scenario is invoked. Cards is
selected through the normal Views picker. The harness then requires the exact
Cards heading, All-channels wall, actual 20,226 header count, one visible native
GridView and real fixture channel-card nodes. An unconfirmed state fails with
native XML/PNG and diagnostics; it never becomes a successful loading metric.

Three HOME/normal foreground returns reuse the strict per-launch OS-notice
helper. No persistent notice suppression or compatibility/native change occurs.
Eight swipes use current native grid bounds and require observed card movement.
The harness imports shared Snapshot/bounds/native-dialog-item utilities only;
it does not invoke the historical Pro journey or a native legacy test runner.

## Measurement boundaries

- Cold Welcome has one fresh `am start -W` sample. Its accessibility/notice
  observer is separate, includes overhead, and is not first-frame timing.
- Source-save to first confirmed Cards is an upper bound including import,
  normal mode selection and host hierarchy queries. It is not isolated renderer
  latency or a decoder-ready declaration.
- Three warm-return samples have nearest-rank p50/p95. With only three samples,
  p95 is the maximum observed sample, not a stable population percentile.
- Public card IDs/bounds/selection/focus are state hints. No private absolute
  scroll offset or offscreen selected-card assertion is inferred. Differences
  remain recorded instead of being normalized away.
- Raw HWUI framestats are captured before scrolling and after every swipe. The
  summary deduplicates newly observed complete frames and uses Android's own
  deadline/interval fields when available. Rolling buffers can omit frames; no
  profiler counter, app data or cache is reset. These records do not measure
  complete FPS, video-decoder frames or physical Fold jank.
- PSS/RSS and CPU are finite process snapshots with raw averaging context. They
  cannot establish absence of leaks, battery or thermal improvements.

Display configuration and Power Saving values are recorded without changing
them. No fixed 60/90/120Hz assumption, data wipe, private-data injection, native
library change, new background service, application shutdown or release promotion
is part of this harness.

## Immediate current-root observer preparation

The two previous signed431 attempts are retained under results/signed431-baseline and results/signed431-baseline-observer-fixed. The latter proved source import/Mobile rendering but the stock dump command repeatedly failed its idle gate before Cards entry. No Cards performance baseline was established.

The selected follow-up QA implementation uses the existing Android17 public shell wrapper and platform Dumper through a standalone reflected main, without waitForIdle/JUnit/runtest. It does not change app bytes or timers. Build only the QA JAR with:

```sh
python3 repairs/cobra-next-from-2103427/cards-from-2103431/android-qa/immediate-observer/build.py --android observer-tools/receipt-evidence/android-34.jar --d8 "$ANDROID_HOME/build-tools/35.0.0/lib/d8.jar" --out runtime-observer
```

Both tool hashes are pinned. Only the single QA class is compiled/bundled. Before any Cards input, the host pushes and hashes that exact JAR, and a fail-closed device preflight records the actual OS script/JAR hashes, application classpath and reflected public method surface. BOOTCLASSPATH is inherited unchanged. Unsupported APIs are an exact blocker; no permission/classpath workaround or replacement app is allowed.

Every current-root capture records native monotonic metadata, root package/window/bounds, XML hash and post-dump active-window validation. Actions require the latest target within clipped root/display bounds and a conservative age under3.5seconds from observer start. Known-notice captures can admit only the Android root in addition to Cobra; the original exact notice/native-member checks still gate its sole OK press. Only explicit null/changed roots can consume the existing finite15/10 observation loops; input/action paths remain strict. All raw diagnostics and independent terminal screenshot are retained.

Preparation has20 selected mocked-ADB host controls passing, plus pinned compilation/class/source binding and workflow contracts. Actual API37 immediate-observer execution is not yet run; root review is required before a third CI dispatch. See immediate-observer/RESULT.json. These host controls establish neither Android acceptance nor Fold performance.
