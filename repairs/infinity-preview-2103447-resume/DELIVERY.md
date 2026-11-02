# Infinity Preview 2103448 — resume memory testing candidate

Delivered one original-key signed combined APK. This adds per-video Resume / Start Over to the exact signed 2103447 Preview, preserving its existing dark UI, horizontal controls, seekbar and playback engine. The separately approved cinematic Light/Dark design remains unchanged and unimplemented. No new release lock or acceptance promotion was made.

## Downloads and source

- [Signed APK archive](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41442869656/artifacts/13140468029) — extract `Infinity-2103448-Combined-Original-Signer.apk`.
- [Exact matching component ZIPs](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41442869656/artifacts/13140233242) — includes INFINITY, COBRA, CHOOSER_SHELL, MINIMAL_ANDROID_CONTRACT, catalog and SHA256SUMS.
- [Successful original-key signing run](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41442869656).
- Signed source: [`ecfbfdd00c443bad530d3ed429eb69755f46601f`](https://github.com/mahfouzhassine8-ops/project-infinity/commit/ecfbfdd00c443bad530d3ed429eb69755f46601f).
- Component preparation: [run 41442339036](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41442339036), source `14c3997da7e7fb1938f60decfe57d8b9d2e16dc5`. Release registration changes authority metadata only; compiled production bytes match the Android-tested owner.

Package `com.projectinfinity.kodi`; versionCode **2103448**; inherited versionName `1.0.9-Final-Corrections-TEST0011`; APK 778,583,809 bytes. Same package and original signer with a higher versionCode support installation over 2103447 without uninstall or data clearing. Installation on the user's device remains pending.

APK SHA256: `2c20613f9056e84fea402cf67729939a205b7d9afb87ec1b6fab800a641efbd3`.

Original certificate SHA256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`. Independently verified baseline and candidate with apksigner: one original signer, RSA4096, v1/v2/v3 valid. Signed artifact digest: `6776f9d6dfeb5455929a07197aa1d9860208a76f6bacf762fe46259e999bca42`; component artifact digest: `84bbc5e6b9268088bcc623e651e053e3fa88a293b5b98d83c68530da2684e244`. Both downloaded archives passed SHA256 and ZIP CRC checks.

| Component | SHA256 |
|---|---|
| `CHOOSER_SHELL.zip` | `d367b4fa024c7de897d67352e87028877b7e2b9b2f8a61713e29b631643aa302` |
| `COBRA.zip` | `f63d4c1e491dc94591c5623bf02be90d4f9c187b91a0511b36398ee96745f8a8` |
| `INFINITY.zip` | `50c2ed899113c63511422b0a1db85dc458e0701d8d05f7d1036001aed190ae25` |
| `MINIMAL_ANDROID_CONTRACT.zip` | `1c4a2890ef5ca8665b86b148dd293c06a56d76ec846de1e0c9c037a3b0151a25` |

## Implemented and verified

Private Preview SQLite history records each seekable video's millisecond position, with lifecycle checkpoints and periodic saves on the existing decoder worker. A prepared video offers native Resume / Start Over; playback waits for the chosen seek. Generation checks reject stale requests and choices. Start Over clears that video's aliases; last 30 seconds or 95% completion resets progress. Less than 30 seconds of progress and live/nonseekable media start normally.

- **15 host checks pass:** 12 storage checks plus 3 scheduling/provider boundary checks. Two reproduced boundary problems were fixed before release: zero-valued UI restoration must not override committed progress, and arbitrary non-document providers must not acquire SAF document identity semantics.
- **Actual Android API37.1 decoding/input:** independent A/B/A/B positions; real Resume and Start Over presses; Pause/Stop/Close/Back and source return; background and periodic saves; registered SAF plain/tree and same-granted-file aliases; private Preview process loss/restart; emulator reboot persistence.
- **Remaining Android segment PASS:** [run 41440829875](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/41440829875), same tested production DEX. 1080x2520, 1600x1680 and 2520x1080 viewports; both Android system theme settings; seekbar and horizontal-strip/Display input; rapid A/B/C; near-end reset; denied and malformed source errors; decoder release and no unintended Kodi process.
- **6 release-protection checks pass**, followed by the trusted source, owner, original-signature, package, exact-member and published-component gates.

The core evidence comes from completed checkpoints in run 41436653854; its later test-observation failure remains recorded as FAIL. The successful remaining run closes the unfinished checks, with exact source/DEX binding. No failed workflow was relabeled PASS. Intermediate harness failures and their evidence are retained under `runtime-attempts/`. No shutdown suite was run.

## Exact preservation

[Published verification](delivery-evidence/PUBLISHED-VERIFICATION.json) and [all payload member hashes](delivery-evidence/ALL-APK-MEMBERS.json) compare the downloaded signed APK directly with exact signed 2103447. **7,611 payload members and all 47 native libraries are unchanged.** Cobra and shared component ZIPs are byte-identical. Splash/routing DEX, chooser code/appearance, launcher resources, Kodi/add-ons/skin and protected shutdown remain unchanged. In the Infinity owner, 587 unrelated classes are identical; only the Preview engine/activity families and new resume helper differ.

Every changed APK member:

| Member | Authorized change |
|---|---|
| `classes3.dex` | Preview resume implementation only; exact Android-tested SHA256 `001cb13a340c513fbd05fb955532716e1902c012fee6e86bdce5e58eaebc9eb4` |
| `AndroidManifest.xml` | versionCode 2103447 → 2103448 only; normalized manifest otherwise identical |
| `assets/experience-component-updates.properties` | Infinity 2103448; Cobra remains 2103445 |
| `META-INF/INFINITY.RSA` | Original-key regenerated signature |
| `META-INF/INFINITY.SF` | Updated signed digests |
| `META-INF/MANIFEST.MF` | Updated member digests |

The APK signing block also changes for the newly signed bytes; it is not a ZIP member. There are no added or removed payload members. All published component members and DEX parts match the signed APK; the shared component manifest differs only in the assembler-owned versionCode normalization. See [component proof](delivery-evidence/PUBLISHED-COMPONENT-MATCH.json).

Production source: `InfinityExternalEngine.java`, `InfinityExternalPlayerActivity.java`, and new `InfinityExternalResume.java` under `repairs/infinity-2103445-standalone-external-player/runtime/`. The entire pre-existing UI/control-construction suffix and specified playback operations match baseline source. Supporting changes are scoped tests, evidence, owner registration and the existing guarded release workflow. No existing user database is read, reset or migrated.

## Physical acceptance and limitations

Use [the focused Fold checklist](FOLD-ACCEPTANCE.md). Genuine Fold/unfold, hardware rotation, screen-off/interruption behavior, authenticated cloud providers and the user's actual file-manager apps still need physical acceptance. Emulator viewport checks are not physical Fold tests. Existing unrelated playback-control tests are reused where their source is unchanged.

Stable document identity or the same permitted backing file can share progress across callers. Unrelated cloud/local copies, opaque identities and changed signed URLs cannot safely be merged by name. History retains up to 1,000 recent videos and 4,000 aliases. Abrupt process/power loss can lose the last roughly 10-second checkpoint interval; actual seeking is limited by Android and the media format. The core fixture restored saved positions within one displayed second; this is not a universal codec accuracy guarantee.

Signed 2103447 and its lock remain untouched. **2103448 is a testing candidate, not accepted or locked.**
