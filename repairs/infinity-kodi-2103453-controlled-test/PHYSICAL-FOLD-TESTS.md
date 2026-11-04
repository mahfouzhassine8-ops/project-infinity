# Galaxy Fold controlled acceptance procedure — not yet executed

Device: Galaxy Fold 8 Ultra, Android 17, ARM64. The user alone installs and accepts
the candidate. Record APK version/hash, engine hash, Android build, display and
orientation with each observation. Do not clear data, force-kill Kodi, disable
checkpoint validation or inject failures into the user's real databases.

1. Before installing, complete a normal durable close of the current session.
   If saving is unresolved, stop and preserve diagnostics. Verify 453's original
   certificate and checksum, then perform a normal install-over update only.
   Check that chooser, Preview, Cobra and existing user profiles remain intact.
2. In Kodi, test ordinary video startup, Pause/resume, Stop, Back and Home. Check
   actual picture, audio, position and player state. Reopen a second video. Record
   loading/Stop anomalies independently; this correction does not claim to fix all
   historical playback or loading failures.
3. Invoke Google Assistant, dismiss it and return to playback repeatedly (for
   example ten cycles, stopping on failure). Also test another available source of
   audio-focus loss. Capture which focus event actually occurred; do not assume
   Assistant always sends permanent focus loss. Verify responsive callbacks and
   the existing playback behavior for pausable and, where available, cannot-pause
   sources. Check foreground-return Play and channel/video identity.
4. Repeat screen-off/on and background/foreground transitions. Test portrait and
   landscape, cover-to-inner and inner-to-cover changes, and supported window
   resizing. Check video-surface recreation, audio continuity and responsiveness.
   Capture ANR stacks if any stall occurs; do not infer all surface hangs have the
   same cause as the checkpoint queue defect.
5. Exercise normal Close and restart, then a deliberate watched/resume update on
   a disposable test item followed by ordinary Close. Verify actual persistence
   after reopening. Preserve unknown provider/recursive/PVR obligations as unknown;
   do not classify the old job973/token976 operation without evidence.
6. If a failed checkpoint occurs naturally, record the failed receipt and pending
   owners before further actions. Observe Pause/Stop/focus/foreground and surface
   callbacks: they should finish their existing refusal without hanging Android.
   Refusal is not a successful pause, stop, save or permission to terminate. The
   checkpoint failure must stay visible/blocking. If this condition cannot safely
   be reached, record NOT REPRODUCED, not PASS. Injected failure testing requires a
   separately controlled disposable profile/device, never the real user database.
7. Capture diagnostics promptly if freezing, loading failure, crash or unexpected
   state appears. Record PASS, FAIL, NOT RUN or NOT REPRODUCED for each scenario.
   Stop on a durability failure; follow FORWARD-RECOVERY.md rather than attempting
   a downgrade or forced shutdown. Do not automatically promote or lock 453.

Acceptance requires actual Android evidence. The 20 host checks and ARM64 build
do not prove Android lifecycle, codec/EGL behavior, data durability on the device
or absence of ANRs. Settings retirement, Scudo memory exhaustion, Continue Playing
and Home loading remain separate unresolved workstreams.
