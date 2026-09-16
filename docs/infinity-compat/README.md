# Infinity compatibility work: not an APK release

Baseline: signed Infinity 1.0.6, APK SHA256
`db85653a1453748dd96f0d6c3e4c0e92693cf1938cb5f42a225067ff6c43af85`.
The released theme-hook branch and its signing identity are unchanged.

## Implemented here

- A source patch adds bounded, local Android ApplicationExitInfo collection on a
  background thread. It queries only this app's package, saves exit reasons on
  API 30+, and requests available ANR/native evidence (native traces on API 31+).
  It neither changes codec/player teardown nor replaces crash/signal handlers.
  Native traces are protobuf, can be absent/evicted, and may contain private data.
  This source patch is not installed in the released 1.0.6 APK.
- A concrete presentation defect is reproduced against the signed 1.0.6 APK:
  VideoOSD references InfinityColor_blue and InfinityColor_white but the base
  palette definitions are absent. The old transformer updated existing colors
  without creating them on a fresh source-built base. The new transformer fills
  missing definitions and preserves every non-palette/non-signature APK member.
  Its temporary output is UNSIGNED, not an installable update or a crash fix.
- The player-resource auditor traverses includes, expressions and variables,
  records asset/font hashes, and explicitly refuses to call the boundary ready
  for release. It does not activate a window redirect.
- A small manual Support Exporter collects active-skin XML, four appearance
  settings and Health Center source. It does not copy user account-settings
  folders, full Kodi logs, media, texture bundles or font binaries. With explicit
  consent it can also attempt a same-UID Android crash-buffer snapshot and copy
  retained diagnostic traces. Unavailable access is reported, not bypassed.
  No automatic network upload, add-on disabling or skin changes occur.

## Crash findings and limits

The supplied Health Center archive contains restart detection and Kodi text logs,
not a fatal Android stack. Its skin-theme field is not the active skin add-on ID.
The active skin observed in the old log is skin.xenon2 version 430.99.8.
A MediaCodec buffer timeout appears during Stop as well as earlier in playback.
Python no-media exceptions after Stop are symptoms, not proof of process death.
No component is confirmed responsible. Raw logs, media URLs and account data
are deliberately not checked into this public repository.

## Required ownership contract (pending implementation)

Diggz/Xenon retains its home layout, widgets, menus and artwork. Infinity retains
its explicit light/dark/system policy and permanent player controls. Implementing
that requires a Xenon-specific home palette adapter plus an independent player
resource package: includes/defaults, variables/expressions, named fonts, packed
texture resolution, localization, custom-dialog IDs, and native window routing.
Do not switch the global skin during playback or redirect only VideoOSD.xml.
Do not blanket-disable add-ons or suppress player errors to mask the crash.
Ordinary skin isolation is not a security sandbox against arbitrary add-on code
running with the same application privileges.

Exact installed Xenon XML is needed before claiming its home-screen palette is
compatible. The Support Exporter is the next input-gathering step. Device checks
must cover Stop/resume, audio/subtitles, lock/unlock, folding and both palettes.
There is no completed combined player-protection/crash-fix APK in this commit.

## Validation

The isolated preflight downloads and hash-pins the actual released 1.0.6 APK,
prepares the pinned Kodi/bridge source, runs Python tests and real JVM file-I/O
tests, and compiles both diagnostic classes against Android's real API jar.
This is not a full Android build or runtime/device test. It uploads receipts and
test logs only; the generated unsigned test APK is not published as a release.
