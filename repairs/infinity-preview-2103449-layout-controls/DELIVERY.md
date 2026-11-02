# Infinity Preview 2103450 — responsive layout and control polish

One original-key signed testing APK contains the three selected Preview changes
and requested seek-icon polish. Signed 448 remains the user-selected recovery
base; signed 449 remains retained. **450 is not accepted, promoted or locked.**

## Downloads

- [Signed APK archive](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41541654995/artifacts/13186062986): extract `Infinity-2103450-Combined-Original-Signer.apk`.
- [Exact matching component ZIPs](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41541654995/artifacts/13185429405), including catalog and SHA256SUMS.
- [Successful original-key signing run](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41541654995).
- Signed source: [`f372d25e5e3b23634895ef2e9c9ed60e5246d123`](https://github.com/mahfouzhassine8-ops/project-infinity/commit/f372d25e5e3b23634895ef2e9c9ed60e5246d123).
- [Verified preparation](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41540911894), source `07c33e67eb31ff1d586257bd3c7c959a18c73c2e`. Registration changes release metadata only; the production DEX matches Android verification.

Package `com.projectinfinity.kodi`; versionCode **2103450**; APK **778,592,001
bytes**. Inherited versionName `1.0.9-Final-Corrections-TEST0011` is unchanged.
The higher versionCode and original certificate support installation over 448
or 449 without uninstalling or clearing data. Physical installation is pending.

APK SHA256: `01cb1b35ded45ca4124a1e0feed5029554fee51ca0f14c1b3d72bf9e50460161`.

Original certificate SHA256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
Independent verification confirms one original RSA4096 signer and valid v1/v2/v3
signatures. Signed artifact SHA256:
`c2631df3b5adf2008a0fbde566913aa0670a993b171c59fc71f0aa00a93e391c`.
Component artifact SHA256:
`3e10918eb45e6b8eb5740535254c90b8e57826d10481b4cf8d10280547a770d0`.
Both downloaded archives passed their GitHub SHA256 and ZIP CRC checks.

| Component | SHA256 |
|---|---|
| INFINITY.zip | `c6edb142b15967ee2870fda1f85503eef5d65782601deb95bbe07cb16d55101f` |
| COBRA.zip | `f63d4c1e491dc94591c5623bf02be90d4f9c187b91a0511b36398ee96745f8a8` |
| CHOOSER_SHELL.zip | `90a5e50a85b28b51a4604f6c6d5e75003832d0d3511e7284afd9a2a29cc0efad` |
| MINIMAL_ANDROID_CONTRACT.zip | `1c4a2890ef5ca8665b86b148dd293c06a56d76ec846de1e0c9c037a3b0151a25` |

## Changes and checks

- Best Fit uses actual media proportions and the available viewport. Timeline
  and toolbar stay adjacent to the video. The existing tap-to-hide action frees
  the reserved space for unobstructed video; showing controls restores the group.
  Fill remains explicit cropping. No stretching or fabricated image is added.
- Auto rotation has persistent cyan selection; Locked clears Auto selection and
  retains its caption and accessibility state. Rotation policy is unchanged.
- The duplicate Volume button/dialog is removed as requested. The existing
  inline slider beside Audio remains the sole volume-level control.
- The ±10s glyphs are matched, mirrored round arrows. Their original seek
  callbacks remain unchanged.

**10 focused host tests PASS**, using the production Activity, actual View input
and native Canvas, with a decoder terminal spy. **6 release-protection tests
PASS**, followed by the original source/owner/signature/package/member gates.

[Android remaining checks PASS](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41539406515): real decoding; real rotation taps and selected state; no duplicate Volume; actual private player volume of 0.35 through the inline slider; Light/Dark at 1080x2520,1600x1680,2520x1080 and1080x960 with measured non-overlap; video-tap hide/show; actual portrait and square decoding/proportions; source return, decoder release and no unintended Kodi launch. Actual app renders were visually inspected. [Render evidence](final-evidence/) uses synthetic video content.

Both real ten-second seeks completed in run 41538194686 on the same production
DEX. That workflow remains FAIL: the old QA observer did not export selected
state. The observer was corrected without production changes; completed seek
evidence is reused. The first attempt failed during SDK installation before app
execution. All failure evidence remains recorded; no failed workflow became PASS.
The [combined evidence](final-evidence/ANDROID-RESULT.json) binds exact source,
artifact and DEX bytes. No shutdown test was run.

Existing 449 resume-storage, call/audio and other control evidence is reused only
where source and complete class definitions remain exact. No new physical call
audibility or Fold acceptance result is claimed.

## Preservation

[Independent published comparison](delivery-evidence/PUBLISHED-VERIFICATION.json)
and [all payload hashes](delivery-evidence/ALL-APK-MEMBERS.json) compare actual
downloaded signed 450 with signed 449. **7,611 payload members and all 47 native
libraries are byte-identical.** Cobra and shared component ZIPs are byte-identical.
Splash/routing DEX, chooser code, launcher assets, Kodi/add-ons/skin, native/shared
and shutdown are unchanged. The [transitive comparison](delivery-evidence/PROTECTED448-TRANSITIVE-PRESERVATION.json)
also confirms every unrelated payload member remains identical to signed 448.

Only `InfinityExternalPlayerActivity.java` and `InfinityPreviewChrome.java`
change in production. The source guard permits four Activity methods and the
Control drawing only. **637 complete class definitions are unchanged** from 449;
the two obsolete duplicate-Volume handlers are removed. Decoder, resume store,
request state, call/focus handling and lifecycle remain exact. DEX index offsets
are not claimed unchanged. User data was not accessed, reset or migrated.

Every changed APK ZIP member:

| Member | Authorized difference |
|---|---|
| classes3.dex | Selected Preview changes; Android-tested SHA256 `6692252f1c8b6c6c18b9d1e60af2a4c1ab3624214f3a9123cfb724686b0ef8f2` |
| AndroidManifest.xml | versionCode 2103449 → 2103450 only; normalized manifest otherwise exact |
| assets/experience-component-updates.properties | Infinity 2103450; Cobra remains 2103445 |
| META-INF/INFINITY.RSA | Original-key signature regenerated |
| META-INF/INFINITY.SF | Signed digests updated |
| META-INF/MANIFEST.MF | Member digests updated |

The APK signing block also changes and is not a ZIP member. No payload member
was added or removed. [All published component payloads and DEX parts match the
signed APK](delivery-evidence/PUBLISHED-COMPONENT-MATCH.json); only the established
assembler-owned manifest versionCode normalization applies to the shared bundle.

## Physical acceptance

Use the [Fold checklist](FOLD-ACCEPTANCE.md). Genuine fold/unfold, hardware
rotation, Samsung call-audio policy and final visual acceptance remain physical
checks. Emulator viewport changes are not physical Fold tests. A wide clip cannot
fill a tall portrait display without cropping or distortion: Best Fit preserves
the full picture, while Fill is the user's explicit crop choice. Existing codec
seeking, resume-identity and background behavior retain their prior limits.

**450 is a testing candidate. Only the user can accept and lock it.**
