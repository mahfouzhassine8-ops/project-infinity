# Cobra 2103206 — physical-device acceptance

Status: NOT PERFORMED. Automated results are separate from physical acceptance.
Install as an update over locked 2103205; do not uninstall or clear app data.
Record phone model, Android/One UI version, candidate APK hash, call type, route,
and whether Samsung Multi Sound is enabled. Test without relying on Multi Sound.

1. With Normal Android Behavior (default), confirm normal Live TV, pause/play,
   rewind, channel changes, preview, mini-player, background and PiP work as before.
2. Receive a call while playing and while paused. Cobra yields audio, never blasts
   or automatically starts media, and keeps the current channel/player/session.
3. Enable Allow When Manually Resumed during an active call: merely changing the
   setting must stay silent. Press the existing Play control once. Confirm it
   attempts media playback. Check audio and video separately; note denial/muting.
4. Repeat explicit Play in fullscreen, mini-preview, native PiP controls, and
   background media notification. Pause must work; a later focus grant must not
   undo your pause. D-pad and touch must use the same behavior.
5. Repeat with cellular and supported VoIP calls; speaker, earpiece, wired/Bluetooth
   routes as available. Multi Sound may change outcomes but is not required.
6. Rewind before a call. Note position/live-edge distance before and after Play,
   call end, PiP return and background return. No jump-to-live, stream restart,
   channel reset, duplicate audio/player or lost timeline/session is acceptable.
7. End the call while playing, paused, and awaiting focus. Preserve user intent.
   Call end must not retune or duplicate the player. Repeat eight call cycles.
8. Switch back to Normal Android Behavior during a manually resumed call. Cobra
   must yield again; a late focus callback must not override the disabled option.
9. Multi-View: only selected audio tile may request focus; preserve layout on PiP
   return. Changing channels must not inherit the old player's call authorization.
10. Incoming second call/focus interruption must revoke earlier manual authorization.
    No automatic retry from navigation, rotation, Fold transition or screen unlock.
11. Verify setting survives navigation and app restart. Check its two options and
    existing Play/Pause icon/labels in Light, Dark, OLED Black and Follow System.
12. Health Center: compare policy, mode hint, granted/delayed/denied attempt and app
    mute with observations. A grant is not proof of audible output. Save redacted
    diagnostics if Play remains silent; do not expose source URLs or credentials.

Keep the locked 205 APK and complete rollback available. If Android rejects a
downgrade, do not delete data to force it; use a reviewed forward-version recovery.
