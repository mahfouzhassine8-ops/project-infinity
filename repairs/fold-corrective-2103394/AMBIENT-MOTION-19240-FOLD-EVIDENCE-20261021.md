# Infinity 2103394 physical Fold video — Ambient Home, Motion and other UI observations

**Source:** user-supplied physical Fold recording `19240.mp4`, duration approximately 77.1 seconds, captured on cover/front Compact view. **This document records evidence and diagnostic targets only. No code or APK changes.**

## Confirmed: Ambient Home save/readback does not confirm

- At about 00:00–00:20, user repeatedly opens Infinity drawer → Performance & Ambient → Ambient Home and selects among **Off / Subtle / Immersive**.
- At ~00:02–00:03, ~00:15 and ~00:19, the app displays the exact user-facing failure: **“Kodi did not confirm this setting. Its previous saved value was retained.”**
- Thus the choice UI opens, but its write/readback handshake is failing or cannot be confirmed. The video does **not** independently prove the on-disk value remained unchanged, nor prove that the ambient visual renderer is broken. Do not misstate a false-positive readback error as a definitively rejected write.
- After changing the setting, user-visible ambient result is not clearly demonstrated. Require durable state readback across closing/reopening and visible Off/Subtle/Immersive behavior, including no playback-video recolor.

### Concrete source-level investigation target
`repairs/fold-corrective-2103394/infinity_settings.py`:
```python
actual = xbmcaddon.Addon(owner)
current = actual.getSetting(key) or default
...
if not addon_set_setting(owner,key,values[pick]) or actual.getSetting(key)!=values[pick]:
    xbmcgui.Dialog().ok(...,'Kodi did not confirm this setting. Its previous saved value was retained.')
```
The existing `common.addon_set_setting` calls `xbmcaddon.Addon(owner).setSetting(key,value)` on a **different Addon instance** from `actual` (verified in existing Command Center source). Kodi's setting cache behavior on real Android has not been tested; a stale readback is **one plausible cause**, not yet established. Failures due to `setSetting` itself and failures due to readback are currently conflated in one generic dialog. Instrument and test these separately, using the real expected persistent owner and current on-device source (see the installed APK/ZIP identity investigation).

Test the `script.infinity.commandcenter/resources/settings.xml` schema keys and actual `script.infinity.commandcenter` loaded versions; verify `ambient_home` allows `off/subtle/immersive`. Capture actual saved setting via a newly resolved owner after the write, check writer admission and field persistence, and verify proper Home property notification. Avoid switching modes solely via Home property when persistent write failed.

## Motion / Settings — separate findings

- At ~00:42–00:46, System Hub → Command Center → Motion / Settings **opens correctly**, unlike the earlier reported “This add-on can't be configured.” Good regression to preserve.
- The actual page still displays the contextually wrong heading **“INFINITY COMMAND CENTER · SEARCH”** although the user opened **Motion / Settings**. Confirmed UI labeling issue.
- At ~00:57–01:07, the **Infinity Motion** pop-up offers Full / Reduced / Off, with Full visibly selected. The video does not establish a successfully saved or applied mode change; investigate the same `setting_choice` helper and `motion_mode` setting path as Ambient Home. Do **not** claim it is defective solely because Full remains highlighted in screenshots.
- Command Center screen reports **60 Hz requested, 120 Hz active**, with **requested-not-active** and **granted=false** at ~00:46–01:12. This is a confirmed *reported mismatch*, but Android may legitimately decline a refresh request; diagnose mode/permission/power state rather than force a refresh rate or represent the mismatch as a proven Infinity fault.

## Other observable UI / regression notes

- Compact Home heading/title overlap persists at the top of the screen (~00:32 onward): stacked letters across “Movie Addons” / “Latest Releases” region. It is **already recorded as a separate Compact layout defect**, not an Ambient Home issue.
- Home posters and add-on Rails stay populated while accessing side drawer, System Hub, Power and Command Center during this clip. Preserve successful content and navigation.
- System Hub Silent Mode has the approved **blue active indicator** (~00:42 and ~00:54). Do not change the already working notification suppression or red Health Center indicator.
- Power modal opens and offers Shutdown Timer, Force Close Kodi, Close Kodi, Skin Settings and Reload Skin (~00:34–00:36). This video does not document a Close attempt or shutdown failure.
- Normal-mode row receives focus in the drawer (~00:28), but there is insufficient evidence to conclude a normal-view switch was attempted and failed. Do not add a speculative mode-switch bug.
- The recording does **not** demonstrate Option B popup; that is separately proven failed by the user's still screenshots and existing fourth-failure note. Authorized Option B scope remains **Normal and Compact, Movies and TV**, not Cinema/Two-Pane.

## Acceptance tests / isolation

1. First capture version/loaded-file hashes for the CC24, UI Repair 0.1.6, Watched Bridge 1.0.5, Skin 1.0.5.231, Health Center 2.5.21 and unchanged Rails 0.2.7; compare external files to signed APK before changing source. ZIP installs can shadow bundled files.
2. On physical Fold, vary each Ambient mode and distinguish setSetting failure, stale-instance readback, persistence/flush timing, actual fresh-instance value, resident experience publisher, and rendered result. Check after normal Close/reopen.
3. Repeat Motion Full/Reduced/Off with actual persisted value and meaningful UI effect. Preserve working route to the screen.
4. Correct the Motion context heading only with a scoped UI label; no generic Command Center or third-party menu rewrite.
5. Independently verify desired refresh mode vs OS active/granted outcome. Do not treat a denied Android request as if it were silently granted.
6. Test on the cover/front and inner Fold displays and with Normal and Compact Home layouts; preserve Cobra, providers, playback, Essential-First and user data.
7. No final Lock or statement of device pass until user verifies the corrections on the physical Fold.

**Status:** Ambient Home setting confirmation **FAILED on physical Fold**. Motion selector outcome **INCONCLUSIVE**. Motion contextual heading **FAILED visually**. Requested/active refresh mismatch **OBSERVED**, cause unknown. Compact header overlap **CONFIRMED separately**.
