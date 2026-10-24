# Search evidence on the protected 2103401 installation

The delivery target is one signed 2103402 candidate with matching component ZIPs.
No interim diagnostic APK installation is requested. Internal builds are not final
releases and are not user installation prerequisites.

The supplied October 24 archive contains Android reason 2 / status 7 for process
`com.projectinfinity.kodi:kodi`, PID 9097, at **15:22:18 America/Detroit**.
Its native crash snapshot is zero bytes. No faulting thread, PC, stack, signal
code or matching native build ID is present. The APK-native file hash matches
the signed baseline, but it cannot replace an actual crash stack.

No newer uploaded bugreport was found in the recent Library inventory. This
workspace has no attached USB device, ADB, Android SDK, emulator or `/dev/kvm`.
Device reproduction and OS captures are **NOT RUN**, not exhausted methods.

## Capture without replacing the APK

First preserve existing OS evidence. On a computer already connected through
authorized Android Platform Tools, identify the Fold with `adb devices`, then:

```sh
python capture_baseline.py --serial DEVICE_SERIAL --output private-fold-evidence --bugreport
```

The script records existing exit history, crash and recent logcat buffers,
available native/ANR DropBox records, build/API/package information and memory,
then requests an Android bugreport. Each command is bounded. Failed, empty,
truncated and partial results remain explicit in `capture-manifest.json`.
The tool never launches, stops, installs, clears, resets or changes Infinity,
its profiles, providers, logs or settings. It does not use root.

Android also supports **Developer options → Take bug report** directly on the
device, without an APK change. Existing reports may remain in `/bugreports/`.
Availability depends on the device and retained OS records; a missing or denied
record is not evidence that no crash occurred.

If retained evidence lacks the incident, reproduce the original sequence on
2103401 while capturing logcat: Search → History → restore the stored query →
select Search All → explicitly submit → results/Back. Record the device-local
time and whether Enter or the Search button was used. Save an OS bugreport
immediately after the failure, without clearing logs. Stop reproduction after
capturing the failure; do not manufacture 50 passing candidate cycles from this
baseline investigation.

Bugreports can contain personal data and other applications' logs. Keep raw
reports private; do not commit them to GitHub. The script does not upload them.
For review, retain the original privately and extract the relevant timestamp,
process/PID, signal/code/address, native backtrace and module build IDs.

## Attribution and release gates

1. Match event time and process to the observed Search failure.
2. Match each faulting module build ID to the exact baseline binary and symbols.
3. Establish the failing ownership/call path before proposing a native repair.
4. Keep signal termination distinct from ANR, Java exceptions, older crashes and
   Essential-First Close results.
5. Require the approved candidate Search, Home-return, rotation and integration
   checks. Physical Fold acceptance remains separate and pending.

An interim APK could be considered only after these viable OS-record and
baseline-reproduction paths have actually been attempted and their limitations
documented. None is currently demonstrated indispensable.

Official references: [Android bugreport capture](https://developer.android.com/studio/debug/bug-report)
and [native crash interpretation](https://source.android.com/docs/core/tests/debug/native-crash).
