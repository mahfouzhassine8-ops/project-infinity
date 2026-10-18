# Experimental Fold acceptance — no baseline promotion

Keep APK **2103384**, its original signed download, protected skin **1.0.5.223**,
and the current **1.0.5.225** ZIP. Do not uninstall, clear application data, reset
the build, or replace an add-on database. These tests are updates to the existing
Infinity installation. The five established workstreams remain in scope.

## Candidate choices and installation

**Skin 1.0.5.226 — Rotate / Playback only.** This full ZIP can be tested with the
locked APK 2103384. Install the ZIP through Kodi's existing add-on installer as
an update to `skin.infinity.diggz`; retain the existing settings. Verify the
installed version is 1.0.5.226. It does not restore the two new context menus.

**Coordinated candidate — skin 1.0.5.227 + Item Options 0.1.0 + APK 2103385.**
The new touch behavior requires the matching input engine. Do not treat this
combination as ready until its **exact signed APK** passes the fresh/loaded
Android Close/reopen gate. A skin ZIP build alone is insufficient. Install the
permanent-signed APK as an in-place update, then the helper ZIP, then the full
skin ZIP. Preserve Command Center 0.3.5.20 and Rails 0.2.6. The helper checks the
original controller source hashes and refuses writes if they differ.

Record the APK SHA-256 from `SIGNED-2103385.json` and the installed skin/helper
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

## 4. Stop paths — crash remains unresolved

Run each path separately, ideally first on the retained 2103384 + .226 skin and
then on a qualified coordinated candidate. Use the same privately recorded
source and playback settings for comparison.

* **A:** Video → Stop → movie choices. Remain there for at least 30 seconds.
* **B:** Video → Stop → movie choices → Back/Home. Remain there for at least
  30 seconds. Then restart playback and test a background/foreground return.

When ADB is available, run the supplied capture script on the computer before
reproducing, with a new private output directory each time:

```bash
python3 capture_stop.py --path A --out ./Infinity-Stop-A --bugreport
python3 capture_stop.py --path B --out ./Infinity-Stop-B --bugreport
```

Follow its timestamps/prompts. It collects logcat, exit-info and permitted
crash records; it does not clear logs, force-stop, install, change settings or
upload anything. Export Infinity Diagnostics immediately afterward through its
existing UI. Keep all captures private. A missing/denied tombstone is a capture
limitation, not evidence of a clean exit. Never publish titles, screenshots,
playback history or diagnostic archives in the public repository.

## Final acceptance gate

Finish with normal Essential-First Close/reopen and verify durable Resume Hub,
watched progress, Watchlist, Collection, settings, favourites and installed
add-ons. Confirm Cobra, PiP, Multi-View, background playback, audio, subtitles
and timeshift using the existing working configuration. Record any regression
against the exact candidate SHA. No final lock is authorized by these builds
or by emulator success; promotion requires the user's explicit Fold approval.
