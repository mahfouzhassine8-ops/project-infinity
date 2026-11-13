# Infinity Cast QA 2103494 and forward recovery 2103495

This pair starts directly from the exact signed **2103492** APK, SHA-256 `3a3c08d5d168d040a34562d6a033f75b8680a242202afef965ac42fdd7383827`. It retains 2103490/2103492 Cast improvements. It is an internal functional QA candidate; actual Fold/TV acceptance remains pending. No accepted baseline is promoted.

| Artifact | Download | APK SHA-256 |
|---|---|---|
| Combined Cast QA **2103494** | [Signed APK artifact](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43347320164/artifacts/14001304481) | `fa0da5675443803ff2af42526243f81b9a1be774f7deeecdaf7e7557fff2a36c` |
| Forward recovery **2103495** | [Signed recovery artifact](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/43348342010/artifacts/14002702684) | `a92df7057d9937fb0d2c5aa56753e69ee66e7bcf9bdd3622975dc23c2370ed4d` |

The downloads are GitHub artifact ZIPs. Extract `Infinity-2103494-Combined-Original-Signer.apk` for the QA installation. The recovery ZIP contains `Infinity-2103495-Combined-Original-Signer.apk`; it restores exact **2103492 functionality** at a higher version, without an uninstall or data reset. It does not restore older 2103490/2103488/2103486 code. Historical artifacts remain unchanged.

Package: `com.projectinfinity.kodi`. Both APKs have one original RSA4096 signer and verified **v1/v2/v3** signatures. Certificate SHA-256:

`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`

Candidate signing source: `a8d732beec1272bd526741e2eb7dc009e2190c0b`. Recovery signing source: `828b3fde39351de19504d273afccbf02994e49fe`. Actual corrected Java was compiled and exercised by Android run **43345587052**, source `ba683a2eaa4b471ac5b5086315a31eedcc12f5cb`. All Java/build hashes are bound to the signed source. The original assembler and permanent-key workflow 397702717 are unchanged; no replacement signer is used.

## Confirmed corrections

- The actual relay lost the source's ordinary User-Agent/Accept on cross-origin redirects, reproducing HTTP403 with a controlled two-origin source. Preserve User-Agent, Accept and Accept-Language. Authorization, Cookie, X-headers, Referer and Origin remain restricted to the original origin. The receiver continues to receive only temporary local capabilities.
- The Cast clock worker could remain blocked in Unix `accept()` after listener `close()`. Android run43344651096 completed two retirements, then failed the third. The repair shuts down **only the owned listener** before closing it, serializes descriptor closure and closes an accept racing cancellation. Run43345587052 verified all five workers retired.
- The old controller announced session release despite native release refusal and before actual transport retirement. Cleanup now finishes only after relay retirement, clock retirement and a successful native release. Refusal retains ownership and permits explicit Disconnect retry. Phone restoration remains independent of transport draining.
- Cast Details supplies an 80-event RAM-only outcome summary: transfer stages, receiver error/status codes, HTTP status, delivered-body counters and retirement/release outcomes. No source URLs, credentials, cookies, titles or exception text are accepted. It creates no file, database or new diagnostic add-on.

These are executable source defects. **The exact cause of the owner's physical 2103492 receiver returning home remains unproven**: the supplied shutdown ZIP contains no Cast receiver or relay trace. This candidate includes functional corrections and safe outcome reporting; it does not claim the physical movie now plays without the owner test.

## Exact production changes

All five files reside in the existing Cast Java directory under `repairs/infinity-movies-continue-cast-2103486-20261112/cast/java/com/projectinfinity/kodi/`. That retained directory name is not the release base; exact signed2103492 is enforced by its APK and source hashes.

| File | Changed functions / purpose |
|---|---|
| InfinityCastRelay.java | `open`, `serve`, `delivered`, `closeWhenRetired`, `retired`: public header preservation, accurate delivery and retirement outcomes |
| InfinityCastChannel.java | `serve`, `close`, `closeWhenRetired`: owned Unix-socket cancellation and real clock-worker retirement |
| InfinityCastSession.java | `choose`, `returnToPhone`, `leaveReceiver`, `releaseNative`, `finishCleanup`, `onSessionEnded`: safe completion, retained ownership on failure and explicit retry |
| InfinityCastDiagnostics.java | `begin`, `event`, `summary`: bounded credential-safe outcomes |
| InfinityCastDialog.java | constructor, `applyColors`, `changed`: Cast Details inside the existing Cast controls |

No native source, engine binary, provider, Search, Movies, Infinity Movies, Continue Watching, TV, recorder, shutdown, Python startup, skin resource, database, settings schema or Cobra implementation changes. Cast entry-point locations are unchanged. Other changes are scoped tests, build routing, exact-baseline assertions, evidence and release metadata. Ownership metadata adds only generated Cast class root `w`; no existing owner is relabeled.

## APK preservation

Candidate: **7,772 unchanged payload members**, zero additions/removals. The only three payload changes are `classes6.dex`, typed `AndroidManifest.xml` versionCode, and `assets/experience-component-updates.properties`.

Recovery: **7,773 unchanged payload members**, zero additions/removals. Only those two version metadata members change; its Cast DEX is exact2103492.

The original five DEX members, all native libraries, resources, authenticated Command Center/skin/module files, provider files and Cobra members are identical. The only manifest change is versionCode. Cobra's component remains 2103445. APK signing regenerates the expected `META-INF/MANIFEST.MF`, `META-INF/INFINITY.SF`, `META-INF/INFINITY.RSA` entries and APK signing blocks; those are signature metadata, not payload changes.

`lib/arm64-v8a/libkodi.so` remains `3caccc96c23336e220b791118989f3a850b73fa8804267fb7beb2aad3b3afc75`. Existing full ARM64 compile/link evidence run43314732573 is reused because this exact binary is unchanged. There is no native rebuild or library replacement.

## Verification

| Check | Result / evidence |
|---|---|
| Production relay HTTP/ranges/privacy/cancellation | PASS,38 focused host checks |
| Authenticated HLS/DASH, FFmpeg decode and seeking | PASS,57 focused host checks |
| Real two-origin public headers, credential isolation | PASS; retained baseline HTTP403 failure |
| Actual controller handoff/cancellation/release contracts | PASS,15 retained cases +9 focused cleanup/privacy cases; deterministic SDK/native backends |
| Actual Android API36 component | PASS,43345587052: progressive/HLS/DASH/redirects, cookies, socket retirement, five clock workers and explicit ownership retention on JNI absence |
| Successful live Kodi JNI handback | NOT VERIFIED by the separate component package; it has no running Kodi engine. Refusal must retain ownership. Host success paths are not physical-device proof |
| Exact source / APK preservation and original signature | PASS, preparation43346220579, review43346995172/43348026091, signing43347320164/43348342010 |
| Actual signed92→94→95 PackageManager installation | PASS,43349020579; all three normal installations succeeded with stable UID/dataDir/firstInstallTime; no app launch, uninstall, reset or database access |
| Physical Fold/TV movie playback, controls, handback and post-Cast shutdown | OWNER ACCEPTANCE PENDING |

Historical failures remain in `ANDROID-HISTORY.json`. No failed test is rewritten as a pass. No shutdown test was run implicitly by feature or packaging verification.

## Supplied shutdown diagnostic and limitations

`Infinity-Diagnostics-20261112-195309.zip` was verified privately, SHA-256 `abac954dba12ee9325c24ce5e7b729921463161e5f2644e93cd2bae56b3f7500`. Raw logs and private database paths were not published.

It confirms a 25.227-second failed checkpoint, zero active native writers at its final snapshot, and unresolved TMDb Helper `ItemQueries.db` transaction/retirement proofs. Eleven deadline owner rows do not establish eleven active writers. A pending ambient-script entry is also present. The two 8 MiB native traces are truncated; an old cleanup receipt and a logical `live=false` flag do not prove current process death. These facts do not establish Cast caused the transaction, or that TMDb Helper is the underlying root cause.

**Shutdown, TMDb Helper, SQLite protections and deadlines are untouched. The recorded persistence blocker is not repaired or declared passing.** Post-Cast shutdown remains part of owner acceptance. DRM and receiver-incompatible media/codec limitations remain enforced; no DRM, credential or container validation is bypassed.

## One owner acceptance session

1. Download/extract the QA artifact and install **2103494** over the existing app. Do not uninstall, clear data or manually replace modules.
2. Play a streaming-provider movie locally; open the existing Cast control and select the TV. Confirm actual TV playback, position, seek and Pause/Resume.
3. Use Return to Phone / Disconnect, confirm local playback and Continue Watching. Close Controls only dismisses the dialog. Cast Details is available if a transfer fails.
4. Use normal Power→Exit once, then relaunch and verify the same profile/data. Acceptance remains the owner's decision.

Keep **2103495** available solely as forward recovery if needed. Installing it restores 2103492 functionality while preserving the package/data owner. Do not attempt a version downgrade or reinstall 94 over 95. No baseline is automatically promoted.
