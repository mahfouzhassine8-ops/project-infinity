# Infinity background/resume RC1 — candidate, not a lock

## Exact lineage

This candidate branches from successful Candidate 2 **run 40**, GitHub run
35044752997, source commit `2674c05e605afbf19a2fe54bdab1a552e76ec394`.
The postponed Extended Background branch is retained as historical reference,
not merged wholesale; it predates later successful packaging repairs.

Base signed APK SHA-256:
`8ef45e9c54a79e2295e295ce1fcdd3430322a0049c7ff5227804c15aed6b4c57`

Native libkodi.so SHA-256, retained byte-for-byte:
`9783527356ec108fb3bdd61213dc6c7af9b227da3b81051163aa893a9fa358d0`

Candidate: `com.projectinfinity.kodi`, versionCode **2103136**,
versionName **1.0.9-Cobra-Background-Resume-RC1**.

## What changes

The optional Extended Background Mode remains **OFF by default**. Enable it in
**Infinity System Hub → Cobra → Settings → EXTENDED BACKGROUND MODE**.
It applies to the shared Infinity process, not just the Cobra screen. Both Main
and Cobra synchronize it only after resuming in the foreground. Android must
allow the visible notification before it can be enabled. The notification is
low-importance and has a **Turn off** action.

A selected ON setting is a saved request. The notification confirms that the
foreground service is active; a setting alone is not proof. Restricted service
starts/promotion and notification-query errors are handled without crashing the
activities. Swiping away the app task ends the service session. Manually
reopening the app honors the saved preference. Force-stop is not bypassed.

There is **no wake lock**, boot restart, polling keepalive, or promise of survival
under Android memory pressure. This does not reconstruct an Activity after
process death or guarantee uninterrupted playback in the background.

Cobra's non-PiP pause/resume now remembers each actual player separately, including
buffering players. Duplicate stop callbacks do not lose resume intent. Manually
paused, stopped, ended, released, or replaced players are not blindly restarted.
Late playback startup is deferred while hidden. The stall watchdog cannot
restart hidden/paused playback. Actual PiP playback and its existing cleanup,
audio-owner, rotation, and Fold behavior remain unchanged.

## Preservation and build boundary

The real Android Java layer is compiled from source against Android SDK 35 and
the same pinned dependency declarations. Existing compiled resource IDs are
pinned and checked. The new manifest is compared structurally against run 40;
only version identity plus the background service/permission may differ.
All original native declarations must match between the old and new DEX.

The final APK reuses **every original native library, asset, compiled Android
resource, and other non-manifest/non-DEX payload entry** exactly. No Kodi native
recompilation, native patch, smali rewrite, skin update, Command Center update,
Health Center change, or provider configuration change is part of this task.
The locked skin 1.0.5.134 and companion suite remain untouched.

The permanent signing certificate must match run 40. There is no test-key
fallback. All intermediate source snapshots, receipts, tests, hashes and the
exact base APK are archived. An APK update cannot itself back up device userdata.

## Device acceptance — still required

1. Update-install this APK over the matching-signed existing Infinity; do not
   uninstall or clear data. Confirm 2103136, one launcher, existing settings and
   provider accounts retained. The default setting must be OFF for a fresh
   preference; an existing explicit preference is intentionally retained.
2. With mode OFF, exercise Kodi → Android Home/Recents → Kodi, idle and playing.
   Retest native rotation unlocked/locked, portrait/landscape, Fold/cover,
   split-screen and PiP. Verify normal player pause/return behavior.
3. Enable Extended Background Mode. If notifications are denied, opening Android
   notification settings is offered; Cancel must leave the setting unchanged.
   After granting notifications, return and explicitly enable the mode again.
4. Confirm the notification. Leave Kodi in the background for several minutes,
   return via Recents, and verify the existing UI state under normal resource
   pressure. Repeat from Cobra, then switch back to Kodi. Process retention is
   an observation to record, not a guaranteed outcome.
5. Turn the mode off using the notification. Confirm the notification disappears,
   Cobra Settings reads OFF, and future ordinary resumes do not restart it.
6. In Cobra, manually pause a channel before backgrounding; it must stay paused
   after return. Background an actively buffering channel without PiP: no hidden
   audio/retry startup; returning may resume only that lifecycle-paused player.
7. Repeat Multi-View with active and manually paused tiles. The prior active tiles
   may resume, paused tiles must stay paused, and the selected audio owner must
   remain unchanged. Repeat rapid background/foreground transitions.
8. Actual PiP should continue as before. When PiP is unavailable/rejected, hidden
   playback must pause. Test stop/release before returning: no unexpected restart.
9. Swipe away the task while mode ON; the notification should clear. Manually
   relaunch: saved ON preference may start a new visible session. Force-stop must
   leave the app stopped until you launch it again.
10. Verify System Hub → Cobra OPEN_LIVE → Return to Infinity, Compact Continue
    Watching, player/OSD, Add-ons → Install from ZIP, and FileBrowser. No skin
    reinstall is needed. Capture fresh logs for any failure before further edits.

Host tests and static APK verification are not Android/Fold runtime testing.
This candidate does not replace any lock until explicitly accepted.

## Recovery

The exact signed run-40 base APK and original source remain preserved. Android
may reject a lower-version APK downgrade. Do not uninstall to force a downgrade
or discard userdata; stop testing and use a separately prepared same-key forward
recovery build if needed. No recovery APK is falsely claimed to be included here.
