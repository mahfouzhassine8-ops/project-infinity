# Experimental Fold acceptance — no baseline promotion

Keep APK **2103384**, its original signed download, protected skin **1.0.5.223**,
and the current **1.0.5.225** ZIP. Do not uninstall, clear application data, reset
the build, or replace an add-on database. These tests are updates to the existing
Infinity installation. The five established workstreams remain in scope.

**Acceptance device: Samsung Galaxy Fold, One UI 9.0, Android 17 / API 37.**
Record the actual firmware/build fingerprint with every capture. API 30/35 jobs
are supplementary compatibility checks. The API37 workflow uses a published
generic Android17 image and verifies its runtime SDK/release; it does not emulate
Samsung One UI, the Fold's hardware decoder, sensors or physical hinge.

Per the user's October18 continuation, Android15/API35 is **manual-only** for
optional later compatibility checks. It is not automatically scheduled and does
not replace or delay the primary API37/Fold work. Preserve its existing results,
including run39125992273's failed Essential-First Close owner-proof deadline;
that result remains a failure, not a pass or a diagnosed physical crash.

## Candidate choices and installation

**Current API37 gate is blocked:** run39126569633 passed the interface/Stop
matrix but failed Essential-First Close on an unverified Version Check child
attempt. Do not install the coordinated candidate on the Fold based on that
run. The separately versioned Android Version Check correction is undergoing
targeted locked384/original386/corrected386 comparison; it is not yet accepted.
See `VERSIONCHECK-API37-CLOSE.md`. No APK rebuild or protection bypass is part
of that correction. Installing an add-on cannot erase an existing session's
failed writer receipt.

Before the APK update, finish playback and use the existing normal
**Essential-First Close**. Wait for its successful completion before starting
Android's installer. Do not use force-stop as a substitute for that Close.

**Skin 1.0.5.226 — Rotate / Playback only.** This full ZIP can be tested with the
locked APK 2103384. Install the ZIP through Kodi's existing add-on installer as
an update to `skin.infinity.diggz`; retain the existing settings. Verify the
installed version is 1.0.5.226. It does not restore the two new context menus.

**Coordinated candidate — skin 1.0.5.227 + Item Options 0.1.0 + APK 2103386.**
The new touch behavior requires the matching input engine. Do not treat this
combination as ready until its **exact signed APK** passes the fresh/loaded
Android Close/reopen gate and the full UI/Stop matrix. APK 2103386 retains the
2103385 input engine and adds only the API 30 system-bar compatibility repair.
A skin ZIP build alone is insufficient. Install the
permanent-signed APK as an in-place update, then the helper ZIP, then the full
skin ZIP. Preserve Command Center 0.3.5.20 and Rails 0.2.6. The helper checks the
original controller source hashes and refuses writes if they differ.

The older `Infinity-2103385-2103384-Compatibility-Return.apk` is retained for
2103385 only. Its lower version code is not an in-place return from 2103386.
Do not attempt a downgrade or uninstall. A same-or-higher-version compatibility
return must be separately built, signed and qualified before using it.

Record the APK SHA-256 from `SIGNED-2103386.json` and the installed skin/helper
versions. An APK from a different run is a different candidate. Android tests
use disposable emulator profiles only; the user's installed environment is
never a clean-state test target.

## 1. Player rotation and Playback

1. Play a known working video. Open the OSD and press the restored Rotate icon.
2. Verify white means **Follow Device** and cyan means **Infinity-controlled**.
   Verify actual orientation changes with the device's physical orientation;
   a color change or absence of a Repeat toast alone is not a pass.
3. Repeat folded and unfolded, portrait and landscape. Verify no Repeat action.
4. Open Playback: **Display Mode must be absent**. Test the remaining menu rows,
   including Video Settings, zoom/aspect, audio/subtitles and Stop.
5. Verify PiP, audio continuity, playback restart and background/foreground
   return using the previously working controls.

## 2. Home Continue Playing

Use one movie and one episode with known saved progress. Record the original
position, watched indicator, Watchlist/Collection membership, rating and custom
list privately so that intentional test changes can be restored.

1. Normal tap: retain the original Resume/Play choice and correct provider route.
2. Press and hold the item: open **Continue Playing — [that item]**, not the
   All Add-ons popup or a generic context menu.
3. Tap a different popup row once: highlight only. Tap the same row again, or
   press D-pad Select, to invoke it. Back/tap outside must perform no action.
4. Check original item highlight, rail and scroll position after dismissal.
5. Exercise each applicable action: watched/unwatched, reset progress,
   Watchlist add/remove, Collection add/remove, rate/change/remove rating,
   custom list, and remove from Continue Playing. Re-seed progress by ordinary
   playback when testing an action that intentionally removes the item.
6. Close through normal Essential-First Close, reopen, and verify each intended
   state remains. Confirm unrelated saved titles, progress and play counts did
   not change. Repeat for an episode, checking season/episode identity.

## 3. All Add-ons → Video Sources

For a left tile and a right tile, including tiles after scrolling:

1. First tap selects/highlights and remains on the grid.
2. Tap the same selected tile again: open that add-on once.
3. Return, first select a different tile, then hold it: open that tile's menu.
4. Tapping a different tile must change selection without launching either.
5. The menu must follow this order, omitting unsupported actions only:
   Open; Add-on Information; Add-on Settings; Add to Favourites;
   Add to Infinity Rails; Hide from This View; More / Manage Add-on.
6. Move popup focus without invoking anything. Back/outside dismissal must
   retain the exact tile and scroll position, with no ghost panel/focus trap.
7. Open Information and Settings for the correct add-on. Check Favourites and
   Rails create working shortcuts through their existing owners.
8. Hide a harmless tile. Verify the add-on remains enabled and its settings,
   existing favourite, rails and provider entry points still work. Use the
   separate **Restore Hidden Video Sources** control to restore it. Close and
   reopen to confirm the visibility choice is durable.
9. Open More / Manage Add-on → Disable Add-on on a harmless test add-on. Confirm
   the warning names it and distinguishes disable from hide. **Cancel** and
   verify it stays enabled. Do not use a production provider for a disable test.
10. Repeat after rotating and folding/unfolding, in Light, Dark and OLED.
    Check the recovery control remains reachable and the popup fits on screen.
    If available, check TV/D-pad navigation still opens on explicit Select.

## 4. Exit/lifecycle paths — crash remains unresolved

**Optional passive capture instead of deliberate reproduction:** The checked-in
`fold_passive_crash_watch.py` runs on the user's Mac with authorized ADB,
observes the existing Kodi engine process while the user uses Infinity normally,
retains a bounded rolling crash/main/system logcat, and collects historical
exit-info and available tombstone/DropBox records if that process disappears.
It never force-stops Infinity, clears logs or data, installs anything, or
uploads private reports. A missing PID alone is not called a crash.
See `FOLD-PASSIVE-CRASH-WATCH.md`. The observer and its host safety checks
are not substitutes for a native fatal stack, a durability receipt, or
physical Fold acceptance.



Run each path separately, ideally first on the retained 2103384 + .226 skin and
then on a qualified coordinated candidate. Use the same privately recorded
source and playback settings for comparison.

* **A:** Video → Stop → movie choices. Remain there for at least 30 seconds.
* **B:** Video → Stop → movie choices → Back/Home. Remain there for at least
  30 seconds. Then restart playback and test a background/foreground return.
* **Background:** Repeat normal background/foreground return after **5, 20, 45
  and 90 minutes**, both idle and playing. Record Home versus Recents return,
  screen on/off, PiP/background-playback mode, and whether the original process
  survived or Android reclaimed it. Stop is not a prerequisite for this path.
* **Screensaver:** Let the configured screensaver appear normally, dismiss it,
  then navigate provider choices/Home. Repeat after background return.
* **Fold:** Test one fold/unfold or portrait/landscape transition per capture,
  both playing and idle, then repeat while returning from the background.
  Record the starting and ending physical state privately.

When ADB is available, run the supplied capture script on the computer before
reproducing, with a new private output directory each time:

```bash
python3 capture_stop.py --path A --out ./Infinity-Stop-A --bugreport
python3 capture_stop.py --path B --out ./Infinity-Stop-B --bugreport
python3 capture_stop.py --path background --out ./Infinity-Background --bugreport
python3 capture_stop.py --path screensaver --out ./Infinity-Screensaver --bugreport
python3 capture_stop.py --path fold --out ./Infinity-Fold --bugreport
```

Follow its timestamps/prompts. It collects logcat, exit-info and permitted
crash records; it does not clear logs, force-stop, install, change settings or
upload anything. Export Infinity Diagnostics immediately afterward through its
existing UI. Keep all captures private. A missing/denied tombstone is a capture
limitation, not evidence of a clean exit. Never publish titles, screenshots,
playback history or diagnostic archives in the public repository.

For a **still-live frozen engine**, optionally add `--native-snapshot` to request
`debuggerd -b` after reproduction. This can briefly pause threads; Samsung may
deny it. The script records failures and never elevates access or changes policy.
It also records process/thread, power, display, device-state and exit snapshots.
Those snapshots are evidence to correlate, not an automatic crash diagnosis.

## Final acceptance gate

Finish with normal Essential-First Close/reopen and verify durable Resume Hub,
watched progress, Watchlist, Collection, settings, favourites and installed
add-ons. Confirm Cobra, PiP, Multi-View, background playback, audio, subtitles
and timeshift using the existing working configuration. Record any regression
against the exact candidate SHA. No final lock is authorized by these builds
or by emulator success; promotion requires the user's explicit Fold approval.
