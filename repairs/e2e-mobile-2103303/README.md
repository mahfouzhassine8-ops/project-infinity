# Infinity mobile repair — source checkpoint, not an APK release

This is an incomplete implementation of the October 3 end-to-end brief. No device
acceptance, native crash fix, skin repair, IME replacement, or completed lifecycle
repair is claimed. Do not install this source test harness as Infinity.

## Baseline and rollback

- App: `com.projectinfinity.kodi`, version code `2103302`,
  `1.0.9-Chooser-Weather-Snapshot-RC1`.
- Exact locked APK SHA-256:
  `bcd316d398925f2cdb01f4d1ce5030664ea9a4007598d7acf6440adb240b9b50`.
- Source baseline: `e0bd90006c71c605010172c919358f6939c91ae8`.
- Remote rollback branch:
  `rollback-infinity-2103302-before-e2e-repair-20261003`.
- Original successful package workflow: run `37146313126`, job `111270885273`.
- Exact native `libkodi.so` SHA-256:
  `b3f32d5c5a3c346b7c0b15e382d0b43e0d6e795edabadb9e6b4175209043cf61`.

The saved audit archive had stale hashes for two exit helpers. The original CI
source artifact was independently inspected by source-verification run
`37161396886`, job `111315402471`. Actual files match the source repository:

- InfinityExitCompletion.java.in:
  `b9260cd45309a6d8f8f78f31d1c1d4395380529ac448f54d70e30c0b480e790a`.
- InfinityPowerMenuRoutes.java.in:
  `0f364714ec7b85198b8888a372efc14fa244b60c11a3baf5fbddfff5329da74a`.

`baseline-source-sha256.json` records the verified source preimages. The patch
refuses a mismatching parent; it does not weaken the existing release gates.

## Implemented source changes

1. Remove the HM and both experience-card slogans in the locked Android mobile
   chooser. Use the exact subtitle `TWO UNIVERSES.`. Artwork, names, settings
   actions, routing, weather bridge and responsive layout remain inherited.
2. Separate chooser visible duration from the Kodi handoff clock. An eight-minute
   chooser wait no longer becomes an eight-minute Kodi startup. Repeated chooser
   composition after opening settings retains the first-frame timestamp.
   Unknown handoff time is explicitly `-1`. A closing native owner cancels that
   timing attempt; a new accepted selection starts another.
3. Identify a retained responsive trace as historical, with its own session/date.
   This does not repair native geometry telemetry or choose a responsive profile.
4. Export Health Center diagnostics as a ZIP on an explicit background worker.
   Store native tombstone bytes without UTF-8 conversion, include a timestamped
   exit manifest and retain ANR traces as separate entries. Limit collection to
   four attempts and 2 MiB per trace; flag truncation. Clipboard receives a bounded
   text summary without binary traces. Export failure is reported; unavailable
   traces are recorded rather than fabricated.

The raw export work is essential for the requested ownership investigation. It
does not symbolicate traces or prove a crash repair. Existing native diagnostic
collector metadata contains an old hardcoded engine hash; do not use that value
as proof of historical APK ownership.

## Evidence limits and required input

The supplied `Infinity-Diagnostics-20261003-184051.txt` contains three native exits
at approximately 13:50, 13:53 and 14:00 local time. They predate completion of the
2103302 CI build. The text exporter decoded protobuf as UTF-8, replacing invalid
bytes; those bytes cannot be reconstructed reliably from this TXT. Native frames
cross rendering/property refresh, but ownership remains unproven.

The report's `0x0` native geometry and fallback profile occur in a retained trace
dated October 1. They are not evidence of the current October 3 launch geometry.
The reported absence of Android ANRs does not establish the absence of UI freezes.

Remaining work needs the current installed Infinity skin and relevant add-on
source/configuration, plus original binary tombstones and exact build-ID-matched
symbols for each affected build. Available archives include skin 1.0.5.189 and a
1.0.5.190 candidate; this report does not establish which is actually installed.
No device/ADB connection is available in this workspace.

Useful reproducible findings for the continuation:

- `unified/Custom_1198_InfinityNav.xml` in the .190 candidate routes Movies/TV
  into generic `videodb://.../titles/`. The command-center add-on implements
  `plugin://script.infinity.commandcenter/?action=movies` and `?action=tv` hubs.
- `unified/Home.xml` sets default focus to hamburger `9090` and retains full-height
  rail artwork plus a 100-unit main content inset.
- Settings radio rows use a fixed `radioposx=520`; their available label space is
  not safely coupled to responsive width.
- The player XML retains two control rows and header-back focus references.
- Native Android currently selects Kodi's keyboard in GUIKeyboardFactory;
  using the installed IME requires an actual native/Java text-input bridge.
- The .190 continuity service records screensaver activity and yields ambient
  sampling; its own audit explicitly does not claim the delayed takeover fixed.

## Validation and outstanding scope

The source-validation workflow reconstructs the exact lineage, applies this
patch, compiles the actual Java shell and runs inherited plus new Robolectric
tests at API 35. Weather snapshot tests and the compiled no-JNI weather audit
remain enabled. It has no signing or package-production step. CI status is the
authority for whether those checks passed; this file is not a test result.

All Samsung/API37 physical checks remain outstanding: cover, inner, portrait,
landscape, split-screen, pop-up, live resize, cold/warm launch, immediate/delayed
relaunch, background/foreground, playback on/off, light/OLED, touch and IME.

The following brief areas remain unimplemented: delayed home takeover ownership;
capsule and downward drawer; Movies/TV routes in the active skin; spinner; ambient,
context, confirmation, playback-failure and source dialogs; global touch timing;
settings and logo audit; Android IME; movie transition; compact player and volume;
native crash ownership; CPU constraints; deterministic native teardown and bounded
recovery; internal freeze watchdog; current-session native geometry/profile
telemetry. The deferred movie-video framing issue is untouched.

The existing weather snapshot implementation, provider/add-on data, native engine,
Resume Hub, installed skin and playback have not been changed by this checkpoint.
