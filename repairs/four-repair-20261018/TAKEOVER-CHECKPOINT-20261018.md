# Infinity four-repair implementation — takeover checkpoint (Oct 18)

**Status: implementation partially verified; NOT approved for Fold installation or final lock.**

Owner: ChatGPT continuation of Astra's existing work. Preserve source history and protected locked APK 2103384. No APK, native engine, protected-write/shutdown admission, installed services, profile, signing identity, or user data were modified by this continuation.

## Protected identities
- Locked APK: 2103384 SHA256 `b571676731bb9bdccb25134c557be613e15cc9adaf77d6675dabc8e0586e54af`.
- Original signed experimental APK: 2103386 SHA256 `342587d9079f7e51b61ef525c04ae9b62adb6d128791164acbd99ec691fbac87`.
- Skin 1.0.5.227 and UI helper 0.1.0 remain experimental.
- Original protected locked skin 1.0.5.223 and current .225 Foundation retained.
- User's Samsung Fold: One UI 9.0 / Android17 (API37). Generic AVD is not Samsung firmware.

## Existing UI progress retained
Previous exact 2103386 API37 full UI run39126569633 reported 89 app observations covering OSD Rotate/Playback, Home item context, both-column All Add-ons gestures/menus and Stop choices/Home; it FAILED unchanged Essential-First Close. That is not a release pass; retained application and state after Close remain unqualified.

## Targeted Version Check work retained
- Native script ledger originally blocked Android `service.xbmc.versioncheck` because its bundled desktop Linux `lsb_release` subprocess was unverified. Corrected experimental same-ID add-on v0.5.28+infinity.1 selects the existing Android non-APT codepath without bypassing service or durability enforcement.
- Matched API37 run39129598974 found original locked384/original386 Close refused with `python_persistence_observer_initialization_failed` and two Version Check opaque-child blockers. Corrected addon eliminated the child blockers and natural startup was observed; Close still FAILED `protected_durability_failed:/memfd:[guest /proc/self/maps] (deleted)`.
- Dedicated descriptor run39130737400 showed an ordinary read-only `/proc/self/maps` Python TextIOWrapper and successful flush/close, but under x86_64 Android API37 `libndk_translation` a different kernel memfd reported O_RDWR and incompatible identity/flags. Do not infer safe persistence from apparent guest readonly state.
- `translated_descriptor_evidence.py` and fail-closed negative controls classify this exact captured translation mismatch for diagnosis only: `durable_close_verified=false`, no write-protection or exception change. Failed Close stays red and original receipt preserved. Source-only CI host run39133536492 PASS.
- Locked 2103384 source guard run39133557178 PASS. Earlier matched Close and descriptor Android runs remain failures, not reclassified.
- One bounded ARM64 runner preflight run39133157301 PASS as a host check only: architecture aarch64, RAM15.57GiB, /dev/kvm ABSENT; therefore direct KVM-accelerated ARM64 Android17 AVD cannot be run on this GitHub runner. No full emulator reruns were started during takeover and no native APK rebuild was done merely to get green.

## Crash investigation: still open
- Physical October18 abnormal engine exit status139 remains unproven cause. No matching native tombstone/backtrace in original privately exported diagnostics. Do not blame Stop, graphics/directory deadlock, or background return without evidence.
- The signed 2103386 APK contains the existing `libinfinitycrash.so` companion and exit collector references, but their mere presence does not prove the native fatal handler was installed/owned the process at failure or that it wrote a record.
- Added `fold_passive_crash_watch.py` for a Mac USB-debugging session: read-only rolling 64MiB logcat, PID and rapid PID-replacement detection, private Android exit/crash/DropBox snapshots. No app installation/force-stop/wipe/system setting changes; a process disappearance is UNKNOWN, never automatically a crash. `test_fold_passive_crash_watch.py` and host CI run39133536492 PASS. See `FOLD-PASSIVE-CRASH-WATCH.md`.
- Crash cause, missing tombstone recorder gap and actual corrective native fix remain OPEN. The physical Fold is not connected to the GitHub execution hosts.

## Next safe decisions
1. Do **not** install/promote experimental 2103386 as a qualified full four-repair release. Keep 2103384 locked.
2. Obtain physical Fold crash/event observations during normal use (optional passive capture; no deliberate triggering necessary). Correlate original PID, timestamp, Android exit cause, crash-recorder handler breadcrumbs and native frames; protect privacy.
3. For shutdown: either obtain *native* ARM64 Android17/Samsung Fold matched Close data with immutable protected user data, or a genuine direct ARM64 build/test host; do not waive memfd, broaden path lists, or mislabel translated AVD as a durable pass. If physical prior locked base Close passes and experimental fails with matching conditions, trace actual candidate delta before implementing.
4. Only implement crash/Close root-cause corrections when evidence proves the failing component. Preserve essential owner16/17, checkpoint durable/sealed, zero blockers, process death/reopen, Watchlist/progress, background player and PiP; user explicitly authorizes any final lock.

**Source-only implementation and evidence capture are complete for this checkpoint; the underlying native crash and fully qualified Close are NOT complete.**
