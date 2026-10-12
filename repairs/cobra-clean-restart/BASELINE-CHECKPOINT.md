# Cobra clean restart — baseline checkpoint

Date: 2026-10-12.

**Status: artifact identity and Cobra source equality verified. Six-change implementation NOT completed. No runtime test rerun, candidate packaging, new signing, release lock, or production promotion occurred in this checkpoint.**

## Source of requirements

The user's uploaded `COBRA — ASTRA PRO CORRECTIVE IMPLEMENTATION HANDOFF / Restart From Approved Cobra Baseline — Six Changes Only` is authoritative. This is a fresh branch, not continuation of the earlier failed corrective implementation. The current checkpoint changes documentation only.

- Repository: `mahfouzhassine8-ops/project-infinity`.
- Fresh branch: `work/cobra-clean-restart-20261012`.
- Initial branch commit: `9abf7c84fbd8224958bc8465c983429bc5976074`, retained 2103369 transport.
- Approved Cobra source: `9f621f34e3ded845e1c3e9c2a49d98158b6e31b3`, 2103324.
- Approval lock: `25497c4dfd6be8d83f32580495b16afb6eaed736`.
- Rejected 2103370 implementation: not imported, cherry-picked, or used as the new branch parent.
- Earlier corrective branch `work/cobra-astra-corrective-20261012` at `1007195a34ca79045703cd8b620d74a6ee38efca`: left unchanged; its implementation is not the new parent.

## Independently executed artifact checks

Both original APK artifacts and both original source-evidence artifacts were downloaded via the GitHub connector. The APK ZIP archives passed CRC checks. SHA-256 was computed over the APK bytes, not inferred from filenames or earlier reports.

| Artifact | Verified value |
|---|---|
| 2103324 APK artifact | `11463970585`, original run `37578532123` |
| 2103324 APK SHA-256 | `5af58f2e700e636cdc798cbde0acc89e8091153cfcf1e17c792375fe285dd8c3` |
| 2103324 APK bytes | `157925831` |
| 2103324 evidence artifact | `11464155407` |
| 2103324 evidence ZIP SHA-256 | `a2adff818f331bd7ee49750b3435b0bb056d4b88e70db423a8e952f1a1a980b4` |
| 2103324 repaired-shell-source.tar.gz SHA-256 | `f2507e3e1f131ed448e381bb0c876cd0816c7d4cadc0f00440ef29cb7993b1e5` |
| 2103369 APK artifact | `11721786639`, original run `38188883754` |
| 2103369 APK SHA-256 | `83128afbd2595dbf4053ded40ee1d22ae0d1c7b798f62dd9f077bd4d729261f4` |
| 2103369 evidence artifact | `11721467881` |
| 2103369 evidence ZIP SHA-256 | `79c32db03dccbeb3b2d1020e9dd4da5c7ca26483b1dd40a5529837901eea7885` |
| 2103369 runtime-shell-source.tar.gz SHA-256 | `b3d70a863adbe350141729989bfe78279514f0870e55107d15bf15dc1e766597` |
| Extracted APK v2 signer certificate SHA-256, both APKs | `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7` |
| Retained 2103369 lib/arm64-v8a/libkodi.so SHA-256 | `5d42d0d8ef6a90a5678fd7a24cc4e3b01e2375c213c590a92c178d7a34cc1113` |

The embedded v2 certificate was extracted and hashed directly. Full APK signature cryptographic verification was not rerun, and certificate equality is not described as such a verification. The exact original APK hashes match the recorded artifacts.

## Independent source comparison

The 2103324 source archive contains 254 files. Of those, 243 are byte-identical in the retained 2103369 source archive; 11 differ, and 2103369 adds 10 files. All 24 named Cobra-owned runtime source files are byte-identical. This confirms the presence of the original Cobra source within the retained transport; it does not, by itself, certify every runtime interaction with that transport.

Shared SHA-256 values for the Cobra-owned files below are relative to `tools/android/packaging/xbmc/src/`:

```
0d66b91d8a06830fea1c541a916e7bf9045160b362226efb3f0ee56856dd8055  CobraDiagnosticArchive.java.in
4d505bcb698b02a47f39f3cdef3fb3e3bda495f3d5562c90d3adde5a200d090f  CobraEmbeddedCrop.java.in
22404bb3d0531d16e826a49962fa0045a9932ff843de9e6b236d8c460bb2de07  CobraEmblem.java.in
9210eb5b7aba775a1aa223014209fd728cf7fabe4e9df2d422d2a97d3b98c5bf  CobraImmersiveAmbient.java.in
763c74a60f92710e16d15ebe218638cecf7615e4d44d7fc38b443f20091f4f46  CobraNetworkIntelligence.java.in
5dfdd9016fc0c46354953bbfc5e1dc402de9cef14e78ca80e8223f881756e9e4  CobraPresentationEffects.java.in
02957b1257e2a7e3589bcfeda050404e8e6d631a3cb7acb88e8671523aa295ec  CobraPresentationSafety.java.in
68b5eee8a3783594cbb8da86474279b34e9181b65530e30e6bede1bf809b4ec3  CobraProUi.java.in
40f4786003d2e53ca3ed1c4ace7d2d144cbea5eb49ae436acab7c88262387b17  CobraQuickPeekSession.java.in
7bf7dc411149bee5482f5390d986a9e375b3b6b28f02a1e35bf1d6e92855b8fb  CobraSmartReturn.java.in
5270ec1631dceab1bed9cf42203a9b8ddd06525d09362bb6b931087fbf60f46a  CobraSportsPreferences.java.in
89ac526756ba5133d8d3668244d0bb6a9926c3b3f26756edb97b4f8710679f71  CobraSportsReminderJob.java.in
d9411565610879ba810cb7e7a2d37026fa8519fac5204ae327aa3c11313ee7a0  CobraVisualCatalog.java.in
705c99eafc6c1d648167ab8689254dc8f330d69299eebf45a9c0637397c980da  CobraVisualGeometry.java.in
1ce2ec9bd3b29a32fc706619830d231b48ef5499f6e9f4c379a5a49350cdbebc  CobraVisualRenderer.java.in
9f315de2034de2eb262310e11054e62e42b37b3b0ebc9ae2c5edce97fd09b444  CobraVisualScene.java.in
dc5c8c05bbc559500689cd5a68c3128edf575b836e977fdd503959b7a27959fe  CobraVisualTheme.java.in
267fa7f6a8ccb529b3a3f8e70870a3e2a36282c06652e127c459cfbcef6e263a  InfinityCobraBootReceiver.java.in
58668d619eced74015e84a872d1a398af55a17d83df3e7a6dd32ca0ff5c995d4  InfinityCobraDeviceBridge.java.in
cfca77afbdd34ede8731143332dc81601c6e65800b252ecb6b167f6c4eaccc0b  InfinityCobraDiagnostics.java.in
7a07cef5fac3c82ee44cde3fd0310178baa40e59a54a150cc3ff116566819751  InfinityCobraFeatureRuntime.java.in
6c5e680dcb8c2b8a0e775db2eb37077b73ba93521558a6e198bc72dc9ee93567  InfinityCobraRecordingService.java.in
d3e058831dccae84c6a52a0ec03410e9dc7e4b0a6c69bb59d84a528bbcf7f7f7  InfinityCobraReminderReceiver.java.in
02111d4971307e5e0e0e9f22c319305e2924bc1942fa03f68b7b3a3a50f2f9ba  InfinityLiveActivity.java.in
```

Transport differences retained unchanged: `cmake/scripts/android/Install.cmake`, `AndroidManifest.xml.in`, `InfinityChooserWeather.java.in`, `InfinityExitCompletion.java.in`, `InfinityExitDiagnostics.java.in`, `InfinityGlassChooser.java.in`, `InfinityHealthExport.java.in`, `InfinityKodiShutdown.java.in`, `InfinityStartupHandoff.java.in`, `Main.java.in`, and `Splash.java.in`. All ten additional checkpoint/close/installed-code source files are also retained unchanged.

A complete 254-file comparison, all additional transport paths, both APK identities, and all 47 native-library hashes per APK are in the generated `BASELINE-IDENTITY.json`: 97,339 bytes; SHA-256 `b2bedc7044cf23681ec4251b0536e222315131bba478991c0e339b5d1fdf0bbb`.

## Six-change boundary

1. Cobra-wide: retain the previous user mute state only for tuning through fullscreen video UI > Channels, including available categories. Previous/Next, Last Channel, mini-player tuning, audio focus, calls, volume settings and background policy remain protected.
2. Cobra-wide: add working PiP controls to mini-player and fullscreen using the existing supported player/PiP system; preserve the originating experience and playback session.
3. Pro only: horizontal fullscreen controls with no direction arrows or new scroll instructions. Non-Sports retains original controls/order with PiP as the only addition.
4. Pro Sports only: `Channels > Display > Multi-View > PiP > Stats > More`; exact existing mini-player Stats icon; supported home-game details in both mini/fullscreen Stats; existing statistics/leaders, spoiler settings and freshness retained. No invented data or Status/Health Center substitute.
5. Pro Sports fullscreen only: visible, selectable channel chooser above the Sports panel; four complete choices when available; vertical scrolling beyond four; original matching, navigation and Back/Close preserved.
6. Pro only: existing header theme compatibility, without changing its placement/functionality, other modes, ambient engine or video.

## Earlier failure evidence — historical, not a new test run

The untouched earlier corrective branch records run `38206152159` on source `0c18474b13650f17740869c1156a2d885e7c713e`: 196/199 cases passed, including all 167 inherited cases. Three failures remained: preview PiP overlap at the actual 280x280 size, Activity recreation encountering an absent recreated Robolectric ViewRoot, and the Groups fixture failing to expose a different visible channel. These are required verification targets, not permissions to weaken tests or move original controls. They were read from the saved run report; this checkpoint did not independently rerun them.

## Remaining gates — explicitly uncompleted

- Independently verify original runtime behavior and the retained transport's relevant interactions; source equality alone is insufficient.
- Implement and inventory the six authorized changes on this fresh branch. Current changed-runtime-file and changed-runtime-method inventories are empty.
- Explain 2103370 leakage using source/view/lifecycle evidence, without importing its UI/player modifications.
- Run actual layout/control and functional tests for Mobile, Compact, Cards, TV Grid, Pro non-Sports and Pro Sports, including Back, PiP return, recreation, theme transitions and the exact tuning routes.
- Clear all failures and preservation gates before packaging. No new candidate version is assigned here.
- Verify candidate payload preservation, signing identity and hash only after a candidate exists.
- Physical Fold acceptance, release lock and promotion require the user's subsequent approval.

No product source was changed in this checkpoint. No new candidate APK was produced. The previous branch, approved rollback artifacts, native engine, Command Center, shutdown repairs, Cobra TV/onn builds and unrelated Infinity components were not modified.
