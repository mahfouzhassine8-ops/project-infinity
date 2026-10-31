# COBRA 2103437 — STRICT CARDS-ONLY LIGHT/DARK COMPATIBILITY AND PRESERVATION

**Direct user requirement, October 31, 2026:** The user observes that **Cobra Cards view remains dark despite Cobra's previously implemented appearance system**, and specifically instructs: **"Everything else is untouched including other cobra stuff that is not in this scope."**

**Scope: ONE targeted Cobra Cards theme-compatibility correction ONLY.** This document captures implementation boundaries; it does NOT authorize a redesign, unrelated feature changes, or acceptance of an untested APK.

## Signed authoritative baseline

- Repo: `mahfouzhassine8-ops/project-infinity`
- Protected signed 2103437 source **`31d55543e3a01a37975c396c0291ff26d98cc4b8`**.
- Protected lock: `lock/infinity-cobra-2103437-user-approved-20261031`; DO NOT ADVANCE/MODIFY/REBASE.
- Cobra-only working branch: `work/cobra-only-from-2103437-20261031`.
- Signed APK: `Infinity-2103437-Combined-Original-Signer.apk`, SHA256 `6852a7e50003648e56a9f6f0f9e185a1f80f341b4bad9c4c6be7e2f02856b88c`, original-key run `41194267440`.
- Original certificate SHA256 `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
- Frozen Infinity 2103437 ZIP SHA256: `d03b4d5e845dfb5e1d6bb75c1967c7b6a2e55c5b17a7c65d66d43d43abd2e73d`.
- Frozen minimal/shared ZIP SHA256: `432bfb7b246a504d9550e1de39368c3b7e0946532f1c695531ed891e74ef03d8`.
- Current Cobra 2103437 ZIP SHA256: `41d812863992d9200bbd7708cc03c4a4c048354ccb67cc4ff73ec8c5fb6bb0cb`.
- Retain locked 2103436 and older signed recovery artifacts untouched.

## Verified source-level clues, not a fully established runtime cause

In the current signed437 source:
- `repairs/cobra-next-from-2103427/cards-from-2103431/runtime/CobraCardsLayout.java` uses hard-coded dark `0xff000000` for Cards shell/browser; `PanelSurface.onBoundsChange` draws `0xff00090d/0xff000203/0xff001016` dark gradients; text is styled with constant WHITE/MUTED; Cards' icon/progress shapes have fixed dark/light colors regardless of theme.
- `repairs/cobra-next-from-2103427/cards-from-2103431/runtime/CobraCardsTiles.java` uses fixed WHITE/MUTED text and dark tile gradient `0xff010a0e/0xff01070a/0xff001016`, dark progress track and fixed divider/More glyph colors.
- Existing Cobra appearance/theme infrastructure already exposes `cobraEffectiveAppearanceMode()`, `cobraModeDark()`, `cobraModeColor("text")`, `cobraModeColor("muted")`, palette publication and `cobra_appearance_mode`. Historical `addons/script.infinity.cobra.theme/resources/cobra-theme.json` defines dark, light, oled palettes (historical JSON alone is NOT proof of the exact signed437 active runtime palette). Diagnose the **actual source and runtime** theme owner before implementing.
- Signed437 Cards native theme-rebase logic monitors `mVisualTheme` publication; ensure theme changes are reflected while Cards is visible, without stale drawable/text color caches.
- User's `20791.jpg` shows four-column unfolded Cards in dark styling. A still dark screenshot does not by itself prove the saved preference, chosen mode or an on-screen toggle failure; confirm selected light mode in the actual UI/runtime.

## Only authorized functional result

**Cobra Cards only** must use the existing Cobra appearance choice with no new setting or theme system.

- **Dark mode:** identical to the current signed437 Cards screen, ideally pixel/paint parity. No edits to dark geometry, gradients, selected cyan border, fonts or artwork.
- **Light mode:** background, header, preview/Now Playing panel, toolbar, cards, text, logos/fallback, glyphs, dividers, progress tracks, and focus borders draw using **existing native Cobra light palette** with appropriate contrast. Do not change shapes, positions, density, action meaning or channel data. Cyan/blue accent may remain but must contrast against light backgrounds.
- **Existing OLED/true-black and other native appearance variants:** retain their existing semantics and preserve approved dark/OLED baseline; ensure Cards does not override them with an incorrect light/dark mode. Do not invent a new fourth palette.
- **Live switching:** Cards must reflect an existing appearance change on the visible page, including return from Settings, fold/unfold, rotation and cold/warm startup, without requiring uninstall, clearing data, restarting playback or recreating grid/decoder. Maintain existing appearance precedence (manual selection, day/night, Night Cinema, inherited system mode where already implemented). Do not create a second preference or override platform mode.
- **Scope of Cards:** header, shell/browser, selected channel preview controls, Now Playing details/progress, filter/search toolbar, actual channel card components, context-menu More glyph and focus/selection; their already working callbacks/visibility/hit targets are unchanged.

## ABSOLUTE NO-CHANGE LIST

1. **INFINITY 2103437 COMPLETELY FROZEN:** actual Infinity owner ZIP/skin/loading animation, Search/providers, native playback, PiP/Resume/Health/Command Center, addon Python code, data/persistence and protected shutdown. No Infinity re-signing apart from the unchanged owner in a versioned combined package.
2. **ALL NON-CARDS COBRA MODES FROZEN:** Mobile, Compact, TV Grid, Pro, Pro Sports, Sports, Multi-View, player/fullscreen surfaces, TV guide presentation in other modes, global appearance system, Settings/chooser, themes, preference schema. Reuse existing colors **without changing native palette definitions or the shared theme engine** unless the needed change is proven to be exclusively Cards-owned and user separately authorizes it.
3. **WORKING COBRA CARDS FUNCTIONALITY FROZEN:** original two-column front and four-column inner geometry (including accessibility fallbacks), drawer-sizing fix, rows/logos/EPG, channel selection, focus, scroll, long press, More/sun menus, search/filter, playback, progress values, PiP, fullscreen, video surface/decoder, live status, animation timing. Color styling and its valid theme-refresh mechanism only; no resize/reflow or network/worker changes.
4. **ALL DATA/INSTALL INTEGRITY FROZEN:** user favorites/channel sources/playlists/profiles/guide cache/watch data/passwords, settings, signed package `com.projectinfinity.kodi`, original key/cert, launcher icons, 47 native libraries, essential shutdown. Never uninstall/clear data, reset settings or migrate databases.
5. Do not replace native Android player architecture, create new drawables with unrelated geometry, add global listeners/timers/polling, alter callback order, change background threading, speed optimization, recording/EPG mapping or source addresses. Do not change historical signed lock and release artifacts.

## Mandatory fail-closed verification

1. Resolve actual signed437 runtime theme and color owner. Test normal Cobra appearance switching in a known working mode first as **read-only reference**; verify Cards fails to follow the exact same setting and isolate its hard-coded surfaces. Do not change working modes to make Cards match.
2. For dark and OLED, compare current signed437 vs candidate **painted colors, text and geometry** under identical viewport/data/theme settings. For light, check background/foreground contrast and selected/hover/pressed/focused/disabled/progress states at actual touch and remote focus.
3. Test front display 2 columns, inner 4 columns, drawer-open/close, cover→inner transition, rotation, return from fullscreen/PiP, theme toggles live and after reopening Cards, cold/warm theme publication, rapid switching and user profile/setting retention. Confirm card bounds, playback session, selected channel/scroll offset and callbacks unchanged.
4. Verify real user setting `light`, `dark`, `oled` as supported by signed437; if system/night appearance inherits a mode, follow the original mode resolver. Do not use hardcoded alternate flags based only on screenshot or time.
5. Freeze non-Cards Cobra mode appearance/behavior by method-level negative controls, and fully freeze Infinity and shared/native code by source + **actual signed APK-member comparisons**. Any modified global theme method requires an exact source/DEX owner guard and negative controls; if it cannot be proven isolated, STOP and request approval.
6. Compare exact original signed437 with candidate: enumerate each changed, added and removed APK member, and demonstrate only Cards-specific Cobra methods/assets plus mandatory truthful versionCode/chooser metadata differences. Preserve original signer/cert, executable chooser, source/module authentication and package/data installation behavior. Do not use source similarity alone to claim byte-parity.
7. Focused tests only, reuse passing evidence but run new light/dark/OLED checks. No unrelated shutdown stress. Only after gates pass build ONE original-key signed install-over *test candidate*, do not promote/lock until real Fold approval. If runtime or light-mode evidence unavailable, disclose the limitation and do not fabricate PASS.

**STOP CONDITION:** Any regression, unrelated Cobra change, Infinity owner change, unexpected native/shared or data change, dark-mode visual drift, or incorrect light-mode appearance is a failure. Keep the signed437 lock untouched.

**STATUS:** Scope and preservation only; no code corrected or APK signed by this document.
