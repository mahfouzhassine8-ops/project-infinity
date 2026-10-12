# Cobra six-change test candidate 2103370

This candidate is not locked, promoted, or physically verified. Galaxy Fold acceptance belongs to the user.

The retained transport is exact 2103369 from source `9abf7c84fbd8224958bc8465c983429bc5976074`, run 38188883754. Its 24 Cobra-owned Java sources are byte-identical to the latest user-approved Cobra component 2103324 from source `9f621f34e3ded845e1c3e9c2a49d98158b6e31b3`, locked by `25497c4dfd6be8d83f32580495b16afb6eaed736`. These are distinct component and transport identities. The candidate is built on 2103369, not an older transport.

## Product scope

| Authorized change | Boundary |
| --- | --- |
| Mute and logical volume preservation during channel replacement | Cobra fullscreen retunes only; existing focus/call policy remains authoritative |
| PiP controls and originating mini/fullscreen return | Cobra-wide explicit controls; same existing player/session and PiP engine |
| Channels, Display, Multi-View, PiP, Status, More scroll rail | Pro fullscreen only |
| Verified home/away, venue/location, time/state, score/progress and available team stats | Pro Status only; existing sports repository; spoiler/freshness rules preserved |
| One active broadcast-choice layer and rejected obsolete async results | Pro fullscreen Sports only |
| Palette and glass compatibility in Pro heading | Pro header only |

Only `InfinityLiveActivity.java.in` and `CobraProUi.java.in` change at runtime. Source token guards preserve every other method/token, with a closed list of modified owners. All other 262 Android source files, native libraries, assets, resources and non-Cobra compiled behavior must remain identical to 2103369. The native engine is not rebuilt or retagged. The known startup-Close condition remains deferred for Astra.

`changes.patch` is applied with zero fuzz to the exact associated 264-file CI source export. Baseline and reviewed result hashes are checked before compilation. No product source is reconstructed from screenshots or older variants.

The mini PiP control is a 48dp addition above the existing player controls; the six existing controls keep their order, callback mapping and sizing. Pro owns its existing scroll strip with PiP and Status additions. The existing Pro game information action expands to Game Status for upcoming events as well as live games. The expanded mini Status keeps the prior detailed statistics and leaders presentation reachable; Sports hub Stats remains unchanged.

## Verification

The pipeline runs 41 new real Android/Robolectric contracts plus the ten inherited Cobra suites (167 existing checks). Two copied regression files update expectations only for the approved extra buttons and expanded Pro game information sheet; their prior behavioral checks remain. The exact inherited obsolete Pro drawer-destination exclusion remains documented; no new tests are skipped.

Nine host checks exercise negative source preservation, pinned baseline identity and exact DEX encoding/control-flow equivalence. Packaging compares every protected ZIP entry, resources, manifest (except candidate version), permanent signer, JNI declarations, and exact unaffected compiled instructions. Stateless D8 API helper relocation is resolved by exact method bodies, never blanket-exempted.

The repository branch and successful CI artifact are evidence of source/automated acceptance only. They do not establish actual Android PiP, decoder/audio routing, Galaxy Fold appearance or physical acceptance.

## Installation and acceptance

Install the signed candidate over 2103369 using the same `com.projectinfinity.kodi` identity. Do not uninstall, clear storage or replace profiles/add-ons. If Android reports a signing/version/install error, stop and retain its exact message; do not bypass it.

Keep the exact 2103369 APK and exported user settings as rollback references. Android normally refuses installation of a lower version code over 2103370; a non-destructive downgrade needs a separately reviewed supported method. Do not uninstall or clear data to force rollback.

On the Fold, test all five modes (Normal/mobile, TV Grid/grid, Compact, Cards, Pro/focus), both audio states through channel selection and previous/next/last, PiP from mini and fullscreen, native expansion and launcher return, pause, refusal/disabled PiP, Back/Close and interrupted transitions. In Pro, compare the six-control rail and Game Status against the approved image, live/upcoming/unavailable/non-sports fields and spoiler protection, Sports broadcast switching, and header appearance in Dark/Light/OLED/System/Ambient and Night Cinema transitions. Confirm multi-window, existing playback, scaling/Fill, rewind, subtitles, channel menus, Multi-View, account settings and protected Infinity features remain intact. Record any failure explicitly. Do not lock before user acceptance.
