# INFINITY — GROUP #2 / ADD-ON BROWSER — SOURCE-STAGED FIRST CHECKPOINT

**Date:** October 19, 2026. **ACTIVE GROUP #2**, original detailed tasks **05, 06, 07, 08**. This is **not complete**, not a signed APK, not integrated Android CI, and **not physical Fold acceptance**. Group #1 is explicitly **paused unfinished** (#19 no-reload still not fixed). Group #3–#7, Cobra and shutdown are off-limits.

## Source/visual evidence and root cause

- Examined the user's actual Add-on Browser screenshot `1792383561650.jpeg` and the original **signed** experimental APK **2103390** (`778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb`).
- Original actual Add-on Browser `AddonBrowser.xml` renders exactly one `infinity_browser/header_arc.png` image atop the blue header next to the genuine Infinity icon. That is the unwanted screenshot cyan slash. **No shared icon file is deleted** and the same header decoration on other screens is not changed.
- Original subtitle/help text in all **14** Infinity skin layouts permanently says `Select “Install from zip file” here to enter Kodi’s native file picker.` even on the root or other add-on categories.
- The four original non-clickable footer labels `INSTALL ZIP / REPOSITORIES / UPDATES / DEPENDENCIES` are styled like active navigation tabs but have no click handlers; screenshot confirms they misleadingly appear on all destinations.
- Original Add-on Browser panel 50 sends RIGHT back to itself; the original BACK button already exists at 9096. Original native ZIP FileBrowser lists 450 and 451 route RIGHT to scrollbar 61, which might not receive focus on a one-page directory; the existing right-side native OK action is id413 and existing Preview is 9410.

## First strictly scoped implementation — host source stage

**Saved repair source:** `repairs/2103390-bugfixes/group2/addon_browser_group2_patch.py` (**commit `4b18d89c7fb69ec554887257c07b87ff6aebf400`**, verified remote Git blob `d62986156ca61bfafd5ea13fb037d62e0a3d7d06`).

- Group #2 task **05**: Delete *only* the single AddonBrowser header-arc image control in all 14 original Infinity layouts, preserving the actual infinity logo/title/subtitle, BACK and theme.
- Task **06**: Replace the always-ZIP description with one already-supported `$VAR[InfinityAddonBrowserHint]`. Extend original `Includes_InfinityBrowser223.xml` **only with new named contextual help/footer variables**, keyed by the native `addons://user/`, `outdated/`, `recently_updated/`, `repos/`, `search/`, `install/` and root paths. These use the existing Kodi folder path; unknown nested views receive accurate non-prescriptive fallback. Replace **only** the four misleading nonfunctional footer labels and three separators with a single truthful context line; retain the original footer background and layout. Do not invent shortcuts, native routes or new buttons.
- Task **07**: Browser panel 50 RIGHT focuses the existing BACK button 9096 (its LEFT remains 50), so navigation focus may reach it without activating a list item. Kodi's original built-in selected-item actions, add-on enabled state and data remain untouched. The footer states **Disable is not Hide**; no pseudo-Hide or automatic disable is introduced.
- Task **08**: In original `FileBrowser.xml`, **only** list controls 450 and 451 RIGHT now navigate directly to existing native OK button 413, not optionally nonfocusable scrollbar 61. Existing ZIP selector, repository navigation, Kodi search keyboard, native package filters/permissions, scrollbar, buttons 413/414/415 and compact ZIP Preview 9410 are preserved, as are its conditions.

## Exact proposed member scope and SHA receipts

The **original signed APK is unmodified**; no new APK or skin installation was performed. All proposed changes are confined to **42 existing APK members**:

- **14** `assets/addons/skin.infinity.diggz/{layout}/AddonBrowser.xml`
- **14** `assets/addons/skin.infinity.diggz/{layout}/Includes_InfinityBrowser223.xml`
- **14** `assets/addons/skin.infinity.diggz/{layout}/FileBrowser.xml`

The unchanged **7,388** members include every Cobra resource, Kodi native engine library, Essential-First shutdown, Command Center, providers and their data, the original FileBrowser ZIP Preview native implementation, `DialogAddonInfo.xml` and all other skin windows. No ZIP members are added/removed. The exact patch source prints **full before/after SHA-256 for every changed member** via `staged_inventory`, refusing a different original signed APK or layout inventory.

The default actual Fold `unified` file preimage/output SHA-256:

| Scoped file | Before SHA-256 | After SHA-256 |
|---|---|---|
| `unified/AddonBrowser.xml` | `b5bb154ec78021f01f1b904e221bc63be3d2121b2f0b85de04a4c228edb89f90` | `3248b8d63373ae07aca438f8b74d42b86ecc093ad591a2b62fd24cbb7a61e156` |
| `unified/Includes_InfinityBrowser223.xml` | `51c4ddba2c79254c93b7b7218ad7877d6d0a4f224eb86951c7e2ab480ea8b2d4` | `73621c646ada7945b91be9e6dbec6feb382989ebe980d89a1eb54dd1fcb53a3b` |
| `unified/FileBrowser.xml` | `b51c040103277eadd1b34c1e01474977349dd32d1145e3bd1b7dbacf0bb995e1` | `a8198fddba54f29e27a924c82e0926b540c31148586c5f7019d0e11441d34059` |

SHA-256 of the canonical JSON array of 42 before/after entries (compact sorted-key serialization): `dd9eca615bcb4f7c908510a27845592acbd98e05bfe744ceabc4cf52d771207a`.

## Executed tests and limitations

**Saved test source:** `repairs/2103390-bugfixes/group2/test_addon_browser_group2_patch.py` (commit **`2b97f4ecb8aa835e9d39ae0c26776df946d0c345`**, remote Git blob **`1c6934398826b03f88eee32cf6b7b783d1079a2a`**).

Local Python `python -m unittest -v test_addon_browser_group2_patch` performed **10/10 PASS** on the *real signed* original 2103390 file (about 3.6 seconds): 42 exact allowlist/7,430 count; cyan-arc-only removal; root help/native panel preservation; native contextual routes; footer nonclickable replacement; panel/back focus; two FileBrowser lists and all existing ZIP buttons/preview; all original theme variable values and click handlers unchanged; immutable signed APK and safe separate staging; and fail-closed altered/double-applied source. One transient **test assumption** about the logo file name and XML tail whitespace was corrected in the test before this green run, without changing the approved patch.

**Tests are not proof** of rendering, touch precision, all six root item visibility under different update availability, right-side button focus in the actual Fold, correct back/selection restoration, successful repository install, actual ZIP preview or keyboard Search, or native Enable/Disable confirmation.

## Important native limitation: Do not confuse Disable with Hide

Kodi Omega `xbmc/addons/gui/GUIDialogAddonInfo.cpp` dispatches the existing `CONTROL_BTN_ENABLE` to `OnEnableDisable()`. If enabled and not a required dependency, native code directly calls `DisableAddon(..., USER)`; **it does not guarantee an explicit Yes/No confirmation** for an ordinary add-on. The correct reversible **Hide** behavior and user-requested confirmation/two-step actions are **NOT fixed by this skin-only patch**. Changing the global native handler would risk Cobra and unrelated windows, so no misleading UI relabel or speculative native mutation was made.

## Remaining Group #2 acceptance blockers

- Reproduce/verify actual root and each of the six native destinations on the user Fold, including conditions when Updates/Recently Updated are empty. Do not invent native entries.
- Confirm visible list selection, long-press and contextual action relevance, item-dependent context menu, native enable/disable confirmation and actual **view-only Hide** semantics without editing shared Cobra-sensitive native core. If the only viable approach changes a shared native handler, STOP and request explicit scope decision.
- Verify both picker lists can reach the correct side actions without launching an item, that Kodi native ZIP and Preview, Search keyboard/results, repository and installed add-on subpages still work.
- Verify all light/dark/OLED, Fold cover/inner, Back, D-pad/touch, selected item/scroll restoration.
- Later integrate only user-accepted Group #2 changes under Group #7 build gate. **No build, no final lock.**

**Group #2 is ACTIVE / PARTIALLY SOURCE-STAGED; tasks 05/06 source-staged, 07/08 targeted UI-focus stage with other requirements open. Group #1 remains unfinished and paused.**
