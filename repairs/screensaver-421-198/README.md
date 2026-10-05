# Infinity / Diggz Arctic Mirage repair candidate

Date: 2026-10-05. Status: source and package verified; physical acceptance pending.

## Delivery

| Component | Exact input | Candidate |
| --- | --- | --- |
| Infinity skin, `skin.infinity.diggz` | 1.0.5.197 Browser Focus RC1 | 1.0.5.198 Arctic Mirage Integration RC1 |
| Diggz Arctic Mirage, `screensaver.arctic.mirage` | installed version 420 | 421 Infinity Responsive RC1 |
| Android app, `com.projectinfinity.kodi` | APK 2103305 | unchanged by this repair |

Install both ZIPs. The skin supplies the responsive presentation; the screensaver
supplies the lifecycle repair. An APK update is not required for this delivery.
The separately built APK 2103306 provider-coordinate candidate does not contain
these screensaver updates and is not a prerequisite.

## What changed and why

The version 420 fallback XML used a fixed 1920 x 1080 canvas. Its plot ended at
1295 and its hint ended at 1100, beyond the 1080 canvas. Skin 197 had no named
override. Candidate 198 adds the override to all 14 retained skin profiles,
uses existing Infinity fonts, and sizes the backdrop and metadata relative to
the owning canvas. The opaque backdrop covers the underlying page. Short
canvases omit the plot to keep the title and Details control inside the viewport.

Version 420 assigned a boolean to `restore_paused_video_osd`, shadowing the
method, and its entry point never invoked the restoration helper. Candidate 421
uses a separate setting member and restores the OSD only for the same still
paused video that started in foreground fullscreen playback. It does not start,
resume, or replace playback, or pull a background paused video out of Home.

The controller now has one script-owned callback-pumping loop. Event callbacks
record intent; close and metadata reads occur in that loop. Cleanup closes once
and detaches the monitor. There is no daemon GUI polling thread and no global
module-cache clearing. A changed-item key limits full metadata capture. Generic
wake and plain touch close the saver without launching another information
dialog; explicit Details/Info can request information. Back/Stop cancel any
pending follow-up action. A settled viewport change recreates only this saver
while Kodi still reports it active, since the retained native reflow guard
excludes the absolute XML path used by Python windows.

These defects and changes are source-confirmed. The reported device freeze's
root cause and the repair's on-device outcome have not been established.

## Preservation evidence

- All 2,889 existing non-metadata skin files are byte-identical to exact 197.
- The inherited 197 Add-on Browser focus repair is byte-identical.
- Skin additions are only 14 copies of the named screensaver override; existing
  edits are only addon.xml, infinity-skin.json and the protected manifest.
- The saver changes only addon.xml, default.py, resources/lib/screensaver.py,
  and resources/skins/Default/1080i/screensaver-arctic-mirage-addon.xml.
- Its other 16 files, including settings, widget-source helper, font installer
  and artwork, are byte-identical to installed 420.
- Add-on IDs, skin resolution declarations and dependency requirements remain
  unchanged. No provider, Home, player, drawer, weather, Resume Hub, Android or
  native-engine code is changed by this repair.
- 20 host tests passed: callback ordering, Back, touch wake, explicit Info,
  paused foreground/background playback, abort/error cleanup, polling limits,
  stable/transient resizing, exact preservation, Python/XML parsing and bounds.
- ZIP CRC and exact archive-content round-trip checks passed.

The geometry checks cover the logical canvases derived from cover, inner,
portrait, landscape, square, split-screen, pop-up and TV viewports. They are
coordinate checks, not physical rendering or touch tests.

## Install

1. Keep the supplied rollback bundle. Leave the installed Android APK in place.
2. In Infinity's Add-on Browser, choose Install from zip file and install
   `skin.infinity.diggz-1.0.5.198-Arctic-Mirage-RC1.zip`.
3. Install `screensaver.arctic.mirage-421-Infinity-Responsive-RC1.zip` the same way.
4. Fully close and reopen Infinity so an already loaded saver script is not
   retained. Check the skin version is 1.0.5.198 and the saver version is 421.
5. Under Interface > Screensaver, retain Diggz Arctic Mirage. Retain the current
   widget/source and settings; this package does not reset them.

## Phone acceptance checks

Perform these with the existing configured idle timeout:

1. Idle on Infinity Home until the saver appears. Verify full-window artwork or
   black base, readable title, bounded captions, and no Home/footer bleed.
2. Wake with a normal tap, then repeat with Android Back. Verify responsive Home
   and no unsolicited movie-information dialog or duplicate saver window.
3. While the saver is visible, fold/unfold, rotate, resize split-screen and resize
   pop-up mode. Verify the saver adjusts after the size settles and remains
   dismissible. It must not reload Home or interrupt playback.
4. Pause a video in fullscreen, let the saver activate, then wake normally.
   Verify that the same title remains paused and the OSD returns. Repeat using
   Back: it should dismiss without forcing an OSD or information window.
5. Pause a video in the background while on Home. Activate/wake the saver and
   verify it stays on Home. Verify resumed, stopped or replaced playback is not
   resurrected by a later wake.
6. Repeat activation/wake three times. Verify no stale dialog, delayed secondary
   modal, lost touch input or accumulating UI stall. Check Details/Info only
   when that control/action is received by the saver.
7. Spot-check Home, drawer, player, weather snapshot and provider settings after
   restart. Their source files are preserved, but runtime acceptance is separate.

If a stall remains, record the action, playback state and window mode, then
export the support ZIP with Kodi log and original raw crash/ANR evidence after
recovery. New saver log lines identify the logical canvas and close reason.
Do not treat absent logs as a pass.

## Rollback

Extract `Infinity-Arctic-Rollback-Skin197-Saver420.zip` outside Kodi. It contains
the exact input skin 197 and installed saver 420 ZIPs plus hashes/instructions.
Install those two original inner ZIPs, then fully close/reopen Infinity. The
outer rollback ZIP itself is not a Kodi add-on. No APK rollback or provider reset
is part of this screensaver rollback. Candidates are not locked by host tests.

## Reproduce from source

Use Python 3 with the standard library and the exact two baseline ZIPs. The
builder checks their full SHA256 before writing and refuses output overwrite.

```bash
python3 repairs/screensaver-421-198/build.py \
  --skin /absolute/path/skin.infinity.diggz-1.0.5.197-Browser-Focus-RC1.zip \
  --saver /absolute/path/screensaver.arctic.mirage-420-INSTALLED-20261004-203213-1.zip \
  --output /absolute/path/new-output-directory

SKIN_BASE=/absolute/path/skin.infinity.diggz-1.0.5.197-Browser-Focus-RC1.zip \
SAVER_BASE=/absolute/path/screensaver.arctic.mirage-420-INSTALLED-20261004-203213-1.zip \
python3 repairs/screensaver-421-198/test_repair.py
```

The host mocks verify the actual generated controller's behavior at the Kodi
API boundary. They do not execute Kodi's renderer or Android touch dispatch.

## SHA256

- Input skin 197: `ba1b5639dbbf81136a075d41f81c8a092f7b8afcfe25e71732545a67b21f948e`
- Input saver 420: `1682f01d2f0098f2e3d96d25cfd62ef9cb2cf747f7f4618ff0a25f282632c4f3`
- Candidate skin 198: `27f1b69b00af77b40539fb59e1175bcb98971d63ca66cb24e67315d403cf0363`
- Candidate saver 421: `d9435302d165aa3a176c00c44262f24c84808584aa88f562e5e0ff0ba5ff783b`
