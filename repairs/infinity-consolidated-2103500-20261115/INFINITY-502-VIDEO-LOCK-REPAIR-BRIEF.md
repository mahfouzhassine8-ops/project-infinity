# Infinity 502 — Video UI Lock redesign + functional repair (owner-requested)

**Owner direction — November 16, 2026:** Video UI changes and fixes, especially **redesign the Video Lock** and repair its functionality end-to-end. The user referenced a video but the current message surfaces a still image; **do not invent a reproduction or claim the clip was viewed until an actual playable clip is obtained**.

**Base:** Original-signed Infinity **2103502** (`f35b6e6015d91185d76a12b4f21cec17c9eaa65ef07b17d8fed91a547dfffb28`), retain shutdown observer, Silent Mode and Cast discovery corrections; preserve Cobra 2103445, provider/native search/playback, data and existing UI outside this player-lock flow.

## Exact source inspection (signed502 APK; not a simulated screenshot)

- The player VideoOSD lock control is `<control type="button" id="262">` within `assets/addons/skin.infinity.diggz/*/VideoOSD.xml`. On press it calls `Skin.Reset(Infinity.PlayerDrawerOpen)`, `Dialog.Close(videoosd)`, then `ActivateWindow(1199)`.
- The associated screen is `assets/addons/skin.infinity.diggz/*/custom_1199_InfinityVideoLock.xml`, `<window type="dialog" id="1199">`. It has a full-window transparent button `9900` that shows a temporary unlock control, and image/button `9901` for unlocking.
- On entry the dialog sets `InfinityUnlockVisible` and schedules `AlarmClock(InfinityHideUnlock,ClearProperty(InfinityUnlockVisible),00:00:03,silent,false)`. Any backdrop tap re-arms this three-second hide. OnBack on backdrop also only re-arms the hide.
- Button `9901` calls `CancelAlarm`, `ClearProperty`, `Dialog.Close(1199)`, `ActivateWindow(VideoOSD)`; the **unified** variant additionally injects `INFINITY_LOADING_V2` `NotifyAll(... seamless.loading ...)` before/after activation, unlike 16x9 and responsive/portrait variants. Its payload references `Container(9901)` even though 9901 is a button, warranting bounded owner-state review.
- These source differences are **verified package differences**, not yet the physical failure's cause. The active skin root and behavior on owner's actual Fold remain unverified; avoid assuming packaged XML is the loaded copy.
- Possible failure hypotheses to validate against the owner's recording: 3-second unlock auto-hide can frustrate tap, focus/default full-window capture, Back/gesture may dismiss or propagate unexpectedly, unified-only loading signals may generate overlay/stuck spinner or stale owner, layout sizing/position may be awkward when folded/unfolded. **All hypotheses, not established symptoms**.

## Owner-approved outcome (behavioral contract; exact visual style requires clip review)

1. **Video continues playing** during lock. Lock must suppress ordinary unintended screen taps/seek/OSD/gesture commands within Kodi player area, without blocking legitimate OS/emergency/system gestures; respect Android BACK/back-exit policy and navigation safety.
2. **Unlock is reliable and obvious:** intentional user interaction reveals an accessible, legible unlock affordance with a comfortable touch hitbox, and a clearly distinguishable locked state. Do not let auto-hide silently trap the user or produce repeated ambiguous taps. Specify/test clear hold/tap or confirmation logic after reviewing the recording.
3. **Visual redesign:** one polished, minimal, contrast-safe, responsive lock interface. No giant center obstruction, microscopic affordance, undesired fade or visual conflict with playback. Honor Infinity theme, motion-reduction setting, device form factor, landscape/portrait/fold/unfold, Fullscreen/PiP transition.
4. **State and lifecycle:** enter, idle, reveal, unlock, reenter, video end, screen rotate, Fold transition, external back/exit are deterministic. No stale timers/Window properties, overlays or stranded dialogs; unlock does not create fake loading tasks, change playback progress or trigger unwanted UI reset. Fix unified-only loader inconsistency if source/runtime evidence warrants it.
5. **Preservation:** Only actual scoped player-lock XML and minimal necessary first-party support code may change, with exact old/new file list/hash receipts. No Cobra, cast transport, native media engine, stored progress, add-ons, providers, watchlist, shutdown or unrelated skin layouts.
6. **QA:** Compare affected XML variants, validate XML/control navigation, onClick commands and focus behavior, test folded/unfolded/rotation, touch and BACK, locked/unlocked state, active paused/playing/resume/stop, reduced motion, and Kodi/Android UI in emulator plus owner Fold one acceptance cycle after package. After corrected code passes, original-sign successor QA APK from 502 with matching recovery; no premature "fixed" claim.

## Next gate

Request/look at the owner's **actual video recording** to identify the observed visual and malfunctioning interaction, correlate the actual active runtime skin variant and relevant logs. Source-level audit alone cannot establish exactly what failed. Then implement a bounded corrective change under this workstream, run targeted tests, compare full APK/native/skin diff and obtain independent review.

**Status:** **AUDIT + DESIGN + FIX AUTHORIZED.** Exact issue and final approved design **PENDING RECORDING REVIEW**. Production source and APK **UNCHANGED** by this brief.
