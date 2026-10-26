# INFINITY POWER — ONE-TAP ASK EVERY TIME / CHOOSE YOUR EXPERIENCE RESTORE

**Explicit user UI clarification, October 26, 2026.** This is a small, specifically authorized corrective addition to the existing Infinity Power UI, intended for the next APK. It is NOT a license to redesign the chooser, alter Cobra, modify shutdown or add an extraneous Save flow.

## Actual user problem

The existing **Choose Your Experience** launcher offers **Remember & launch Infinity**, **Remember & launch Cobra**, **Launch [experience] just this time**, and **Ask every time**. Once the user sets "Remember & launch Infinity," subsequent app-icon launches correctly skip the chooser; **Infinity Power currently offers no convenient return to Ask every time**. Cobra already has an **Ask every time** option that applies immediately; after exiting Cobra and starting the app again the chooser appears. The user requires the SAME one-tap behavior for Infinity.

## Required exact new UI

In the **existing Infinity Power dialog**, add ONE regular focusable action alongside Shutdown Timer, Force Close Kodi, Close Kodi, Skin Settings and Reload Skin:

> **ASK EVERY TIME**  
> Show Choose Your Experience on next launch

- Follow the existing white/translucent Infinity Power row typography/icon spacing, touch/remote focus, Light/Dark/OLED styling and dialog dimensions. Use the remaining dialog space or adapt height without overlap. The supplied screenshot-based UI mock shows the new row **directly below Reload Skin**; the existing five actions remain intact and same-order.
- The row is a **direct action**, **not** an entry to another "Choose Your Experience Options" dialog. **NO submenu, NO Save button, NO Cancel/Confirm page, NO two-step sequence.** The user explicitly rejected the illustrated submenu/Save variant. The mock is one Power dialog with one ASK EVERY TIME row.
- On SINGLE tap (or D-pad select), immediately commit the launcher’s **existing authoritative persisted Ask Every Time choice** using its already-established preference storage/API, with correct flush/durability as required by that preference contract. Must work even when the remembered preference is currently Infinity. Do not create a second flag, reset default, edit Cobra settings, or invent a new independent preference source.
- Give minimal nonblocking feedback (e.g. checked row, brief toast `Ask every time enabled`). Do not force an app close or immediately show the chooser; the current Infinity playback/session remains unaffected.
- After the user subsequently selects the existing **Close Kodi** action and launches the app again, show the **existing** Choose Your Experience screen. Its Infinity/Cobra behavior, remember options, one-time launch, theme and persistent settings remain unchanged.
- Existing **Remember & launch Infinity** stays valid when deliberately chosen later. For users who never tap this new Power row, launch behavior must be entirely unchanged.
- All original Infinity Power actions (including normal Close and Force Close) must remain exactly intact. **Shutdown is user-confirmed working and FROZEN. No new shutdown testing, no shutdown changes or new shutdown-test CI signing gate.** Do a minimal preference-only UI check and source/member preservation review if needed. **Cobra is completely untouchable**—reuse launcher’s existing Ask Every Time setting, do not edit Cobra UI, binary, preferences, or code.
- Preserve installed package, user data, Kodi settings and last-played context. No uninstall, clearing data, extra settings screen, or account/profile reset.

## Why an earlier visual draft must NOT be copied

Two automatically generated flow infographics introduced **CHOOSE YOUR EXPERIENCE OPTIONS** and **Save** screens. Those images are **WRONG** for this user's request. Ignore those draft screens entirely. The corrected screenshot-based mock shows only one added **ASK EVERY TIME** row in the original Infinity Power dialog and a check indicating immediate activation. Use this direct UI contract and the user-provided original screen to implement precisely.

## What Pro / Work must deliver

1. Verify existing launcher shared-preference ownership and the same one-tap Ask Every Time entrypoint already used by Cobra; reference that authoritative existing behavior without changing Cobra.
2. Implement the single new Infinity Power row and its immediate preference change.
3. Include it in the exact signed Infinity corrective APK and matching skin/module components as applicable. Add source/member ledger for the Power UI change and explicitly show that native/Java shutdown owner/Power Close handling, Cobra and user data remain unchanged.
4. Simple useful UI demonstration: set Remember & launch Infinity; launch goes direct; open Infinity Power, tap ASK EVERY TIME once; feedback says active; normal user Close; next app-icon launch shows existing chooser. **No new shutdown tests are authorized**; acceptance of the row itself does not require a new Close protocol test, synthetic fixtures, 3-cycles, or red shutdown workflow gate.
5. Finish previously mandated P0 incomplete menu/Health Center/performance/loading/Continue Playing corrections and sign/deliver; do NOT allow this tiny preference UI addition to sidetrack or block the rest of the approved APK work.

**Implementation test:** `Infinity Power > ASK EVERY TIME` single tap = existing persisted chooser policy becomes AskEveryTime immediately; reopening app after an ordinary user exit shows chooser. No Save, no second screen, no Cobra/shutdown edits.
