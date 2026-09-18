# Cobra 2103164 device acceptance

Install the signed APK over the existing app. Do not uninstall or clear data.
The exact 8f2c9c7 / 2103163 APK and HM 2.0.3 theme are preserved; this is a new candidate, not a new lock.

1. Open fullscreen playback. Check More, Aspect / Display, Channel playback, Audio & subtitles, and their submenus. They should remain horizontally centered at the bottom inside system bars, including folded/inner displays and landscape. Rotate with a menu open; controls must stay reachable and playback must not restart.
2. From fullscreen, press Home. PiP should contain video only. Expand PiP: the same fullscreen session should continue. Close PiP using Android's close/swipe-away control: audio must stop. Reopen Cobra: it should show browsing, not reopen the dismissed fullscreen video or auto-play it.
3. From the main-screen mini-player with Play in background ON, press Home. Audio should continue with Android media controls. Pause, Play and Stop should control that same session. Tap the media notification: return to Cobra browsing/mini-player without creating a second session.
4. Repeat mini-player exit with Play in background OFF. No background mini-player audio should continue. Task removal and notification Stop must not leave ghost audio.
5. Recheck rotation, guide views/EPG, channel preferences, Health Center, theme built-in/custom switch, and the installed file picker. These remain inherited features, not rebuilt native subsystems.

Automated Android tests use real framework views/storage/lifecycle/media callbacks with disclosed controlled players. They do not prove real-provider, decoder, OEM PiP, Fold posture or hardware GPU behavior. Report the device/Android version, which exit control you used, and a screenshot/diagnostic export if any device-only behavior remains.
