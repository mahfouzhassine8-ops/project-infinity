# Kodi P0 physical Fold testing — engineering candidate, not acceptance

Android runtime verification is pending. Native compilation and host checks do
not prove the ANR is fixed. Job973/token976's historical item route is unknown.
Recursive, UPnP, PVR and unreviewed persistence obligations remain blocking.

## Preserve the current session before installing

Keep the existing data/profile and APK recovery baseline. Finish active playback
and use the current normal Close path; allow its existing verified-save process
to complete. If it reports CHECKPOINT_FAILED or unresolved saving, leave that
session intact and capture Health Center evidence. Do not force-stop, swipe-kill,
clear data, uninstall, bypass a checkpoint or install over an actively unresolved
save simply to start this test. No such operation is part of this procedure.

Install the signed candidate directly over the application when the current
session is safely closed. Package and permanent certificate must match the
published verification; no new permissions or database migration are introduced.
Record the installed version and Health Center installed-code identity.

## Selected independent checks

1. **Normal Close/reopen:** open Kodi normally, navigate Home and one existing
   library screen, then use the normal approved Close control. Record the actual
   checkpoint result. Reopen only after normal completion and confirm the same
   profile, settings and library state. A successful Android task exit alone is
   not a verified-save receipt.
2. **Single-item watched update:** choose a disposable/test library movie or
   episode with no important resume position. Record its initial watched state
   and private item route. Use the existing Kodi watched/unwatched action, then
   Close normally while the update is pending if that timing is observable.
   After a verified close/reopen, confirm the actual watched state and expected
   resume behavior. Restore the test item's original watched flag through the
   same existing action if needed. Do not use an in-progress personal movie for
   a reset-resume test. If no pending job was observed, record that timing case
   NOT REPRODUCED rather than claiming the pending-job test passed.
3. **Stop/Back/Home:** play an existing Kodi video, use Stop, return with Back and
   navigate Home. Repeat with another video. Confirm responsive input, correct
   item identity and normal saved progress. Do not open Cobra or change Preview.
4. **Display lifecycle:** during Kodi playback and after returning Home, check
   screen-off/on and background/foreground once, recording times and whether
   Android input, video/surface restoration and playback behave normally.
   Check the front-to-inner and inner-to-front Fold transition with the same
   channel/video session. Use ordinary rotation only where already supported.
5. **Combined failure case, only if it occurs naturally:** if an Unknown job
   blocks a checkpoint, retain the blocker. Check whether Android focus/surface
   transitions remain responsive while the checkpoint is failed/pending. Do not
   inject a writer, alter a provider, clear a blocker or manufacture a receipt.
   If no such blocked state occurs, report the combined case NOT REPRODUCED.

For each case, record PASS, FAIL, NOT RUN or NOT REPRODUCED, plus app/native
identity, display/orientation, action, timestamps and actual checkpoint outcome.
Keep normal completion and failed-checkpoint lifecycle results separate.

## Evidence and stop conditions

Export the existing Health Center diagnostics after the selected checks. Keep
raw diagnostic archives private. Preserve the actual coordinator receipt,
installed-code record, native/Java histories, ANR/exit records and observable
watched/progress readback. An older exit record is not a new candidate failure;
match process/session/time and producer identity where available.

If there is CHECKPOINT_FAILED, a missing receipt, freeze, ANR or unexpected
watched/progress change, preserve that result. Do not force-kill or weaken saving
to obtain a PASS. Do not repeatedly retry the same failure without new evidence.
Missing evidence remains unverified. This candidate is not automatically locked,
promoted, accepted or described as a complete fix for every Unknown job route.
Physical Fold acceptance belongs solely to the user.
