# Cobra — Approved Refinement Addendum: Universal Rotation and Fullscreen Audio

**Status:** Feature/behavior scope approved by user in chat, pending implementation and physical acceptance. This is a specification, not a claim of code changes or testing.

**Authoritative baseline:** approved signed combined 2103442 (`lock/infinity-cobra-2103442-user-approved-20261101`, exact source `2e88f85250ef2e46952192cf0fdb42ac5af7c9c8`).

This addendum **extends** `EXECUTION-BRIEF.md` on the work branch. Neither requirement replaces or relaxes its existing end-to-end workstreams or absolute preservation rules.

## Refinement 1 — Single universal two-state Rotation control

Existing Cobra Rotation control must have only two functional states:

1. **Tap while locked/inactive → Rotation ACTIVE.** Cobra may rotate to the device's supported current physical orientation as the device rotates; respect Android/window and Fold constraints.
2. **Next tap while active → LOCK CURRENT DISPLAYED ORIENTATION.** Freeze the portrait or landscape orientation **currently on screen at that exact moment**, without forcing portrait, forcing landscape, unexpectedly spinning, or reverting to another orientation.
3. **Next tap → Rotation ACTIVE** again. Continue alternating states with each press; this is one button, no extra dialogs.

### End-to-end scope and state contract
- Applies to **all actual installed Cobra view modes**, including Cards, Pro, Pro Sports, Multi-View and any other view mode, as well as each mode's **Fullscreen** player; not a one-mode-only overlay behavior.
- State is consistent when switching modes and entering/exiting Fullscreen and should not silently reset to a different rotation policy. Lock must hold the current displayed orientation until the user reactivates rotation, except when a system/window constraint makes this impossible (then handle gracefully; do not damage layout).
- Clearly distinguish active/free rotation from locked orientation on the *existing* rotate control using the approved palette and theme styling. Do not create unnecessary extra toggle controls.
- The **separate existing padlock icon/control must remain functionally and visually unchanged**; do not repurpose its behavior as a substitute for the rotation-button state.
- Avoid rotation-induced player reload, lost stream, lost focus/channel/scroll position, dead touch areas, clipped buttons or unexpected layout snaps.
- Test alternating press sequences while in portrait, landscape, folded-front, unfolded-inner, while switching modes, moving to/from Fullscreen and with system rotation restrictions. Record host/emulator vs actual Fold evidence separately.

## Refinement 2 — Universal Fullscreen Mute/Unmute button

On the **existing Fullscreen bottom control row**, for every Cobra view mode, insert the **same Mute/Unmute control directly between Channels and Display**:

`Channels | Mute/Unmute | Display | Multi-View | PiP`

- Reuse Cobra's appropriate native player audio owner/state; do not invent a second unsynchronized mute mechanism.
- Tap once → mute the Cobra player's playback audio; icon updates to clearly show muted state. Tap again → unmute and restore previous volume. Preserve the live stream/video and playback session without restarting media.
- Mute state stays coherent when navigating between Fullscreen and the originating Cobra mode and whenever multiple controls reflect the same player state. If audio route/volume is changed externally, synchronize actual mute display; no silent state mismatch.
- Scope is player playback audio only: do not change system ringer, notifications, global unrelated apps or unrelated native/media policies.
- Place in the exact requested order in **all** Fullscreen instances, regardless of originating view mode. Fit five buttons on narrow Fold cover while retaining touch reachability, existing button style, labels, dynamic themes, PiP behavior and safe-area navigation spacing. Avoid overlap/clipping or shrinking video by accident.
- Test playing/paused/buffering, repeat toggles, screen rotations and fold transitions, PiP/Fullscreen transitions, mode swaps and correct UI state. Preserve all other control mappings and order, especially Display, Multi-View and PiP.

## Strict preservation and delivery requirements

- This approval is **only for these two scoped behavior changes** within the larger, already-authorized Cobra-only end-to-end refresh.
- Freeze the combined signed 2103442 accepted baseline, Infinity 2103437, shared/native components, Choose Your Experience, shutdown, all other existing Cobra controls and approved Cards/Pro layouts. Do not modify protected components for this feature without separate explicit authorization.
- Identify the **actual Cobra-owned** control handlers and player audio/orientation owners before editing. Where an essential dependency would require changing protected shared/native code, document it as a blocker for that subfix and seek separate authorization.
- Verify behavior across every registered view mode, both Fold displays and allowed orientation/window configurations. Include source and APK preservation hashes.
- Deliver with the overall Cobra-refresh final original-key-signed install-over APK and exact component ZIPs, not as an independent unrequested release. Do not automatically lock/publish as an approved replacement without physical Fold acceptance.

**No build or implementation was performed by creating this specification.**
