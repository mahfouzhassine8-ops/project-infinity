# Infinity Preview 2103449 — cinematic controls and call playback

One original-key signed testing APK is delivered over the exact signed 2103448
base selected by the user. Preview now has the cinematic Light/Dark presentation
and continues video muted during an active call, with explicitly requested manual
Unmute. Resume memory and existing playback controls are retained. This candidate
is not accepted, locked or promoted.

## Downloads and identity

- [Signed APK archive](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41478361487/artifacts/13159480694): extract `Infinity-2103449-Combined-Original-Signer.apk`.
- [Exact matching component ZIPs](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41478361487/artifacts/13159955000), including catalog and SHA256SUMS.
- [Successful original-key signing run](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41478361487).
- Signed source: [`dd7bd790e7adc3cfadccb9743c9b38b49e8e7b11`](https://github.com/mahfouzhassine8-ops/project-infinity/commit/dd7bd790e7adc3cfadccb9743c9b38b49e8e7b11).
- [Component preparation](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41477597164), source `26b7aeeab627401fe62c502607fa70c7a5549167`. Registration changes release metadata only; the signed DEX matches the actual Android-tested DEX.

Package `com.projectinfinity.kodi`; versionCode **2103449**; inherited versionName
`1.0.9-Final-Corrections-TEST0011`; APK **778,592,001 bytes**. The same package and
original certificate, with a higher versionCode, support installation over 448
without uninstalling or clearing data. The user's installation remains pending.

APK SHA256: `e190c17b3f337133df66e5531d4983e48ce3544c90965db6911936f0db65ec5c`.

Original certificate SHA256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
Independent apksigner verification of downloaded baseline and candidate confirms
one original RSA4096 signer and valid v1/v2/v3 signatures. Signed artifact SHA256:
`008f090e50f9c09dd53f96ce25fb9286261f6aebaac7890a308f6de5cfacac04`.
Component artifact SHA256:
`13aa2ce18e69ba62130c9a5e8ca9c73b2123319e574ca06dd5a83dfa90852e46`.
Both downloaded archives passed their GitHub digest and ZIP CRC checks.

| Component | SHA256 |
|---|---|
| INFINITY.zip | `54628c456a3d1fa587ae108a9dbabc46563d0d45bc518894305bcc42766971a9` |
| COBRA.zip | `f63d4c1e491dc94591c5623bf02be90d4f9c187b91a0511b36398ee96745f8a8` |
| CHOOSER_SHELL.zip | `862c0c2363d47bcb5b6f897e2378a933ae934f9732f8d9e1de4d4670f4b6c571` |
| MINIMAL_ANDROID_CONTRACT.zip | `1c4a2890ef5ca8665b86b148dd293c06a56d76ec846de1e0c9c037a3b0151a25` |

## Implementation and verification

Production changes are limited to `InfinityExternalPlayerActivity.java` and new
`InfinityPreviewChrome.java` under
`repairs/infinity-2103445-standalone-external-player/runtime/`. They provide the
glass header, framed video, independent timeline, native horizontal icon controls,
private System/Light/Dark appearance and call-aware temporary mute. Manual Unmute
changes only Preview's own player volume. Normal non-call audio-focus behavior,
user Pause and background pause remain authoritative. No telephony permission,
new service, device-volume change, decoder replacement or database migration.

- **8 focused host tests PASS:** actual Activity/View input and Canvas rendering,
  call/focus policy, user pause, background callback cleanup and density changes.
  Host decoding uses a terminal spy and is not Android playback evidence.
- **Actual Android API 37.1 emulator:** real decoding and advancing clock;
  Pause/Play, seek and skips, Mute, Audio, rendered subtitles, Best Fit/Fill,
  rotation, original Volume dialog, video-tap controls, Resume/Start Over, rapid
  replacement, error/retry, horizontal scrolling and measured layout checks.
  Light/Dark rendered at cover, inner, landscape and short-window sizes, plus
  System theme switching. Actual renders were visually reviewed.
- **Call and cleanup PASS in [run 41475018882](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41475018882):** Android reported `MODE_IN_CALL`; video advanced with player volume 0.0, then 1.0 after a real Unmute tap. OS media-player dumps confirm the same player connection. Video continued after the call ended; Back returned to the source application and released the decoder. Kodi did not start.
- **6 release-protection checks PASS**, followed by original owner/source,
  manifest, signature and published component-preservation gates.

Completed UI evidence from run 41471747914 is reused with identical final DEX.
That full workflow remains **FAIL**: its later call setup expected a Resume prompt
below the unchanged 30-second resume threshold. The successful call-only run
closes those remaining checks. Earlier test-observation failures remain recorded;
none was relabeled PASS. Existing 448 resume-storage/process/reboot evidence is
reused only because the complete Engine and Resume class definitions and sources
are unchanged. No shutdown test was run.

## Exact preservation

[Independent published comparison](delivery-evidence/PUBLISHED-VERIFICATION.json)
and [all payload hashes](delivery-evidence/ALL-APK-MEMBERS.json) compare the actual
downloaded signed 449 APK with exact signed 448. **7,611 payload members and all
47 native libraries are byte-identical.** Cobra and shared component ZIPs are
byte-identical. Splash/routing and chooser DEX, Kodi/add-ons/skin, launcher assets,
shared runtime and shutdown payload are unchanged. In the rebuilt Infinity DEX,
615 unrelated complete class definitions remain identical; DEX index offsets are
not claimed to remain identical.

Every changed ZIP member is listed below; no payload members were added or removed.

| Member | Authorized difference |
|---|---|
| classes3.dex | Preview Activity/helper only; Android-tested SHA256 `a8ce31bebd92e4ad096b8d54e3f9442ecd55b85197f56edf9ef6bf2b87c50387` |
| AndroidManifest.xml | versionCode 2103448 → 2103449 only; otherwise normalized identity exact |
| assets/experience-component-updates.properties | Infinity 2103449; Cobra remains 2103445 |
| META-INF/INFINITY.RSA | Original-key signature regenerated |
| META-INF/INFINITY.SF | Signed digests updated |
| META-INF/MANIFEST.MF | Member digests updated |

The APK signing block also changes and is not a ZIP member. [Every published
component payload and DEX](delivery-evidence/PUBLISHED-COMPONENT-MATCH.json) matches
the signed APK; the assembler's manifest versionCode normalization is the only
shared manifest exception. No user data was accessed, cleared or migrated.
Protected signed 448 and the existing lock references remain intact.

## Physical acceptance and limits

Use the [focused Fold checklist](FOLD-ACCEPTANCE.md). Samsung/carrier/VoIP policy
may enforce silence despite manual Unmute; the emulator proves player volume and
continuing video, not physical call audibility. Genuine Fold transitions,
incoming-call behavior and final visual acceptance remain device checks.

The actual inline reference was inspected and compared with actual app renders.
Raw reference PNG bytes were unavailable, so no automated pixel-equality claim
is made. Media, title, elapsed time and viewport proportions are dynamic. Light
uses the protected design's palette and the same geometry. The design-lock
document remains unchanged.

Signed 448's paused position ticker behavior remains: ordinary seeks publish the
next clock update after playback resumes. Resume identity, completion thresholds,
codec seeking precision and background behavior retain their existing limits.
**2103449 is a testing candidate; only the user can accept and lock it.**
