# Cobra 2103164 physical-device acceptance (not yet executed)

This is an isolated test candidate, not a new protected baseline. Install as an update only; retain app data. Do not uninstall to downgrade. Candidate 14 remains protected. The exact pre-audit 2103163 APK/source is preserved; a same-signer forward-version rollback is preferable if Android rejects a lower versionCode.

| Scenario | Required outcome | Result |
|---|---|---|
| Playing fullscreen -> Home -> PiP | One continuing video/audio session; no mini-background media session | NOT RUN |
| PiP X/close, and swipe dismissal where supported | Sound stops; no invisible playback or media-session restart | NOT RUN |
| PiP expand/return to app, repeated 20 times | Same stream/surface handoff; no duplicated sound or surprise pause | NOT RUN |
| Buffering fullscreen -> Home | PiP remains eligible while play is requested | NOT RUN |
| Paused fullscreen -> Home | No automatic PiP or background-audio takeover | NOT RUN |
| Mini playing, background toggle ON -> Home | Same audio stream continues with native Android controls | NOT RUN |
| Mini paused/stopped, or toggle OFF -> Home | No hidden audio starts | NOT RUN |
| Mini foreground -> Home -> immediate return, repeated 20 times | No stale notification; same player resumes display | NOT RUN |
| Android media Play/Pause/Stop, Bluetooth/headset controls | Controls affect only the current mini session; stopped session cannot restart | NOT RUN |
| Notification tap | Returns to the existing Cobra screen and session, not the experience chooser | NOT RUN |
| Notification permission denied/channel disabled/service refused | Playback pauses safely instead of continuing invisibly | NOT RUN |
| Incoming call, another media app, transient/permanent audio-focus loss | No competing audio; restoration follows Android focus and user pause intent | NOT RUN |
| Lock/unlock while fullscreen, PiP, mini-background | No ghost sound; verify expected pause/return. PiP onStop conservatively pauses. | NOT RUN |
| Task removed, Activity destroyed, process recreated | No detached session or fake playing indicator | NOT RUN |
| Preview More and long-press -> nested option pages | Menu stays horizontally aligned with pane/button; no centered first-frame flash | NOT RUN |
| Cover/inner Fold displays, landscape, split-screen, bars/keyboard | Popup remains within available window and scrolls; no clipped controls | NOT RUN |
| Large font/display scale, D-pad/touch/back/outside-dismiss | Header/actions remain reachable and focus returns correctly | NOT RUN |
| All five views, EPG, Health Center, per-channel preferences/recovery | No regression, false recovery after stop, or lost selected channel | NOT RUN |
| File picker including MiXplorer; theme/appearance switch | Existing functionality and protected visual assets retained | NOT RUN |
| Local/VOD playback, reconnect/fallback, episode completion | No delayed retry/episode start overrides an explicit stop/pause | NOT RUN |

Record phone model, Android version, installed versionCode, toggle states, exact action sequence, and Health Center diagnostics. A passing JVM/CI suite is not physical PiP, decoder, provider, casting, recording, add-on, or battery certification.
