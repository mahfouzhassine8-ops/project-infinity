# INFINITY — APPROVED EXACT ADD-ON GRID & CONTEXT MENU BEHAVIOR

**APPROVAL:** USER APPROVED — **"Perfect I want this bite to bite no exceptions"**.

**Scope:** `All Add-ons → Video Sources` tile grid, including both left and right columns, touch selection, and the resulting add-on options popup. Preserve the earlier visual/menu proposal faithfully. Do **not** substitute arbitrary/additional commands, change the tap sequence, or silently reinterpret **Hide** as **Disable**.

**Implementation status:** Design and acceptance contract approved. **NOT YET IMPLEMENTED OR PHYSICALLY TESTED.** This is not permission to claim that a new skin ZIP or APK is ready.

**Locked Android baseline:** `2103384`, signed file `Infinity-2103384-Optional-VFS-Shutdown-TEST1.apk`, SHA-256 `b571676731bb9bdccb25134c557be613e15cc9adaf77d6675dabc8e0586e54af`. Existing successful Essential-First shutdown remains untouched. The full five-workstream project remains in scope; this is one **additional precisely approved interface correction**, not a replacement for other work.

## 1. The three EXACT interactions, never a direct-launch-on-first-tap

| Gesture | Exact required behavior | Forbidden regression |
| --- | --- | --- |
| **Tap once on an unselected add-on tile** | Select/highlight/focus that tile. Remain in the same grid. | No launch, navigation, or executing the add-on action. |
| **Tap the SAME selected tile again** | Open/launch that add-on normally. | No launch from the first tap; no second-tap context menu unless held. |
| **Tap once, THEN press and hold the selected tile** | Open its relevant, compact Add-on Options menu for precisely that selected tile. | No immediate open, no tall/narrow black ghost panel, no selection jump, no action executed just because menu appeared. |

Tapping a *different* tile changes the selection to that tile and does not launch the former or new tile. The first-tap semantics must be identical in **left and right columns**, at the boundaries and after scrolling. **No more requirement to first launch an add-on and press Back before the right-hand tiles become accessible.**

Menu close/back returns to the exact highlighted tile, same scroll position, no launch, and no focus trap. A popup action requires deliberate invocation; simply focusing an action must not activate it.

Keep Android touch behavior independent of physical D-pad navigation; preserve D-pad selection/open on TV if present. Preserve fold/unfold changes and native GUI ownership; never add double-trigger dispatch, synthetic right click, duplicate context windows, or native shutdown changes.

## 2. EXACT approved top-level menu structure and order

**Header:** `Add-on Options — [selected add-on]` using the existing Infinity skin visual hierarchy.

1. **Open** — launches the selected add-on.
2. **Add-on Information** — opens the add-on information/details dialog.
3. **Add-on Settings** — opens the add-on's settings **only when supported**.
4. **Add to Favourites** — creates a Kodi Favourite shortcut for this add-on without disabling it.
5. **Add to Infinity Rails** — adds/pins it to the custom Infinity add-on rails only when that action is supported and the Rails helper is active.
6. **Hide from This View** — hides *only the current tile in this grid/view*; **does not disable the add-on, uninstall it, delete settings or data, or alter other rail/favourite/provider uses**. The hidden state must have a reversible user path so it cannot strand the add-on.
7. **More / Manage Add-on** — opens a separate advanced management surface; do not present potentially destructive system management actions as ordinary, harmless tile-hiding commands.

Do not add unrelated permanent top-level actions, change ordering, or rename approved labels as a convenience. Compact menu in Infinity's current design, appropriately anchored to the selected tile and accessible without obstructing/unselecting the right column. No legacy black rectangle, overlap, or action cut-off. Conserve useful existing typography and theme behavior across Light/Dark/OLED and Fold configurations; visual proposal is a **text UI mockup**, not exact pixel coordinates.

## 3. Disable is NOT hide — highest-priority safety rule

Kodi **Disable** actually disables the add-on and may break its dependent functionality. It is **NOT** a UI-visibility toggle.

- Do not display `Disable` as a top-level alternative to `Hide from This View`.
- If available, place `Disable Add-on` **inside More / Manage Add-on**, with a dedicated, explicit confirmation naming the add-on and warning it may affect other Infinity features.
- **Never** disable on selecting/focusing the row; only an explicit invocation and confirmation can perform the action.
- Cancel must leave the add-on enabled and all user settings/data intact. Existing Kodi permissions, enabled-state APIs and dependency checking remain authoritative.
- `Hide from This View` must leave the add-on installed and enabled, and preserve every other entry point.

## 4. Show only actions that actually work for that add-on

- **Add-on Information:** available where Kodi can present accurate add-on info.
- **Add-on Settings:** only where the selected add-on exposes settings.
- **Add to Favourites:** present only for a legitimate favourite destination.
- **Add to Infinity Rails:** only when it can add the selected add-on without a no-op/duplicate-broken shortcut.
- **AutoWidget Group** and **Super Favourites**: put behind `More / Manage Add-on` **when their integrations are installed and the action is genuinely supported**; otherwise do not show.
- **View in Infinity Resume Hub:** only when that add-on/item can open meaningful, supported Resume Hub content. Do not include a meaningless generic action on every video source.
- **Hide from This View:** may appear for eligible view tiles; protect essential system and recovery/navigation tiles from being made permanently unreachable.

Avoid displaying actions which do nothing, unrelated future features, fake data-state changes, or duplicate/ambiguous commands. This is **contextual**, not a fixed eight-item dumping ground.

## 5. Reproduce and verify the exact reported physical behavior

The supplied Fold video showed:
- In `All Add-ons → Video Sources`, directly tapping tiles toward the **right side** could launch the item rather than permit selecting its controls.
- The user could only reach right-side buttons after launching an item and returning Back.
- The old eight-item popup featured **Information, Disable, Settings, Add to favourites, Add to AutoWidget Group, Add to Super Favourites, View in Infinity Resume Hub, Add to Infinity Rails**, indiscriminately.
- The user mistakenly tried `Disable` expecting merely `Hide`; the redesign must make this impossible to confuse.

**Required acceptance cases (not yet performed):**

- Right-column first tap stays in grid and highlights; second tap opens; subsequent first select + hold opens the **correct** tile menu. Repeat on left column and after scrolling.
- Close popup via Back/touch outside and verify focus remains on originally selected tile; move focus between columns and reopen correct popup without launch.
- Every visible menu item opens the correct operation only on deliberate activation; no action on highlight; no black rectangle, double invocation, or overlapping menu.
- Hide → tile disappears only from this grid, add-on remains enabled, settings/data and rails remain usable, and the tile can be restored.
- Disable is inaccessible through Hide and requires explicit management confirmation; cancel preserves state. Check tested harmless fixture, not accidentally disabling a live first-party add-on.
- Conditional actions are present only for valid integrations and capabilities; invalid ones do not appear.
- Fold portrait/landscape, unfolded, Dark/Light/OLED, touch scrolling and gesture after popup; protect normal TV navigation.
- Preserve other existing features: Home Continue Playing rail and its currently missing long-press remain a **separate regression item**; player Rotate-vs-Repeat remains a **separate regression item**.
- No native or APK build merely for this skin/interaction correction unless traced source evidence proves one is required.
- If a new signed APK is needed, use **2103384 as locked parent**, test exact signed candidate on Android fresh and loaded/upgrade, then physical Fold normal Close/reopen and essential writes, and obtain explicit user approval. The lock is never overwritten by a failing candidate.

## 6. Delivery and approval gates

1. Trace actual installed `skin.infinity.diggz` and add-on browser/touch path. Do **not** substitute a generic Kodi stock skin and assume parity.
2. Implement the exact structure and gestures in a **new experimental skin/helper candidate**, not in the locked baseline.
3. Provide working functional screenshots/video and source tests for focus, menu relevance, Hide/Disable separation, and correct contextual actions.
4. Require the user's physical Fold acceptance before promoting anything as a new lock.
5. Keep the other previously confirmed regressions (**Rotate OSD shows Repeat; Home Continue Playing long-press is missing**) in the approved project backlog. Don't silently change their implementation as part of this menu correction.

**No approximation, hidden redesign, missing option, blanket Disable/Hide substitution, or unsolicited feature additions.** If an action or exact interaction proves infeasible in the existing Kodi input architecture, report that blocker and request approval rather than delivering an approximation and calling it exact.
