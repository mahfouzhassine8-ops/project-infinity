# 2103221 onn. 4K Pro TV Remote UI RC4

Protected parent: **2103220 — onn. 4K Pro TV Grid RC3**

This pass is strictly TV/ARMv7. The regular ARM64 phone/Fold Infinity/Cobra line is not modified.

## Physical-device failures reported from 2103220

1. Channel Groups were extremely difficult to enter and select with the onn. remote.
2. Fullscreen video controls were still touch-first and did not establish reliable D-pad focus.
3. The guide preview still exposed phone-style focusable controls and could pull navigation away from the EPG.

## Root cause

2103220 removed the permanent TV Grid side directory to reclaim EPG space, but two wide-screen group paths still tried to focus that now-zero-width directory. That created invisible focus on a TV.

The player also opened a focusable fullscreen container but did not hand focus to a real transport control. The timeline was primarily touch-bound, the channel drawer did not focus the current channel/group, and preview video surfaces still exposed touch-era controls.

## 2103221 contract

- Channel Groups and Playlists always use a dedicated TV overlay.
- The current group/source receives focus immediately.
- Group rows have a large, explicit focused border and 10-foot row height.
- Group selection is one Select press and returns directly to TV Grid.
- Grid lists acquire a real visible focus target after group/source changes.
- Preview video and preview detail controls are passive/non-focusable.
- Preview remains contextual video; selecting the current channel again promotes it fullscreen.
- Quick Peek video is passive and its Watch action receives focus.
- Fullscreen player controls hand focus to Play/Pause.
- D-pad remains inside player controls until Back hides one layer.
- Back unwinds action sheet / channel drawer / player controls predictably.
- Timeline is a D-pad target; Left/Right commits rewind-window movement.
- Player channel drawer focuses the current channel/group and Select tunes in one press.
- Player drawer removes touch wording and fast-scroll behavior.
- Existing Live TV playback, rewind/timeshift, providers, recordings, Quick Peek engine, Smart Return, Movies/Shows, Health Center, signing and package identity remain protected.

Physical onn. 4K Pro acceptance is still required before promotion.
