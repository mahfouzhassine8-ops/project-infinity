# Physical Fold QA — revised user verdict / regression-limited correction scope
Date: 2026-11-06
Source review anchor: delivered signed candidate source `0aa597f1ec152a89d291eef10b8627cd15bd421a`.
This QA record describes the **user's currently installed and tested configuration**; verify its actual addon/APK versions from device evidence before selecting installable patches. A source label is not proof of what the user installed.

## Authoritative 1–9 results (supersedes prior answers)

| # | User verdict | Immutable acceptance or minimal repair |
|---|---|---|
| 1 | **PASS** | Power at absolute drawer bottom. Preserve. |
| 2 | **PASS** | Infinity Movies opens correct main menu (Continue Playing, Watchlist, Collection). Preserve. |
| 3 | **PASS** | Infinity TV Shows opens correct main menu (Next Episodes, Progress Shows). Preserve. |
| 4 | **FAIL** | White curved icon and bottom touch instruction/decorative elements still present. Trace actual rendered owner/control; remove only that visual clutter, without affecting gestures. |
| 5 | **PASS** | Downloads initially shows only real Add videos; user-added folders visible after. Preserve ALL existing working source/rename/edit/return behavior; no new native Downloads edits without a reproduced defect. |
| 6 | **UNTESTED** | Search repeated-queries crash not yet tested in this configuration. No PASS assumption. |
| 7 | **FAIL — P0 regression** | Crew and Nixtoons **used to show valid results after tapping provider heading, even with `state_changed`**. Now **tapping them opens no results**. Restore actual provider heading navigation and valid results; then fix false-positive `state_changed` without weakening meaningful-change protection. |
| 8 | **FAIL** | User likes overall poster/list/season/episode appearance but **Mark as Watched check/action is gone**. Trace original watched toggle/control and indicator, restore actual working state and visual confirmation. Preserve all other browser polish. |
| 9 | **FAIL** | Some Info work visible (Cast now appears), but **Play and Trailer do not respond to presses**; inspect More/Back too. Restore real interactive actions, focus and original routes; do not remove working Cast. |

## Preserve the newly approved working base
Protect #1, #2, #3, #5 in their **physically accepted installed behavior**. Preserve current visible Cast, readable browser layout/posters/metadata, existing playback when invoked elsewhere, native touch, context menus, provider configs, Favorites, Continue Playing, user sources and persisted state. Cobra and Preview completely untouched. No unrelated UI/native/skin/Command Center changes, no revert of all prior corrections, no installation/data wipe/downgrade/signing-key change.

## Evidence-backed diagnostic targets — not presumed root causes

**Search P0:** `repairs/infinity-master-corrective-20261105/overlay/assets/addons/script.infinity.commandcenter/infinity_search.py`
- `_provider_result` rejects if `_query_signature` changes; settings.xml metadata stamps can create known false `state_changed` on benign provider history/rewrites. Two required acceptances were already documented FAIL in `SEARCH-REMAINING-GATES.md`.
- `_publish_result` adds a provider heading with path and `isFolder=bool(path)` even on noncompleted status; original provider route SHOULD be accessible when pressed. Current physical outcome says it isn't. Trace Kodi window activation and native provider navigation from actual installed ZIP/APK; do not attribute solely to warning labels or the cache-only race without proof.
- Compare the user-tested working provider heading/action and current installed generation. Maintain authentic provider URL and all enabled/dependency/source/configuration/cancellation/ABA guards. Preserve the first failing `INFINITY_SEARCH_STATE` category/status/count record for each provider. Do not modify third-party provider implementations.
- No current fatal native stack exists. Search crash #6 remains separately UNTESTED; avoid invented SIGSEGV repair and unsafe repeated forced crashes.

**Watched UI:** Determine whether user means missing actionable **Mark as Watched** control/context-menu entry, missing **checked indicator** after marking, or both. Restore both expected interaction and persisted check/clear indication where supported. Kodi/provider ownership and watch-state storage must remain original, not a fake checkmark.

**Info controls:** `repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz/unified/DialogVideoInfo.xml`
- Native Play control `id=8` is present as `togglebutton` without explicit skin onclick; verify native Kodi dialog binding and actual press reception. **Not a proven cause**.
- Trailer `id=9012` has conditional `Player.HasVideo` stop, optional `script.trailer.bridge`, or `ListItem.Trailer` fallback; verify focus/overlap/touch event, condition evaluation and player dispatch on installed build.
- Cast `id=9013` and native cast list `id=50` are visibly improved—KEEP. Check More and Back against original functional routes. Do not invent trailers/metadata.

**Visual:** Existing icon selector suppresses resource `script.infinity.live/resources/icon.png` in shared variables/21 texture references, and touch-guide include was removed in source; user physically still sees unwanted white curve/guide. Inspect the actual **installed** skin and actual rendering layer to find surviving XML include/resource/overlay; no broad deletion of `script.infinity.live` or working media art.

## Repair and acceptance contract
1. Fix #7 P0 first, then #9 Play/Trailer, #8 Watched, #4 visuals. Only test #6 after stable provider browsing. Protect #1/#2/#3/#5 with focused negative/preservation tests after each patch.
2. Prove behavior on the Fold, both screens/themes where relevant; host XML tests cannot supersede user FAIL.
3. Ship only authenticated compatible installer components for actual modified files, and a signed higher-version APK **only if a proven native change requires one**; original signer, matching manifests, component generations and safe recovery. Do not issue source-only ZIPs as installers.
4. No app uninstall, data clear, settings reset, downgrade, source deletion, Cobra changes or broad native Search rewrite.
5. Explicitly report per-item PASS/FAIL/UNTESTED after user validation; **do not promote/lock** before the user's acceptance.

Current test: **PASS 1,2,3,5; FAIL 4,7,8,9; UNTESTED 6**. Source-only assumptions do not override this outcome.
