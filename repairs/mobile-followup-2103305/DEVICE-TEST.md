# APK 2103305 Power Route RC1 — unlocked test candidate

Install as an update over locked APK 2103304. Keep skin.infinity.diggz 1.0.5.195
and the existing controller. Do not uninstall, reset userdata, change providers,
or install a different skin. This candidate is not skin 1.0.5.196.

This APK packages one verified route-installer correction. It accepts the
existing Android/non-Android conditional Power routes without changing their
bytes, and a rejected profile no longer aborts later valid profile checks.
It reuses every native library, asset and Android resource from APK 2103304.
The normal-close handoff and explicit Force Close policy remain unchanged.

The native shutdown hang is NOT claimed fixed. The earlier suggestion that
restoring direct Quit() is a proven correction is withdrawn: the recorded 297
lock itself had a relaunch-delay exception, and the current hang has not been
correlated to its owner. Do not replace shutdown ordering without evidence.

1. Confirm installed APK version 2103305 and active skin version 1.0.5.195.
2. Check Health Center's Power route audit. The unified profile must validate;
   it must not report Missing command 200. Report rejected/unknown profiles.
3. Record normal Close through immediate launcher relaunch and a usable Kodi
   frame; repeat five times. Separately repeat with five seconds before launch.
4. Test explicit Force Close separately. Normal Close must never force-stop.
5. Test Android Home/return during playback. It must preserve the live session.
6. Repeat on cover/inner screens, light/dark, portrait/landscape, split/pop-up
   windows and live resize. Source/host tests are not these physical results.
7. After a hang, export the current Health Center report/raw traces with exact
   version, session, PID, time and the chosen Power action. Check native cleanup
   completion and Android exit records; a Java request alone is not completion.

Drawer/capsule/player/dialog polish, Umbrella source/resolver sizing and Back
freeze, idle takeover, historical crashes and overall acceptance remain open.
The complete skin archive is required before making the 1.0.5.196 candidate.
The deferred movie-video vertical framing must remain unchanged.
