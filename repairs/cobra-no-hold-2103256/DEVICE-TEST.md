# Cobra 2103256 — remove video hold popup

TEST CANDIDATE. Update-install the APK over Infinity 2103255. Do not uninstall,
clear data, reinstall the skin, reset accounts, or use Start Fresh.

The only functional change is the full-screen Cobra video's long-press callback:
a hold is consumed without opening the Live TV/Channels drawer. The same player
surface is used for Live TV, movie/episode playback and promoted single-screen
playback. Normal taps and explicit Channels/MENU actions remain.

Check one live stream and one movie/episode: with controls hidden, hold empty video
space for 2–3 seconds and release. No drawer should open. Repeat with controls
visible and after an orientation change. A normal tap must still show/hide controls;
Channels must still open the drawer; timeline drag must still seek. Channel-row
Quick Peek and dedicated Last Channel / Multi-View tile actions are unchanged.

Keep Health Center 2.5.18, Skin Audit Update 1.0.1, Command Center 0.3.5.16,
Authorization & Accounts 0.5.2 and whichever skin is already installed.
No new native FD_SET fix, cleanup, Trakt change or stable promotion is claimed.
The source and callback tests cannot substitute for this short phone check.
