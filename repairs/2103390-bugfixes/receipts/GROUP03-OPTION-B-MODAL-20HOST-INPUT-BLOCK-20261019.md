# GROUP #3 — OPTION B MOVIE + TV TOP-RAIL MODAL — SOURCE-ONLY CHECKPOINT

**Date:** 2026-10-19. **User instruction:** “Move on to three.” Work Group **#3** was activated, preserving Group #1 (task 19 not fixed) and Group #2 (task 07/08 unfinished) as **PAUSED / UNFINISHED**.

**State:** APPROVED OPTION B VISUAL DESIGN RETAINED; MODAL ENGINE + XML **SOURCE STAGED**; 20/20 HOST TESTS GREEN; **DIRECT LONG-PRESS DISPATCH NOT INTEGRATED**, NO signed APK / Android CI / physical Fold / pixel comparison / user acceptance. **Do not mark #3 complete.** No code outside exact Group #3.

## Immutable signed original and saved branch

- Original signed Infinity **2103390** (development base), SHA-256: `778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb`, **7,430 original members**, Android identity and signer unchanged.
- Locked shutdown fallback **2103384** protected; original Cobra/native Kodi `libkodi.so`, native touch mapping, Home XML, providers, `script.infinity.rails`, `script.infinity.commandcenter`, user data remain untouched.
- User-approved EXACT Option B spec: `repairs/design-approvals/INFINITY-HOME-POSTER-LONGPRESS-OPTION-B-LOCKED.md`, only original detailed tasks **09 and 10**. Do **not** substitute Option A.
- Top original signed Home controls: **8101 Movies** and **8102 TV Shows**, 14/14 layouts, Umbrella-owned dynamic source; original normal tap / `CDirectoryProvider::OnClick` preserved.

## New approved modal component — ON DEMAND only

The stage proposes only **two new first-party UI Repair files**; it does not change existing binaries, skin Home XML, keymaps, addon manifests or provider data:

1. `assets/addons/script.infinity.uirepair/home_option_b.py` from `repairs/2103390-bugfixes/group3/home_option_b.py`. SHA-256 `2ac0c6dfd68d1b6922632da6e7142cf1f740382a8cc0110d6769fe0c84892ab3`. Source commit **`6d1623e844f2033bd9adc701eef44bdfa28ea0eb`**, Git blob `e75e07e41d823d5e2aad50630d38d0734d4910f4`.
2. `assets/addons/script.infinity.uirepair/resources/skins/Default/1080i/InfinityHomeOptionB.xml` from `repairs/2103390-bugfixes/group3/InfinityHomeOptionB.xml`. SHA-256 `bfe3c823e98631f9e19f8c2a0d6c98b1a39140b6f8c51120f2d9ccd2c06f5e63`. Source commit **`14605aa250f4502880d527d7cec7d7acf3a8f71d`**, Git blob `043ce3183dfca5369c672e0d1fd346a5b3fc082c`.

The modal uses the approved centered dark/pearl/OLED existing Infinity glass/theme tokens, restrained fade respecting existing `Infinity.OptionalMotionAllowed`, existing Home backdrop dim, selected poster LEFT, real title/year/certification/runtime/rating/genre/plot RIGHT, 72px X close, and exactly **Play → Trailer → Favorite → More Info** bottom row. True item media tags only: never fabricate TMDb IDs, season/episode metadata, plots or trailer links. Identical TV/Movie layout and responsive compact two-row action arrangement on narrow screens. Back/X/outside dismissal does not navigate or start video; no auto-launch on focus.

The `capture()` routine accepts **only actual Home focus 8101/8102 with matching Movies/TV section, a known selected native item index, and original provider URL/title**. No adjacent/guessed poster may be chosen. Immediately before any explicitly clicked action, re-check original full identity/source/index/media type/trailer. Play delegates to original Kodi **Action(Select)** for the selected provider path; More Info delegates to original **Action(Info)**; Favorite uses original Kodi Favourites JSON-RPC only after click and avoids duplicate entries; Trailer uses only an existing supported `ListItem.Trailer` URL (never scrapes or invents links). All actions still require physical Kodi/provider behavior verification.

**Critical limitation:** This is NOT an installed, wired or tested touch interaction. The module deliberately has **NO default.py, context-menu or keymap registration**. It cannot yet open on the required first long-press. Those two proposed APK members would be **new members (7,430 unchanged + 2 additions = 7,432 theoretical)**, not a currently installed candidate. The original signed APK has not been repacked or resigned.

## Exact input blocker — no speculative shared native modification

- In the actual **2103390 signed package**, `assets/system/keymaps/touchscreen.xml` maps global `<longpress>RightClick</longpress>` and `mouse.xml` maps native longclick to `contextmenu`; there is no HOME-specific touch override. Both original top Home panel IDs **8101,8102** are horizontal plugin directory controls; 14/14 source variants have no per-panel native longpress action or intercepted normal tap.
- Original Kodi Omega `CGUIBaseContainer::OnMouseEvent/OnContextMenu` sends a native right-click/context menu to its directory provider, which may first select a touch-hit item. A generic skin `<onclick>` would change normal single tap, not supply an isolated hold trigger; adding it is explicitly forbidden.
- **Existing custom Infinity native hold IS real but scoped to ADD-ON RAILS:** source `repairs/rails-hold-2103378/patch_native.py` states `GetID()!=9200 && GetID()!=8820 && GetID()!=8720 && GetID()!=19601`, and native gesture loop tries only `{9200,8820,8720,19601}`. Native binary has `CGUIBaseContainer::OnInfinityRailLongPress`, but that guard EXCLUDES **8101/8102**. Redirecting Home touch globally or disguising these media panels as add-on rails would change other approved behavior. **NOT AUTHORIZED**. No native source, keymap, Cobra, skin Home, or provider was modified.
- Direct One-Press Option B needs an independently proven original hit-tested poster/context dispatch that suppresses the short-tap follow-on **only** for Home top Movie/TV panels. Until such a nonshared/explicitly approved native-scoped route is available, the exact approved interaction cannot be called implemented. If a shared native edit is necessary, the binding contract requires STOP and separate approval rather than an unsafe bypass.
- Read-only audit `group3/input_longpress_audit.py`, commit **`d15f473014f0acc0d257c11943142481fa1a4d27`**, Git blob `e73003c24e54a26d1ea35b9e81fa86c257d51b26`.

## Executed host evidence

`cd repairs/2103390-bugfixes/group3 && INFINITY_2103390_APK=<exact signed parent> python -m unittest -v test_group3_option_b test_input_longpress_audit`

**20/20 local host tests PASS**, using the actual signed 2103390 asset for package/hash/14 Home layout checks and mocks for Kodi GUI, Favourites JSON-RPC, player and keyboard dispatch. Tests cover:
- Signed full 7,430 member inventory, two additive proposed first-party files, 0 original altered; fail-closed tampered signed parent; immutable original during staging.
- Exact approved four action labels/order and glass modal structure, five responsive viewport geometries, no overlapping action buttons.
- Movie/TV item validation, typed-episode-only S/E, missing metadata, wrong Home window/focus/index, stale route/trailer refusal, no autoplay or background state writes.
- Explicit Play → original Kodi Select; More Info → original Info; Favorites → original Kodi JSON-RPC and duplicate guard; supplied Trailer only; cancel → no side effects; one action dispatch after a mocked modal click.
- Original global touch mappings and native hold scope limitation, 14x2 original media widget variants, 0 live direct longpress hook.

`group3/test_group3_option_b.py` commit **`a93d9dc95ba87432cfca917de85f77280f8d86a6`**, Git blob `0b116ff3f9697ec66a4b0f1177089beab1eb3a78`. `group3/test_input_longpress_audit.py` commit **`06e59e7d066d22d8fb2e600bd6b94c13d4c17636`**, blob `55ce194285ec67f0ca54fa1ee88c7d7f642ccb56`. `group3/stage_option_b.py` commit **`bf0d08cd523ae74f88a6141aab0e2c096cadb371`**, blob `4416043f721d1a02ee173445bc27fe8d97a884e0`.

Every committed file's **Git blob SHA** was explicitly checked against the executed local file, not merely a filename.

## Remaining Group #3 acceptance gates

1. Find or explicitly approve a narrow, exact selected-poster first-hold route with native hit coordinate/identity, suppress double-dispatch, other Home gestures untouched. Without this the new modal is NOT connected.
2. Verify actual Kodi `WindowXMLDialog` skin variables, graphics, modal geometry, font/texture loading, input focus, Back and touch targets on real Galaxy Fold cover/inner/rotation and all user themes.
3. Compare against the actual approved Option B mock and original screenshot `19035.jpg` **on the physical Fold** (the image bytes were not available to this inspection session). Source structure alone is NOT pixel-fidelity proof.
4. Verify actual movie + TV records/metadata, provider Play route/Trailer/Favorite/More Info, resume and current stream continuity, no false/adjacent item, scroll offset restored, and no unintended context menu.
5. Repeat strict no-change Cobra/shared Kodi-native/shutdown/Group1/Group2 baseline audit and user approval before including Group #3 in separately authorized final Group #7 signed integration.

**Result: Group #3 ACTIVE / PARTIAL SOURCE STAGE, 20/20 HOST PASS, NO PACKAGED APK, NO FOLD PASS, NO LOCK. Group #1 and #2 remain UNFINISHED.**
